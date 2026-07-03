"""
TEAMMATE SCOPE primarily (used in REASON stage), but kept here since
investigation_service.py's deterministic health score calc depends on it.
"""
from typing import Dict


def calculate_ratios(data: Dict) -> Dict:
    ratios = {}
    revenue = data.get("revenue")
    profit = data.get("profit")
    assets = data.get("assets")
    liabilities = data.get("liabilities")

    if revenue and profit:
        ratios["profit_margin"] = round((profit / revenue) * 100, 2)
    if assets and liabilities:
        ratios["debt_ratio"] = round(liabilities / assets, 2)
    if assets and profit:
        ratios["roa"] = round((profit / assets) * 100, 2)

    return ratios
