def build_executive_summary_prompt(company_name: str, extracted_financials: dict, risk_analysis: dict) -> str:
    return f"""
Write an executive summary for a due diligence report on: {company_name}

FINANCIAL DATA:
{extracted_financials}

RISK ANALYSIS:
{risk_analysis}

Write five sections: company_summary, financial_summary, major_risks, opportunities,
future_outlook. Each should be 3-5 sentences, written for an investor audience.
Be specific and reference actual figures/risks from the data above -- avoid generic
boilerplate language. If the underlying data is sparse for any section, say so plainly
rather than padding with vague statements.
"""