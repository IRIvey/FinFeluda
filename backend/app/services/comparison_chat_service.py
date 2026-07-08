"""
Comparison chat service -- RAG-based Q&A scoped to exactly two
investigations at once (the two currently selected on the Compare
page). Deliberately narrower than a general-purpose chatbot: every
answer is built only from Company A's and Company B's own gathered
evidence, each clearly labeled, and the service never reaches for a
third company or the model's general knowledge -- same audit-trail
guarantee the single-investigation chat makes, just for a pair.

Reuses classify_topics/_build_structured_context from chat_service
(already generic on a single investigation_id) by calling them once
per side, rather than duplicating that logic here.
"""
import asyncio
import logging
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.investigation import Investigation
from app.models.comparison_chat_message import ComparisonChatMessage
from app.schemas.comparison_chat import (
    ComparisonChatResponse,
    ComparisonChatSource,
    ComparisonChatMessageOut,
)
from app.services.chat_service import classify_topics, _build_structured_context
from app.services.embedding_service import (
    generate_query_embedding_async,
    generate_sparse_query_embedding_async,
)
from app.services.qdrant_service import search_hybrid_async, has_sufficient_context_async
from app.services.groq_service import call_groq
from app.prompts.comparison_chat import build_comparison_chat_prompt

logger = logging.getLogger(__name__)

EXCERPT_MAX_CHARS = 280
MAX_HISTORY_MESSAGES = 10

# Retrieval budget is split per-side rather than reusing the
# single-chat's top_k=20/top_n=6 -- two companies' worth of full-size
# context would roughly double prompt size for no real gain, so each
# side gets a smaller slice instead.
PER_SIDE_TOP_K = 12
PER_SIDE_RERANK_N = 4


async def _get_recent_history(db: AsyncSession, id_a: str, id_b: str) -> list[dict]:
    """Last MAX_HISTORY_MESSAGES turns for this exact (A, B) pair,
    oldest first. Order-sensitive: swapping which investigation is A
    vs B on the Compare page starts a fresh thread rather than merging
    histories, which keeps "Company A" / "Company B" labels in past
    turns unambiguous."""
    rows = (await db.execute(
        select(ComparisonChatMessage)
        .where(
            ComparisonChatMessage.investigation_id_a == id_a,
            ComparisonChatMessage.investigation_id_b == id_b,
        )
        .order_by(ComparisonChatMessage.created_at.desc())
        .limit(MAX_HISTORY_MESSAGES)
    )).scalars().all()
    rows.reverse()
    return [{"role": m.role, "content": m.content} for m in rows]


async def _persist_message(
    db: AsyncSession,
    id_a: str,
    id_b: str,
    role: str,
    content: str,
    sources: list[dict] | None = None,
) -> None:
    db.add(
        ComparisonChatMessage(
            id=str(uuid.uuid4()),
            investigation_id_a=id_a,
            investigation_id_b=id_b,
            role=role,
            content=content,
            sources=sources,
        )
    )
    await db.commit()


async def get_comparison_chat_history(
    db: AsyncSession, id_a: str, id_b: str
) -> list[ComparisonChatMessageOut]:
    """Full persisted conversation for this (A, B) pair, oldest first --
    lets the Compare page's chat widget reopen with full history intact."""
    rows = (await db.execute(
        select(ComparisonChatMessage)
        .where(
            ComparisonChatMessage.investigation_id_a == id_a,
            ComparisonChatMessage.investigation_id_b == id_b,
        )
        .order_by(ComparisonChatMessage.created_at.asc())
    )).scalars().all()

    return [
        ComparisonChatMessageOut(
            id=m.id,
            role=m.role,
            content=m.content,
            sources=[ComparisonChatSource(**s) for s in (m.sources or [])],
            created_at=m.created_at,
        )
        for m in rows
    ]


def _to_comparison_sources(chunks: list[dict], company: str) -> list[ComparisonChatSource]:
    sources = []
    for c in chunks:
        text = c.get("text", "") or ""
        excerpt = text if len(text) <= EXCERPT_MAX_CHARS else text[:EXCERPT_MAX_CHARS].rstrip() + "..."
        sources.append(
            ComparisonChatSource(
                company=company,
                source_name=c.get("source_name", "unknown"),
                source_type=c.get("source_type", "unknown"),
                confidence_tier=int(c.get("confidence_tier", 4)),
                origin_url=c.get("origin_url"),
                excerpt=excerpt,
            )
        )
    return sources


async def answer_comparison_question(
    db: AsyncSession,
    investigation_id_a: str,
    investigation_id_b: str,
    question: str,
) -> ComparisonChatResponse:
    topics = classify_topics(question)

    structured_context_a, structured_context_b, recent_history = await asyncio.gather(
        _build_structured_context(db, investigation_id_a, topics),
        _build_structured_context(db, investigation_id_b, topics),
        _get_recent_history(db, investigation_id_a, investigation_id_b),
    )

    # Persist the user's turn immediately, same reasoning as the
    # single-investigation chat: never lose a question the user
    # actually asked, even if generation fails below.
    await _persist_message(db, investigation_id_a, investigation_id_b, "user", question)

    dense_emb, sparse_emb = await asyncio.gather(
        generate_query_embedding_async(question),
        generate_sparse_query_embedding_async(question),
    )

    sufficient_a, sufficient_b = await asyncio.gather(
        has_sufficient_context_async(dense_emb, sparse_emb, investigation_id_a),
        has_sufficient_context_async(dense_emb, sparse_emb, investigation_id_b),
    )

    if (
        not sufficient_a
        and not sufficient_b
        and not structured_context_a.strip()
        and not structured_context_b.strip()
    ):
        answer = (
            "Neither of these two investigations has enough gathered evidence yet to answer "
            "that question. Try re-running analysis once more sources have been gathered, or "
            "ask something closer to what's already in each report."
        )
        await _persist_message(db, investigation_id_a, investigation_id_b, "assistant", answer)
        return ComparisonChatResponse(answer=answer, sources=[])

    hybrid_a, hybrid_b = await asyncio.gather(
        search_hybrid_async(dense_emb, sparse_emb, investigation_id_a, top_k=PER_SIDE_TOP_K),
        search_hybrid_async(dense_emb, sparse_emb, investigation_id_b, top_k=PER_SIDE_TOP_K),
    )
    # Cross-encoder reranking disabled: running a third ONNX model
    # alongside the dense+sparse embedders exceeded the deploy
    # environment's memory budget. search_hybrid_async already returns
    # results sorted by fused RRF score, so the top slice per side is
    # still a reasonable (if less precise) ordering.
    reranked_a, reranked_b = hybrid_a[:PER_SIDE_RERANK_N], hybrid_b[:PER_SIDE_RERANK_N]

    inv_a = await db.get(Investigation, investigation_id_a)
    inv_b = await db.get(Investigation, investigation_id_b)
    name_a = (inv_a.company_name if inv_a else None) or "Company A"
    name_b = (inv_b.company_name if inv_b else None) or "Company B"

    prompt = build_comparison_chat_prompt(
        company_a_name=name_a,
        company_b_name=name_b,
        question=question,
        structured_context_a=structured_context_a,
        structured_context_b=structured_context_b,
        tagged_chunks_a=reranked_a,
        tagged_chunks_b=reranked_b,
        conversation_history=recent_history,
    )

    try:
        answer = await asyncio.to_thread(
            call_groq,
            prompt,
            "You are a careful due diligence analyst comparing exactly two named companies. "
            "Never invent figures, never discuss a company outside the two given, and say "
            "plainly when the evidence doesn't cover the question for one or both companies.",
        )
    except Exception:
        logger.exception(
            "Comparison chat answer generation failed for %s vs %s",
            investigation_id_a, investigation_id_b,
        )
        error_answer = "Something went wrong generating an answer. Please try asking again."
        sources = _to_comparison_sources(reranked_a, "A") + _to_comparison_sources(reranked_b, "B")
        await _persist_message(
            db, investigation_id_a, investigation_id_b, "assistant", error_answer,
            sources=[s.model_dump() for s in sources],
        )
        return ComparisonChatResponse(answer=error_answer, sources=sources)

    sources = _to_comparison_sources(reranked_a, "A") + _to_comparison_sources(reranked_b, "B")
    await _persist_message(
        db, investigation_id_a, investigation_id_b, "assistant", answer,
        sources=[s.model_dump() for s in sources],
    )
    return ComparisonChatResponse(answer=answer, sources=sources)
