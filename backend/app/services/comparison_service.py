"""
TEAMMATE SCOPE -- compares two investigations via Groq.
Stub only.
"""
from app.services.groq_service import call_groq


def compare_two_companies(inv1: dict, inv2: dict) -> str:
    prompt = f"""
    Compare these two companies for investment purposes:
    Company A: {inv1}
    Company B: {inv2}
    Provide a structured comparison covering revenue, profit, debt, growth, risk,
    and a final investment recommendation.
    """
    return call_groq(prompt)
