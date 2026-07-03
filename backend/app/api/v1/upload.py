"""
Upload endpoint: saves PDFs to Cloudinary, creates the Investigation
row (status=pending), kicks off gather+normalize as a background task.
This is the entry point into your owned pipeline.
"""
import uuid
import logging
from fastapi import APIRouter, UploadFile, File, Form, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.dependencies import get_database
from app.core.database import AsyncSessionLocal
from app.services.cloudinary_service import upload_pdf
from app.services.pdf_service import save_temp_pdf  # see pdf_service note below
from app.models.investigation import Investigation, InvestigationStatus
from app.sources.orchestrator import gather_all
from app.sources.normalizer import normalize_and_store
from typing import List, Optional

logger = logging.getLogger(__name__)
router = APIRouter()


async def _gather_and_normalize(
    investigation_id: str,
    company_name: str,
    local_pdf_paths: list[str],
    website_url: Optional[str],
):
    """
    Runs gather + normalize, updates Investigation.status when done.
    This is the actual boundary of your scope -- it stops here.
    Your teammate's /analyze picks up from the normalized chunks.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Investigation).where(Investigation.id == investigation_id)
        )
        investigation = result.scalar_one_or_none()
        if investigation is None:
            return

        investigation.status = InvestigationStatus.processing
        await db.commit()

        try:
            documents = await gather_all(
                company_name=company_name,
                pdf_paths=local_pdf_paths,
                website_url=website_url,
            )
            chunks = await normalize_and_store(investigation_id, documents)

            if not chunks:
                investigation.status = InvestigationStatus.failed
                logger.error("No usable chunks for investigation %s", investigation_id)
            else:
                # Status here means "data is ready for analysis" --
                # NOT "analysis is done". Your teammate's /analyze
                # endpoint moves it to a further status when reasoning
                # completes. Coordinate the exact status enum values
                # with them so polling doesn't get confused.
                investigation.status = InvestigationStatus.gathered
                investigation.company_name = company_name

        except Exception:
            logger.exception("Gather/normalize failed for %s", investigation_id)
            investigation.status = InvestigationStatus.failed

        await db.commit()


@router.post("/")
async def upload_documents(
    background_tasks: BackgroundTasks,
    company_name: str = Form(...),
    files: List[UploadFile] = File(default=[]),
    website_url: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_database),
):
    investigation_id = str(uuid.uuid4())
    local_pdf_paths = []

    for f in files:
        content = await f.read()
        # Upload to Cloudinary for permanent storage/sharing...
        upload_pdf(content, filename=f"{investigation_id}_{f.filename}")
        # ...but also keep a local temp copy for immediate text extraction,
        # since re-downloading from Cloudinary mid-pipeline is wasted latency.
        local_path = save_temp_pdf(content, f"{investigation_id}_{f.filename}")
        local_pdf_paths.append(local_path)

    source_type = "both" if (files and website_url) else ("pdf" if files else "url")

    investigation = Investigation(
        id=investigation_id,
        status=InvestigationStatus.pending,
        source_type=source_type,
        source_url=website_url,
    )
    db.add(investigation)
    await db.commit()

    background_tasks.add_task(
        _gather_and_normalize, investigation_id, company_name, local_pdf_paths, website_url
    )

    return {
        "investigation_id": investigation_id,
        "status": "pending",
        "message": "Gathering and normalizing source data...",
    }