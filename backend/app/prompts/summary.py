def build_summary_and_recommendations_prompt(
    company_name: str, extracted_financials: dict, risk_analysis: dict
) -> str:
    """Combined executive summary + recommendations -- both only ever
    depended on extraction+risk (never raw chunks), so one call produces
    both instead of two separate Groq round trips."""
    return f"""
Write an executive summary and recommendations for a due diligence report on: {company_name}

FINANCIAL DATA:
{extracted_financials}

RISK ANALYSIS:
{risk_analysis}

Part 1 -- Executive summary. Write five sections: company_summary, financial_summary,
major_risks, opportunities, future_outlook. Each should be 3-5 sentences, written for
an investor audience. Be specific and reference actual figures/risks from the data
above -- avoid generic boilerplate language. If the underlying data is sparse for any
section, say so plainly rather than padding with vague statements.

Part 2 -- Recommendations. Generate recommendations across these categories: investment,
business, financial, operational. For EVERY recommendation, the rationale field must
explain WHY -- tie it directly back to a specific figure or risk finding above. Never
output a recommendation without a concrete rationale. Prioritize quality over quantity --
4-8 well-justified recommendations are better than a long generic list.
"""
