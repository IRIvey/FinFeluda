"""
Standalone re-run of the REASON stage for an investigation whose data
has already been gathered. Reads the chunks /upload's pipeline already
stored in Qdrant instead of re-gathering from scratch -- this also
means it doesn't need pdf_paths (server-only temp paths the frontend
never has, which made the old implementation uncallable for PDF-backed
investigations). Useful for retrying analysis after a transient Groq
failure, or re-analyzing after prompts/models change.
"""
import logging
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_database
from app.core.database import AsyncSessionLocal
from app.models.investigation import Investigation, InvestigationStatus
from app.services.qdrant_service import get_all_chunks_for_investigation_async
from app.services.investigation_service import run_reason_stage

logger = logging.getLogger(__name__)
router = APIRouter()

_RE_ANALYZABLE_STATUSES = {
    InvestigationStatus.gathered,
    InvestigationStatus.completed,
    InvestigationStatus.failed,
}


async def _rerun(investigation_id: str, company_name: str):
    async with AsyncSessionLocal() as db:
        chunks = await get_all_chunks_for_investigation_async(investigation_id)
        await run_reason_stage(db, investigation_id, company_name, chunks)


@router.post("/{investigation_id}")
async def trigger_analysis(
    investigation_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_database),
):
    investigation = await db.get(Investigation, investigation_id)
    if investigation is None:
        raise HTTPException(status_code=404, detail="Investigation not found")

    if investigation.status not in _RE_ANALYZABLE_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Investigation is currently '{investigation.status.value}'. "
                "Analysis can only be (re-)run once gathering has finished."
            ),
        )
    if not investigation.company_name:
        raise HTTPException(
            status_code=400,
            detail="This investigation never recorded a company name, so gathering "
            "likely never completed successfully. Nothing to analyze.",
        )

    background_tasks.add_task(_rerun, investigation_id, investigation.company_name)

    return {
        "message": "Analysis started",
        "investigation_id": investigation_id,
        "status": "analyzing",
    }
