"""
Top-level pipeline orchestrator: GATHER -> NORMALIZE -> REASON -> PERSIST.
"""
import logging
from app.sources.orchestrator import gather_all
from app.sources.normalizer import normalize_and_store
from app.services.reasoning_service import (
    extract_financials, analyze_risk, generate_executive_summary, generate_recommendations,
)
from app.services.scoring_service import calculate_health_score, calculate_risk_score

logger = logging.getLogger(__name__)


class PipelineResult:
    def __init__(self):
        self.status: str = "pending"
        self.error: str | None = None
        self.extraction = None
        self.risk_analysis = None
        self.executive_summary = None
        self.recommendations = None
        self.health_score: float | None = None
        self.risk_score: float | None = None
        self.sources_used: list[str] = []
        self.sources_failed: list[str] = []


async def run_pipeline(
    investigation_id: str,
    company_name: str,
    pdf_paths: list[str] | None = None,
    website_url: str | None = None,
) -> PipelineResult:
    result = PipelineResult()

    try:
        # ---- GATHER ----
        documents = await gather_all(company_name, pdf_paths=pdf_paths, website_url=website_url)
        result.sources_used = [d.source_name for d in documents if d.fetch_succeeded]
        result.sources_failed = [d.source_name for d in documents if not d.fetch_succeeded]

        # ---- NORMALIZE ----
        chunks = await normalize_and_store(investigation_id, documents)

        if not chunks:
            result.status = "failed"
            result.error = (
                "No usable content was gathered from any source (uploaded PDFs or "
                "public sources). Cannot run analysis on empty data."
            )
            logger.error("Pipeline aborted for %s: %s", investigation_id, result.error)
            return result

        # ---- REASON ----
        result.extraction = extract_financials(company_name, chunks)
        result.risk_analysis = analyze_risk(company_name, result.extraction, chunks)
        result.executive_summary = generate_executive_summary(
            company_name, result.extraction, result.risk_analysis
        )
        result.recommendations = generate_recommendations(
            company_name, result.extraction, result.risk_analysis
        )

        # ---- SCORE ----
        result.risk_score = result.risk_analysis.overall_risk_score
        if result.extraction.yearly_financials:
            latest = max(result.extraction.yearly_financials, key=lambda y: y.year)
            result.health_score = calculate_health_score({
                "profit_margin": _safe_margin(latest.profit, latest.revenue),
                "debt_ratio": _safe_ratio(latest.liabilities, latest.assets),
            })

        result.status = "completed"
        logger.info(
            "Pipeline completed for %s (%s): %d sources used, %d failed, "
            "health_score=%s, risk_score=%s",
            investigation_id, company_name,
            len(result.sources_used), len(result.sources_failed),
            result.health_score, result.risk_score,
        )

    except Exception as exc:
        logger.exception("Pipeline failed for %s", investigation_id)
        result.status = "failed"
        result.error = str(exc)

    return result


def _safe_margin(profit, revenue) -> float | None:
    if profit is None or not revenue:
        return None
    return round((profit / revenue) * 100, 2)


def _safe_ratio(numerator, denominator) -> float | None:
    if numerator is None or not denominator:
        return None
    return round(numerator / denominator, 2)