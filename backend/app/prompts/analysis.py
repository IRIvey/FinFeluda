"""
Risk analysis prompt -- this is where cross-referencing/contradiction
detection happens. The model gets both company claims (tier 1/2) and
independent public signal (tier 3/4) and is told to compare them.
"""
from app.prompts.extraction import CONFIDENCE_TIER_LEGEND


def build_risk_analysis_prompt(company_name: str, extracted_financials: dict, tagged_chunks: list[dict]) -> str:
    chunks_block = "\n\n".join(
        f"[SOURCE: {c['source_name']} | TIER {c['confidence_tier']}]\n{c['text']}"
        for c in sorted(tagged_chunks, key=lambda c: c["confidence_tier"])
    )

    return f"""
Perform a risk analysis for: {company_name}

{CONFIDENCE_TIER_LEGEND}

EXTRACTED FINANCIAL DATA (already validated, tier 1/2 only):
{extracted_financials}

--- ALL SOURCE MATERIAL (includes tier 3/4 public sentiment) ---
{chunks_block}
--- END SOURCE MATERIAL ---

Your task:
1. Identify financial, operational, and business risks using the extracted financial data
   as your primary evidence.
2. CROSS-REFERENCE: actively look for contradictions between what the company's own
   materials claim (tier 1/2) and what independent public sources suggest (tier 3/4).
   Examples of the kind of contradiction to look for: claimed growth vs. declining
   GitHub activity; claimed strong operations vs. negative Reddit sentiment about
   product/service quality; claimed financial health vs. absence of expected SEC filings.
3. For every red flag, set is_contradiction=true ONLY if it specifically arises from
   a conflict between company claims and independent signal -- not for risks that are
   simply visible in the financial data alone.
4. Every red flag must cite which sources support it in supporting_sources.
5. Do not invent risks not supported by the source material. If evidence is thin,
   say so in the reason field rather than fabricating a confident-sounding risk.
6. Score severity honestly -- "low" and "medium" are valid and expected for most
   findings; reserve "critical" for findings with clear, well-evidenced financial harm.
"""