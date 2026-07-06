"""
Compares two investigations: pulls each one's persisted company/
financial/score data into a summary dict, then asks Groq for a
structured comparison + investment recommendation.
"""
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.dependencies import get_database
from app.models.investigation import Investigation, InvestigationStatus
from app.models.company import Company
from app.models.financial import Financial
from app.services.comparison_service import compare_two_companies

router = APIRouter()


async def _build_summary(db: AsyncSession, investigation_id: str) -> dict:
    investigation = await db.get(Investigation, investigation_id)
    if investigation is None:
        raise HTTPException(status_code=404, detail=f"Investigation {investigation_id} not found")
    if investigation.status != InvestigationStatus.completed:
        raise HTTPException(
            status_code=400,
            detail=f"Investigation {investigation_id} is '{investigation.status.value}', not "
            "'completed' -- nothing to compare yet.",
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
    latest = financials[-1] if financials else None

    return {
        "company_name": investigation.company_name,
        "industry": company.industry if company else None,
        "health_score": investigation.health_score,
        "risk_score": investigation.risk_score,
        "latest_year": latest.year if latest else None,
        "revenue": latest.revenue if latest else None,
        "profit": latest.profit if latest else None,
        "debt": latest.debt if latest else None,
    }


@router.get("/")
async def compare_investigations(id1: str, id2: str, db: AsyncSession = Depends(get_database)):
    summary_a = await _build_summary(db, id1)
    summary_b = await _build_summary(db, id2)

    comparison_text = await asyncio.to_thread(compare_two_companies, summary_a, summary_b)

    return {"comparison": comparison_text}
