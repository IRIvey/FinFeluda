"""
YOUR scope: list/detail/status endpoints. Frontend and teammates both
poll /status to know when gather+normalize has finished (status
"gathered") and data is ready in Qdrant for analysis.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.dependencies import get_database
from app.models.investigation import Investigation
from app.schemas.investigation import InvestigationOut
from typing import List

router = APIRouter()


@router.get("/", response_model=List[InvestigationOut])
async def list_investigations(db: AsyncSession = Depends(get_database)):
    result = await db.execute(
        select(Investigation).order_by(Investigation.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{investigation_id}", response_model=InvestigationOut)
async def get_investigation(investigation_id: str, db: AsyncSession = Depends(get_database)):
    result = await db.execute(
        select(Investigation).where(Investigation.id == investigation_id)
    )
    investigation = result.scalar_one_or_none()
    if investigation is None:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return investigation


@router.get("/{investigation_id}/status")
async def get_status(investigation_id: str, db: AsyncSession = Depends(get_database)):
    result = await db.execute(
        select(Investigation).where(Investigation.id == investigation_id)
    )
    investigation = result.scalar_one_or_none()
    if investigation is None:
        raise HTTPException(status_code=404, detail="Investigation not found")

    return {
        "investigation_id": investigation_id,
        "status": investigation.status,
        "company_name": investigation.company_name,
    }
