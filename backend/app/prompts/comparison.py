"""TEAMMATE SCOPE -- company comparison prompt builder."""

def build_comparison_prompt(company_a: dict, company_b: dict) -> str:
    return f"""
Compare these two companies for investment purposes:
Company A: {company_a}
Company B: {company_b}
Cover revenue, profit, debt, growth, risk, and financial health score.
End with a clear investment recommendation explaining WHY.
"""
