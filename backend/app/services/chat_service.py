"""
Chat service -- single RAG-based Q&A interface for one investigation.

Deliberately NOT split into separate "finance chatbot" / "risk chatbot"
/ "business chatbot" user-facing bots. Instead, one chat endpoint
classifies the topic of each incoming question internally
(classify_topics) and pulls in whichever already-computed structured
analysis (financial rows, risk rows, executive summary) matches that
topic as extra grounding context alongside the RAG-retrieved document
chunks. Same underlying idea as a team of specialized analysts feeding
one advisor -- just without exposing four separate chat windows to the
user.

Pipeline per question:
  1. Classify topic(s) -- cheap keyword heuristic, no extra Groq call
     (keeps latency down and behavior deterministic/debuggable).
  2. Pull matching structured context from Postgres. This chat NEVER
     recomputes scores itself -- it only reads what the REASON stage
     (reasoning_service.py / persistence_service.py) already produced,
     so answers stay consistent with the dashboard.
  3. Embed the question (dense + sparse) with the SAME models used to
     embed stored chunks (embedding_service handles this).
  4. Hybrid search (dense+sparse merged via RRF) -> rerank down to the
     best few chunks (qdrant_service + reranking_service).
  5. Bail out honestly if there's neither structured context nor
     retrieved chunks -- never force an answer from nothing.
  6. Build the prompt and call Groq.
"""
import asyncio
import logging
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.investigation import Investigation
from app.models.company import Company
from app.models.financial import Financial
from app.models.risk import Risk
from app.models.report import Report
from app.models.chat_message import ChatMessage
from app.schemas.chat import ChatResponse, ChatSource, ChatMessageOut
from app.services.embedding_service import (
    generate_query_embedding_async,
    generate_sparse_query_embedding_async,
)
from app.services.qdrant_service import search_hybrid_async, has_sufficient_context_async
from app.services.reranking_service import rerank_chunks_async
from app.services.groq_service import call_groq
from app.prompts.chat import build_chat_prompt

logger = logging.getLogger(__name__)

EXCERPT_MAX_CHARS = 280

# How many prior turns (user+assistant messages combined) get fed back
# into the prompt as conversation context. Kept small on purpose --
# this is for resolving follow-up phrasing ("what about last year?"),
# not for accumulating a long transcript into every prompt.
MAX_HISTORY_MESSAGES = 10

# Keyword routing table -- deliberately simple and inspectable rather
# than an LLM-based classifier, since misrouting here only means
# "included a bit of extra/missing structured context", never a wrong
# final answer (the RAG chunks and Groq call still run regardless).
TOPIC_KEYWORDS: dict[str, list[str]] = {
    "financial": [
        "revenue", "profit", "loss", "margin", "expense", "cash flow", "cashflow",
        "debt", "asset", "liabilit", "ratio", "ebitda", "growth", "income",
        "financial health", "roa", "roe",
    ],
    "risk": [
        "risk", "red flag", "concern", "warning", "lawsuit", "compliance",
        "threat", "severity", "contradiction", "audit",
    ],
    "comparison": ["compare", " vs ", "versus", "difference between"],
}


def classify_topics(question: str) -> set[str]:
    """Cheap keyword-based routing -- decides which structured-context
    blocks are worth pulling in alongside the RAG chunks. Not mutually
    exclusive: a question can hit multiple topics at once (e.g. "is the
    high debt a risk?" hits both financial and risk)."""
    q = f" {question.lower()} "
    topics = {
        topic for topic, keywords in TOPIC_KEYWORDS.items()
        if any(kw in q for kw in keywords)
    }
    return topics or {"general"}


async def _build_structured_context(
    db: AsyncSession, investigation_id: str, topics: set[str]
) -> str:
    """Pulls in whichever already-computed analysis matches the
    question's topic(s). Always includes the investigation's headline
    scores if present -- cheap, and keeps chat answers consistent with
    what the dashboard already shows for this investigation."""
    investigation = await db.get(Investigation, investigation_id)
    if investigation is None:
        return ""

    blocks: list[str] = []

    if investigation.health_score is not None or investigation.risk_score is not None:
        blocks.append(
            "Headline scores: "
            f"financial health {investigation.health_score}/100, "
            f"overall risk {investigation.risk_score}/100 "
            f"(financial risk {investigation.financial_risk_score}, "
            f"operational risk {investigation.operational_risk_score}, "
            f"business risk {investigation.business_risk_score})."
        )

    company = (await db.execute(
        select(Company).where(Company.investigation_id == investigation_id)
    )).scalar_one_or_none()
    report = (await db.execute(
        select(Report).where(Report.investigation_id == investigation_id)
    )).scalar_one_or_none()

    if "general" in topics:
        if company is not None:
            blocks.append(
                f"Company profile: {company.name} -- {company.industry or 'industry unknown'}, "
                f"headquartered in {company.headquarters or 'unknown location'}. "
                f"{company.summary or ''}"
            )
        if report is not None:
            if report.executive_summary:
                blocks.append(f"Executive summary: {report.executive_summary}")
            if report.future_outlook:
                blocks.append(f"Future outlook: {report.future_outlook}")
            if report.opportunities:
                blocks.append(f"Opportunities: {report.opportunities}")

    if "financial" in topics:
        financials = (await db.execute(
            select(Financial)
            .where(Financial.investigation_id == investigation_id)
            .order_by(Financial.year)
        )).scalars().all()
        if financials:
            rows = "; ".join(
                f"{f.year}: revenue={f.revenue}, profit={f.profit}, expenses={f.expenses}, "
                f"assets={f.assets}, liabilities={f.liabilities}, debt={f.debt}, "
                f"cash_flow={f.cash_flow} {f.currency}"
                for f in financials
            )
            blocks.append(f"Yearly financials on record: {rows}")
        if report is not None and report.financial_summary:
            blocks.append(f"Financial summary: {report.financial_summary}")

    if "risk" in topics:
        risks = (await db.execute(
            select(Risk).where(Risk.investigation_id == investigation_id)
        )).scalars().all()
        if risks:
            rows = "; ".join(
                f"[{r.category}/{r.severity}] {r.title}: {r.reason} -> recommendation: {r.recommendation}"
                for r in risks
            )
            blocks.append(f"Red flags on record: {rows}")
        if report is not None and report.risk_summary:
            blocks.append(f"Risk summary: {report.risk_summary}")

    return "\n\n".join(b for b in blocks if b and b.strip())


async def _get_recent_history(db: AsyncSession, investigation_id: str) -> list[dict]:
    """Last MAX_HISTORY_MESSAGES turns, oldest first, as plain
    {"role", "content"} dicts ready to hand to build_chat_prompt."""
    rows = (await db.execute(
        select(ChatMessage)
        .where(ChatMessage.investigation_id == investigation_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(MAX_HISTORY_MESSAGES)
    )).scalars().all()
    rows.reverse()  # back to chronological order
    return [{"role": m.role, "content": m.content} for m in rows]


async def _persist_message(
    db: AsyncSession,
    investigation_id: str,
    role: str,
    content: str,
    sources: list[dict] | None = None,
) -> None:
    db.add(
        ChatMessage(
            id=str(uuid.uuid4()),
            investigation_id=investigation_id,
            role=role,
            content=content,
            sources=sources,
        )
    )
    await db.commit()


async def get_chat_history(db: AsyncSession, investigation_id: str) -> list[ChatMessageOut]:
    """Full persisted conversation for an investigation, oldest first --
    lets the frontend reopen a chat and see everything that was said,
    the same way Claude/ChatGPT restore a conversation."""
    rows = (await db.execute(
        select(ChatMessage)
        .where(ChatMessage.investigation_id == investigation_id)
        .order_by(ChatMessage.created_at.asc())
    )).scalars().all()

    return [
        ChatMessageOut(
            id=m.id,
            role=m.role,
            content=m.content,
            sources=[ChatSource(**s) for s in (m.sources or [])],
            created_at=m.created_at,
        )
        for m in rows
    ]


def _to_chat_sources(reranked_chunks: list[dict]) -> list[ChatSource]:
    sources = []
    for c in reranked_chunks:
        text = c.get("text", "") or ""
        excerpt = text if len(text) <= EXCERPT_MAX_CHARS else text[:EXCERPT_MAX_CHARS].rstrip() + "..."
        sources.append(
            ChatSource(
                source_name=c.get("source_name", "unknown"),
                source_type=c.get("source_type", "unknown"),
                confidence_tier=int(c.get("confidence_tier", 4)),
                origin_url=c.get("origin_url"),
                excerpt=excerpt,
            )
        )
    return sources


def _build_retrieval_query(question: str, recent_history: list[dict]) -> str:
    """
    Retrieval was embedding the bare current question with zero awareness
    of conversation context -- a follow-up like "what about last year?"
    or "why?" would retrieve on almost nothing, even though the previous
    turn (already fetched for the generation prompt) makes clear what
    it's actually asking about. Prepending the last user turn gives
    retrieval the same context resolution the generation prompt already
    had, without a separate LLM rewrite call -- real query rewriting
    would need one, and this flow already makes enough Groq calls.
    """
    last_user_turns = [t["content"] for t in recent_history if t.get("role") == "user"]
    if not last_user_turns:
        return question
    return f"{last_user_turns[-1]} {question}"


async def answer_question(db: AsyncSession, investigation_id: str, question: str) -> ChatResponse:
    topics = classify_topics(question)
    structured_context = await _build_structured_context(db, investigation_id, topics)
    recent_history = await _get_recent_history(db, investigation_id)
    retrieval_query = _build_retrieval_query(question, recent_history)

    # Persist the user's turn immediately -- so it's saved even if
    # generation fails below, and reopening this chat later never loses
    # a question the user actually asked.
    await _persist_message(db, investigation_id, "user", question)

    dense_emb, sparse_emb = await asyncio.gather(
        generate_query_embedding_async(retrieval_query),
        generate_sparse_query_embedding_async(retrieval_query),
    )

    sufficient = await has_sufficient_context_async(dense_emb, sparse_emb, investigation_id)

    if not sufficient and not structured_context.strip():
        answer = (
            "This investigation doesn't have enough gathered evidence yet to answer "
            "that question. Try re-running analysis once more sources have been "
            "gathered, or ask something closer to what's already in the report."
        )
        await _persist_message(db, investigation_id, "assistant", answer)
        return ChatResponse(answer=answer, sources=[])

    hybrid_results = await search_hybrid_async(
        dense_emb, sparse_emb, investigation_id, top_k=20
    )
    # Same context-resolution reasoning as the embedding step -- the
    # cross-encoder also needs to know what a follow-up is really asking
    # about, not just the bare trailing question.
    reranked = await rerank_chunks_async(retrieval_query, hybrid_results, top_n=6)

    investigation = await db.get(Investigation, investigation_id)
    company_name = (investigation.company_name if investigation else None) or "this company"

    prompt = build_chat_prompt(
        company_name=company_name,
        question=question,
        structured_context=structured_context or "(no structured analysis on record yet for this investigation)",
        tagged_chunks=reranked,
        conversation_history=recent_history,
    )

    try:
        answer = await asyncio.to_thread(
            call_groq,
            prompt,
            "You are a careful due diligence analyst answering questions about ONE "
            "specific company investigation. Never invent figures; cite only what's "
            "in the evidence you're given, and say plainly when the evidence doesn't "
            "cover the question.",
        )
    except Exception:
        logger.exception("Chat answer generation failed for investigation %s", investigation_id)
        error_answer = "Something went wrong generating an answer. Please try asking again."
        await _persist_message(
            db, investigation_id, "assistant", error_answer,
            sources=[s.model_dump() for s in _to_chat_sources(reranked)],
        )
        return ChatResponse(answer=error_answer, sources=_to_chat_sources(reranked))

    sources = _to_chat_sources(reranked)
    await _persist_message(
        db, investigation_id, "assistant", answer,
        sources=[s.model_dump() for s in sources],
    )
    return ChatResponse(answer=answer, sources=sources)
