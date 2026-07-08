"""
Comparison chat prompt -- answers questions about exactly two
investigations at once (the two currently selected on the Compare
page), using only each company's own gathered evidence. Deliberately
scoped to just these two companies -- never blends in a third company
or general/outside knowledge -- so a comparison answer stays as
auditable as the rest of this due-diligence tool, and every fact can
be traced back to which of the two investigations backs it.
"""
from app.prompts.extraction import CONFIDENCE_TIER_LEGEND


def _chunks_block(tagged_chunks: list[dict]) -> str:
    block = "\n\n".join(
        f"[SOURCE: {c.get('source_name', 'unknown')} | TIER {c.get('confidence_tier', 4)}]\n{c.get('text', '')}"
        for c in tagged_chunks
    )
    return block or "(no relevant document excerpts were retrieved for this question)"


def build_comparison_chat_prompt(
    company_a_name: str,
    company_b_name: str,
    question: str,
    structured_context_a: str,
    structured_context_b: str,
    tagged_chunks_a: list[dict],
    tagged_chunks_b: list[dict],
    conversation_history: list[dict] | None = None,
) -> str:
    history_block = "\n".join(
        f"{'User' if turn.get('role') == 'user' else 'Assistant'}: {turn.get('content', '')}"
        for turn in (conversation_history or [])
    )

    return f"""
You are answering a question that compares exactly two companies -- {company_a_name} (Company A)
and {company_b_name} (Company B) -- as part of an AI due diligence comparison. Answer ONLY using
the evidence below for THESE TWO companies. Do not discuss any other company, and do not use
outside/general knowledge about either company. Always make clear which company each fact belongs
to (e.g. "{company_a_name}'s revenue was X, while {company_b_name}'s was Y").

{CONFIDENCE_TIER_LEGEND}

--- RECENT CONVERSATION ---
{history_block if history_block else "(this is the first question in this conversation)"}
--- END RECENT CONVERSATION ---

--- ALREADY-COMPUTED ANALYSIS: {company_a_name} (Company A) ---
{structured_context_a or "(no structured analysis on record yet for this investigation)"}
--- END ---

--- ALREADY-COMPUTED ANALYSIS: {company_b_name} (Company B) ---
{structured_context_b or "(no structured analysis on record yet for this investigation)"}
--- END ---

--- RETRIEVED DOCUMENT EXCERPTS: {company_a_name} (Company A) ---
{_chunks_block(tagged_chunks_a)}
--- END ---

--- RETRIEVED DOCUMENT EXCERPTS: {company_b_name} (Company B) ---
{_chunks_block(tagged_chunks_b)}
--- END ---

CURRENT QUESTION: {question}

Answer in 3-6 sentences, directly comparing the two companies using actual figures, scores, or
findings from the evidence above -- label which company each fact comes from. If the evidence for
one or both companies genuinely doesn't cover this question, say so plainly rather than fabricating
an answer or bringing in a company outside these two.
"""
