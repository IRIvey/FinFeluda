"""Compares two companies via Groq using their persisted analysis summaries."""
from app.services.groq_service import call_groq
from app.prompts.comparison import build_comparison_prompt


def compare_two_companies(company_a: dict, company_b: dict) -> str:
    prompt = build_comparison_prompt(company_a, company_b)
    return call_groq(
        prompt,
        system="You are a due diligence analyst comparing two companies for an investor. "
        "Be specific, cite the actual figures given, and always explain WHY behind "
        "your final recommendation.",
    )
