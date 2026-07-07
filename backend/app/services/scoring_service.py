"""
Deterministic health score from financial ratios -- reproducible/auditable,
not just an LLM's opinion. Used by investigation_service.py.
"""
from typing import Dict, List, Optional
from app.services.financial_service import calculate_ratios


def calculate_health_score(financials: Dict) -> float:
    score = 50.0
    pm = financials.get("profit_margin") or 0
    dr = financials.get("debt_ratio")
    if pm > 20:
        score += 20
    elif pm > 10:
        score += 10
    elif pm < 0:
        score -= 20
    if dr is not None:
        if dr < 0.3:
            score += 15
        elif dr > 0.7:
            score -= 15
    return max(0, min(100, score))


def calculate_risk_score(risks: list) -> float:
    if not risks:
        return 50.0
    severity_map = {"low": 20, "medium": 50, "high": 75, "critical": 95}
    scores = [severity_map.get(r.get("severity", "medium"), 50) for r in risks]
    return round(sum(scores) / len(scores), 1)


def _scale(value: Optional[float], low: float, high: float) -> float:
    """Linearly maps value from [low, high] to [0, 100], clamped. Missing
    data scores a neutral 50 rather than being treated as a failure."""
    if value is None or high == low:
        return 50.0
    pct = (value - low) / (high - low) * 100
    return round(max(0.0, min(100.0, pct)), 1)


def calculate_health_subscores(yearly_financials: List[Dict]) -> Optional[Dict[str, float]]:
    """
    Growth/Liquidity/Profitability/Debt/Efficiency subscores (0-100 each)
    from extracted yearly figures. "Liquidity" is approximated from the
    equity ratio (assets-liabilities)/assets, since the extraction schema
    doesn't capture the current-assets/current-liabilities split a true
    liquidity ratio needs -- documented here rather than silently
    mislabeling it as a real current/quick ratio.
    """
    if not yearly_financials:
        return None

    sorted_years = sorted(yearly_financials, key=lambda y: y["year"])
    latest = sorted_years[-1]
    ratios = calculate_ratios(latest)

    growth = 50.0
    if len(sorted_years) >= 2:
        previous = sorted_years[-2]
        prev_revenue = previous.get("revenue")
        latest_revenue = latest.get("revenue")
        if prev_revenue:
            pct_change = (latest_revenue - prev_revenue) / prev_revenue * 100
            growth = _scale(pct_change, low=-20, high=40)

    liquidity = 50.0
    assets = latest.get("assets")
    liabilities = latest.get("liabilities")
    if assets:
        equity_ratio = (assets - (liabilities or 0)) / assets * 100
        liquidity = _scale(equity_ratio, low=-20, high=80)

    profitability = _scale(ratios.get("profit_margin"), low=-20, high=30)

    debt_ratio = ratios.get("debt_ratio")
    debt = _scale((1 - debt_ratio) * 100 if debt_ratio is not None else None, low=0, high=100)

    efficiency = _scale(ratios.get("roa"), low=-10, high=20)

    return {
        "growth": growth,
        "liquidity": liquidity,
        "profitability": profitability,
        "debt": debt,
        "efficiency": efficiency,
    }
