"""TEAMMATE SCOPE -- company timeline generation prompt builder."""

def build_timeline_prompt(company_name: str, extracted_data: dict) -> str:
    return f"""
Generate a chronological timeline of key events for {company_name} based on
the data below. Include only events with reasonable evidence -- do not invent dates.

DATA:
{extracted_data}
"""
