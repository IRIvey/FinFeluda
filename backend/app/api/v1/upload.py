"""
Upload endpoint: saves PDFs to Cloudinary, creates the Investigation
row (status=pending), and kicks off the full pipeline as a background
task -- GATHER -> NORMALIZE -> REASON -> PERSIST, all the way through
to status=completed. Previously this stopped after NORMALIZE and
expected a separate /analyze call to finish the job; that call was
never actually wired up by the frontend, so investigations sat at
"gathered" forever. Now the REASON stage runs automatically using the
chunks already produced by NORMALIZE, no re-gathering or second HTTP
call needed.
"""
import uuid
import logging
from fastapi import APIRouter, UploadFile, File, Form, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_database
from app.core.database import AsyncSessionLocal
from app.services.cloudinary_service import upload_pdf
from app.services.pdf_service import save_temp_pdf
from app.models.investigation import Investigation, InvestigationStatus
from app.sources.orchestrator import gather_all
from app.sources.normalizer import normalize_and_store
from app.services.investigation_service import run_reason_stage
from app.services.persistence_service import mark_investigation_failed
from typing import List

logger = logging.getLogger(__name__)
router = APIRouter()


async def _run_full_pipeline(
    investigation_id: str,
    company_name: str,
    local_pdf_paths: list[str],
    website_url: str,
):
    async with AsyncSessionLocal() as db:
        investigation = await db.get(Investigation, investigation_id)
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
                await mark_investigation_failed(
                    db,
                    investigation_id,
                    "No usable content was gathered from any source (uploaded PDFs or "
                    "public sources). Cannot run analysis on empty data.",
                )
                logger.error("No usable chunks for investigation %s", investigation_id)
                return

            investigation.status = InvestigationStatus.gathered
            investigation.company_name = company_name
            await db.commit()

            await run_reason_stage(db, investigation_id, company_name, chunks)

        except Exception as exc:
            logger.exception("Pipeline failed for %s", investigation_id)
            await db.rollback()
            await mark_investigation_failed(db, investigation_id, str(exc))


@router.post("/")
async def upload_documents(
    background_tasks: BackgroundTasks,
    company_name: str = Form(...),
    files: List[UploadFile] = File(default=[]),
    # Mandatory, not optional -- gather_all() only crawls the company
    # website (and, critically, only discovers/fetches its linked PDFs --
    # annual reports, investor decks) when website_url is present. Without
    # it, a company-name-only investigation silently skips that whole
    # path and can only pick up PDF content opportunistically, if a
    # search result happens to link straight to one.
    website_url: str = Form(...),
    db: AsyncSession = Depends(get_database),
):
    investigation_id = str(uuid.uuid4())
    local_pdf_paths = []

    for f in files:
        content = await f.read()
        # Upload to Cloudinary for permanent storage/sharing, best-effort --
        # never let an archival failure (e.g. the free-tier 10MB/file cap;
        # confirmed in practice with a real 29MB annual report) crash the
        # whole request. An unhandled exception here previously propagated
        # past Starlette's error middleware in a way that drops CORS
        # headers on the fallback response, which the browser then reports
        # as a generic "Network Error" instead of the real 500/detail --
        # same defensive pattern already used for the generated report PDF
        # in report.py.
        try:
            upload_pdf(content, filename=f"{investigation_id}_{f.filename}")
        except Exception:
            logger.warning(
                "Cloudinary archival upload failed for %s -- continuing without it",
                f.filename, exc_info=True,
            )
        # ...but also keep a local temp copy for immediate text extraction,
        # since re-downloading from Cloudinary mid-pipeline is wasted latency.
        local_path = save_temp_pdf(content, f"{investigation_id}_{f.filename}")
        local_pdf_paths.append(local_path)

    source_type = "both" if files else "url"

    investigation = Investigation(
        id=investigation_id,
        status=InvestigationStatus.pending,
        source_type=source_type,
        source_url=website_url,
    )
    db.add(investigation)
    await db.commit()

    background_tasks.add_task(
        _run_full_pipeline, investigation_id, company_name, local_pdf_paths, website_url
    )

    return {
        "investigation_id": investigation_id,
        "status": "pending",
        "message": "Gathering and analyzing...",
    }
