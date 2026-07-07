"""
Writes REASON-stage output (financial extraction, risk analysis,
executive summary, recommendations) into Postgres. This is Step 12 of
the spec's backend pipeline ("Store everything inside PostgreSQL"),
which previously never ran -- /analyze computed all of this and threw
it away.

Each investigation gets one Company row, one Financial row per year,
one Risk row per red flag, and one Report row. Re-running analysis for
the same investigation_id replaces the previous rows (delete + insert)
rather than accumulating duplicates.
"""
import logging
import uuid
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.financial import Financial
from app.models.risk import Risk
from app.models.report import Report
from app.models.investigation import Investigation, InvestigationStatus
from app.schemas.llm_outputs import (
    FinancialExtractionResult,
    RiskAnalysisResult,
    ExecutiveSummaryResult,
    RecommendationsResult,
)
from app.services.scoring_service import calculate_health_subscores

logger = logging.getLogger(__name__)


def _format_recommendations(recommendations: RecommendationsResult) -> str:
    return "\n\n".join(
        f"[{r.category.upper()}] {r.recommendation}\nWhy: {r.rationale}"
        for r in recommendations.recommendations
    )


async def persist_analysis_results(
    db: AsyncSession,
    investigation_id: str,
    extraction: FinancialExtractionResult,
    risk: RiskAnalysisResult,
    summary: ExecutiveSummaryResult,
    recommendations: RecommendationsResult,
) -> float:
    """Persists everything and returns the computed overall health score."""

    await db.execute(delete(Company).where(Company.investigation_id == investigation_id))
    db.add(
        Company(
            id=str(uuid.uuid4()),
            investigation_id=investigation_id,
            name=extraction.company_name,
            industry=extraction.industry,
            headquarters=extraction.headquarters,
            business_model=extraction.business_model,
            products=extraction.products,
            summary=summary.company_summary,
        )
    )

    await db.execute(delete(Financial).where(Financial.investigation_id == investigation_id))
    yearly_dicts = []
    for yearly in extraction.yearly_financials:
        db.add(
            Financial(
                id=str(uuid.uuid4()),
                investigation_id=investigation_id,
                year=yearly.year,
                revenue=yearly.revenue,
                profit=yearly.profit,
                expenses=yearly.expenses,
                assets=yearly.assets,
                liabilities=yearly.liabilities,
                cash_flow=yearly.cash_flow,
                debt=yearly.debt,
                currency=yearly.currency,
            )
        )
        yearly_dicts.append(yearly.model_dump())

    await db.execute(delete(Risk).where(Risk.investigation_id == investigation_id))
    for flag in risk.red_flags:
        db.add(
            Risk(
                id=str(uuid.uuid4()),
                investigation_id=investigation_id,
                category=flag.category,
                title=flag.title,
                reason=flag.reason,
                severity=flag.severity,
                recommendation=flag.recommendation,
                score=risk.overall_risk_score,
                is_contradiction=flag.is_contradiction,
                supporting_sources=", ".join(flag.supporting_sources),
            )
        )

    await db.execute(delete(Report).where(Report.investigation_id == investigation_id))
    db.add(
        Report(
            id=str(uuid.uuid4()),
            investigation_id=investigation_id,
            executive_summary=summary.company_summary,
            financial_summary=summary.financial_summary,
            risk_summary=summary.major_risks,
            opportunities=summary.opportunities,
            future_outlook=summary.future_outlook,
            recommendations=_format_recommendations(recommendations),
            recommendations_json=[r.model_dump() for r in recommendations.recommendations],
        )
    )

    subscores = calculate_health_subscores(yearly_dicts)
    health_score = round(sum(subscores.values()) / len(subscores), 1) if subscores else None

    investigation = await db.get(Investigation, investigation_id)
    if investigation is not None:
        investigation.company_name = extraction.company_name or investigation.company_name
        investigation.status = InvestigationStatus.completed
        investigation.health_score = health_score
        investigation.health_subscores = subscores
        investigation.risk_score = risk.overall_risk_score
        investigation.financial_risk_score = risk.financial_risk_score
        investigation.operational_risk_score = risk.operational_risk_score
        investigation.business_risk_score = risk.business_risk_score
        investigation.error_message = None

    await db.commit()
    logger.info("Persisted analysis results for investigation %s", investigation_id)
    return health_score


async def mark_investigation_failed(db: AsyncSession, investigation_id: str, error: str) -> None:
    investigation = await db.get(Investigation, investigation_id)
    if investigation is not None:
        investigation.status = InvestigationStatus.failed
        investigation.error_message = error[:2000]
        await db.commit()
