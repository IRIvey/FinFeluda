"""
Deterministic health score from financial ratios -- reproducible/auditable,
not just an LLM's opinion. Used by investigation_service.py.
"""
from typing import Dict


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
