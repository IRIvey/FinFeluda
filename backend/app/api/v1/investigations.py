"""
List/detail/status endpoints. Frontend polls /status to know when
gathering has finished, and fetches the full detail from GET /{id}
once analysis (REASON stage) has persisted company/financial/risk/
report data alongside the investigation row.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.dependencies import get_database
from app.models.investigation import Investigation
from app.models.company import Company
from app.models.financial import Financial
from app.models.risk import Risk
from app.models.report import Report
from app.schemas.investigation import (
    InvestigationOut,
    InvestigationDetailOut,
    RiskAnalysisOut,
    ExecutiveSummaryOut,
    ReportRefOut,
)
from typing import List

router = APIRouter()


@router.get("/", response_model=List[InvestigationOut])
async def list_investigations(db: AsyncSession = Depends(get_database)):
    result = await db.execute(
        select(Investigation).order_by(Investigation.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{investigation_id}", response_model=InvestigationDetailOut)
async def get_investigation(investigation_id: str, db: AsyncSession = Depends(get_database)):
    investigation = await db.get(Investigation, investigation_id)
    if investigation is None:
        raise HTTPException(status_code=404, detail="Investigation not found")

    company = (
        await db.execute(select(Company).where(Company.investigation_id == investigation_id))
    ).scalar_one_or_none()

    financials = (
        await db.execute(
            select(Financial)
            .where(Financial.investigation_id == investigation_id)
            .order_by(Financial.year)
        )
    ).scalars().all()

    risks = (
        await db.execute(select(Risk).where(Risk.investigation_id == investigation_id))
    ).scalars().all()

    report = (
        await db.execute(select(Report).where(Report.investigation_id == investigation_id))
    ).scalar_one_or_none()

    risk_analysis = None
    if investigation.risk_score is not None or risks:
        risk_analysis = RiskAnalysisOut(
            overall_risk_score=investigation.risk_score,
            financial_risk_score=investigation.financial_risk_score,
            operational_risk_score=investigation.operational_risk_score,
            business_risk_score=investigation.business_risk_score,
            red_flags=risks,
        )

    executive_summary = None
    if report is not None:
        executive_summary = ExecutiveSummaryOut(
            company_summary=report.executive_summary,
            financial_summary=report.financial_summary,
            major_risks=report.risk_summary,
            opportunities=report.opportunities,
            future_outlook=report.future_outlook,
        )

    return InvestigationDetailOut(
        id=investigation.id,
        company_name=investigation.company_name,
        status=investigation.status,
        health_score=investigation.health_score,
        risk_score=investigation.risk_score,
        source_type=investigation.source_type,
        created_at=investigation.created_at,
        error_message=investigation.error_message,
        financial_risk_score=investigation.financial_risk_score,
        operational_risk_score=investigation.operational_risk_score,
        business_risk_score=investigation.business_risk_score,
        health_subscores=investigation.health_subscores,
        company=company,
        financials=financials,
        risk_analysis=risk_analysis,
        executive_summary=executive_summary,
        recommendations=(report.recommendations_json if report else None) or [],
        report=ReportRefOut(pdf_url=report.pdf_url) if report else None,
    )


@router.get("/{investigation_id}/status")
async def get_status(investigation_id: str, db: AsyncSession = Depends(get_database)):
    investigation = await db.get(Investigation, investigation_id)
    if investigation is None:
        raise HTTPException(status_code=404, detail="Investigation not found")

    return {
        "investigation_id": investigation_id,
        "status": investigation.status,
        "company_name": investigation.company_name,
        "error_message": investigation.error_message,
    }
