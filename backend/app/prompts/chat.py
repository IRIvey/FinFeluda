"""
RAG chat prompt -- answers questions about a single investigation using
only the reranked document chunks (+ any already-computed structured
analysis) as evidence. Deliberately instructed to say "not enough
information" rather than fall back on general world knowledge, since
this is a due-diligence tool, not a general chatbot.
"""
from app.prompts.extraction import CONFIDENCE_TIER_LEGEND


def build_chat_prompt(
    company_name: str,
    question: str,
    structured_context: str,
    tagged_chunks: list[dict],
    conversation_history: list[dict] | None = None,
) -> str:
    """
    tagged_chunks: reranked chunk payloads (dicts with source_name,
    confidence_tier, text) -- already ordered by relevance to `question`
    by the cross-encoder reranker, most relevant first. Kept in that
    order here (not re-sorted by tier, unlike extraction/analysis
    prompts) since relevance to the actual question matters more than
    trust ordering for a direct Q&A answer; the tier label alongside
    each excerpt still tells the model how much to trust it.

    conversation_history: prior turns for THIS investigation's chat,
    oldest first, as [{"role": "user"|"assistant", "content": str}, ...]
    -- already trimmed to the last few turns by the caller. Lets the
    model resolve follow-ups like "what about last year?" or "why?"
    that only make sense next to the previous exchange. Retrieval
    itself still runs fresh on the current question every time (the
    history is context for phrasing/interpretation, not a substitute
    for re-retrieving evidence).
    """
    chunks_block = "\n\n".join(
        f"[SOURCE: {c.get('source_name', 'unknown')} | TIER {c.get('confidence_tier', 4)}]\n{c.get('text', '')}"
        for c in tagged_chunks
    )

    history_block = "\n".join(
        f"{'User' if turn.get('role') == 'user' else 'Assistant'}: {turn.get('content', '')}"
        for turn in (conversation_history or [])
    )

    return f"""
You are answering a question about {company_name} as part of an AI due diligence
investigation. Answer ONLY using the evidence below -- the already-computed analysis
and the retrieved document excerpts. Do not use outside/general knowledge about this
company, and do not guess at figures that aren't in the evidence.

{CONFIDENCE_TIER_LEGEND}

--- RECENT CONVERSATION (for resolving follow-up questions like "what about last year?") ---
{history_block if history_block else "(this is the first question in this conversation)"}
--- END RECENT CONVERSATION ---

--- ALREADY-COMPUTED ANALYSIS FOR THIS INVESTIGATION ---
{structured_context}
--- END ALREADY-COMPUTED ANALYSIS ---

--- RETRIEVED DOCUMENT EXCERPTS (most relevant first) ---
{chunks_block if chunks_block else "(no relevant document excerpts were retrieved for this question)"}
--- END RETRIEVED DOCUMENT EXCERPTS ---

CURRENT QUESTION: {question}

Answer in 2-5 sentences, directly and specifically -- reference actual figures, scores,
or findings from the evidence above rather than generic statements. Use the recent
conversation only to understand what the current question is referring to, not as a
source of facts. If the evidence above genuinely doesn't cover this question, say
plainly that this investigation's data doesn't cover it rather than fabricating an answer.

If the retrieved excerpts conflict with each other (e.g. a tier 1/2 source claims one
thing and a tier 3/4 source suggests something different), do not silently pick one --
say so explicitly and note which side has the stronger source. Never blend contradictory
figures into a single averaged-sounding answer.
"""
