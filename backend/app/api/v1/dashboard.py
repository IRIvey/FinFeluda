"""Dashboard stats -- real counts from persisted investigations."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from app.core.dependencies import get_database
from app.models.investigation import Investigation, InvestigationStatus

router = APIRouter()

_PROCESSING_STATUSES = (
    InvestigationStatus.pending,
    InvestigationStatus.processing,
    InvestigationStatus.gathered,
    InvestigationStatus.analyzing,
)


@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_database)):
    total = (await db.execute(select(func.count()).select_from(Investigation))).scalar_one()
    completed = (
        await db.execute(
            select(func.count())
            .select_from(Investigation)
            .where(Investigation.status == InvestigationStatus.completed)
        )
    ).scalar_one()
    processing = (
        await db.execute(
            select(func.count())
            .select_from(Investigation)
            .where(Investigation.status.in_(_PROCESSING_STATUSES))
        )
    ).scalar_one()
    failed = (
        await db.execute(
            select(func.count())
            .select_from(Investigation)
            .where(Investigation.status == InvestigationStatus.failed)
        )
    ).scalar_one()

    return {
        "total_investigations": total,
        "completed": completed,
        "processing": processing,
        "failed": failed,
    }
