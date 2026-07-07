"""
Financial ratio calculations used by the REASON stage's health scoring
(see scoring_service.calculate_health_subscores).
"""
from typing import Dict


def calculate_ratios(data: Dict) -> Dict:
    """
    Note: current ratio (current assets / current liabilities) is part of
    the spec's ratio list but isn't computable here -- the extraction
    schema only captures total assets/liabilities, not the current vs.
    non-current split, so a "current ratio" using totals would be
    mislabeled and misleading. Deliberately omitted rather than faked.
    """
    ratios = {}
    revenue = data.get("revenue")
    profit = data.get("profit")
    assets = data.get("assets")
    liabilities = data.get("liabilities")

    if revenue and profit is not None:
        ratios["profit_margin"] = round((profit / revenue) * 100, 2)
    if assets and liabilities is not None:
        ratios["debt_ratio"] = round(liabilities / assets, 2)
    if assets and profit is not None:
        ratios["roa"] = round((profit / assets) * 100, 2)
    if assets and liabilities is not None and profit is not None:
        equity = assets - liabilities
        if equity > 0:
            ratios["roe"] = round((profit / equity) * 100, 2)

    return ratios
