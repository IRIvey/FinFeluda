"""
Structured extraction prompts. Every chunk is labeled with its source
name and confidence tier; the prompt explicitly instructs the model
to prefer authoritative sources for hard numbers.
"""

CONFIDENCE_TIER_LEGEND = """
Source confidence tiers (lower number = more trustworthy):
  1 = AUTHORITATIVE  -- audited filings, the company's own uploaded documents, SEC filings
  2 = OFFICIAL        -- the company's own website, GitHub org, verified business listings
  3 = CORROBORATING   -- independent news coverage, Wikipedia
  4 = UNVERIFIED_SIGNAL -- social media, forums, community discussion (Reddit, YouTube, etc.)

RULES:
- Extract financial figures (revenue, profit, debt, etc.) ONLY from tier 1 or tier 2 sources.
  If a number only appears in a tier 3/4 source, do NOT report it as a fact -- you may
  mention it exists as a public claim, but never as verified financial data.
- If the same figure appears in multiple sources with different values, use the
  LOWEST tier number (most trustworthy) and note the discrepancy in extraction_notes.
- If no financial data exists in tier 1/2 sources at all, return an empty
  yearly_financials list rather than estimating or guessing.
"""


def build_extraction_prompt(company_name: str, tagged_chunks: list[dict]) -> str:
    """
    tagged_chunks: list of {"source_name": str, "confidence_tier": int, "text": str}
    """
    chunks_block = "\n\n".join(
        f"[SOURCE: {c['source_name']} | TIER {c['confidence_tier']}]\n{c['text']}"
        for c in sorted(tagged_chunks, key=lambda c: c["confidence_tier"])
    )

    return f"""
Extract structured company and financial information for: {company_name}

{CONFIDENCE_TIER_LEGEND}

--- SOURCE MATERIAL ---
{chunks_block}
--- END SOURCE MATERIAL ---

Extract company profile (industry, business model, products, headquarters) using
the best available information from any tier. Extract yearly_financials following
the strict tier rules above. Set source_confidence on each yearly entry to reflect
which tier the figures actually came from.
"""