"""
Final due diligence report: GET returns the persisted report sections,
GET /download generates a PDF on demand (reportlab) and streams it
back directly. Cloudinary upload is best-effort archival only -- the
download must never depend on it, because Cloudinary's "Restricted
media types" account setting 401s public raw-file delivery by default.
"""
import asyncio
import logging
import re
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.dependencies import get_database
from app.models.investigation import Investigation
from app.models.company import Company
from app.models.financial import Financial
from app.models.risk import Risk
from app.models.report import Report
from app.schemas.report import ReportOut
from app.services.report_service import generate_pdf_report
from app.services.cloudinary_service import upload_pdf

logger = logging.getLogger(__name__)
router = APIRouter()


async def _get_report_row(db: AsyncSession, investigation_id: str) -> Report | None:
    return (
        await db.execute(select(Report).where(Report.investigation_id == investigation_id))
    ).scalar_one_or_none()


@router.get("/{investigation_id}", response_model=ReportOut)
async def get_report(investigation_id: str, db: AsyncSession = Depends(get_database)):
    investigation = await db.get(Investigation, investigation_id)
    if investigation is None:
        raise HTTPException(status_code=404, detail="Investigation not found")

    report = await _get_report_row(db, investigation_id)
    if report is None:
        return ReportOut(
            executive_summary=None,
            financial_summary=None,
            risk_summary=None,
            opportunities=None,
            future_outlook=None,
            recommendations=None,
            pdf_url=None,
        )
    return report


@router.get("/{investigation_id}/download")
async def download_report(investigation_id: str, db: AsyncSession = Depends(get_database)):
    investigation = await db.get(Investigation, investigation_id)
    if investigation is None:
        raise HTTPException(status_code=404, detail="Investigation not found")

    report = await _get_report_row(db, investigation_id)
    if report is None:
        raise HTTPException(
            status_code=400,
            detail="This investigation hasn't finished analysis yet -- nothing to generate a report from.",
        )

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

    data = {
        "company_name": investigation.company_name,
        "health_score": investigation.health_score,
        "risk_score": investigation.risk_score,
        "company": {
            "industry": company.industry,
            "headquarters": company.headquarters,
            "business_model": company.business_model,
            "products": company.products,
            "summary": company.summary,
        }
        if company
        else None,
        "financials": [
            {
                "year": f.year,
                "revenue": f.revenue,
                "profit": f.profit,
                "expenses": f.expenses,
                "assets": f.assets,
                "liabilities": f.liabilities,
                "cash_flow": f.cash_flow,
                "debt": f.debt,
                "currency": f.currency,
            }
            for f in financials
        ],
        "red_flags": [
            {
                "title": r.title,
                "category": r.category,
                "reason": r.reason,
                "severity": r.severity,
                "recommendation": r.recommendation,
            }
            for r in risks
        ],
        "executive_summary": {
            "company_summary": report.executive_summary,
            "financial_summary": report.financial_summary,
            "major_risks": report.risk_summary,
            "opportunities": report.opportunities,
            "future_outlook": report.future_outlook,
        },
        "recommendations": report.recommendations_json or [],
    }

    pdf_bytes = await asyncio.to_thread(generate_pdf_report, data)

    # Archive to Cloudinary if it works, but never let it block or
    # break the download -- delivery of raw files 401s on accounts
    # with the default "Restricted media types" security setting.
    if not report.pdf_url:
        try:
            pdf_url = await asyncio.to_thread(
                upload_pdf, pdf_bytes, f"{investigation_id}_report.pdf"
            )
            report.pdf_url = pdf_url
            await db.commit()
        except Exception:
            logger.warning(
                "Cloudinary archival upload failed for %s -- serving PDF anyway",
                investigation_id, exc_info=True,
            )

    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", investigation.company_name or "company")
    filename = f"{safe_name}_due_diligence_report.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
