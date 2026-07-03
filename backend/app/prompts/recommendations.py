def build_recommendations_prompt(company_name: str, extracted_financials: dict, risk_analysis: dict) -> str:
    return f"""
Generate actionable recommendations for: {company_name}

FINANCIAL DATA:
{extracted_financials}

RISK ANALYSIS:
{risk_analysis}

Generate recommendations across these categories: investment, business, financial,
operational. For EVERY recommendation, the rationale field must explain WHY -- tie it
directly back to a specific figure or risk finding above. Never output a recommendation
without a concrete rationale. Prioritize quality over quantity -- 4-8 well-justified
recommendations are better than a long generic list.
"""