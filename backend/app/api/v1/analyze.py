"""
Triggers the full GATHER -> NORMALIZE -> REASON pipeline for an
investigation. In production this should run as a background task
(Celery/RQ) so the request returns immediately and the frontend polls
/investigations/{id}/status -- shown here with BackgroundTasks for simplicity.
"""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.dependencies import get_database
from app.services.investigation_service import run_pipeline

router = APIRouter()


async def _run_and_persist(investigation_id: str, company_name: str,
                            pdf_paths: list[str] | None, website_url: str | None, db: Session):
    result = await run_pipeline(
        investigation_id=investigation_id,
        company_name=company_name,
        pdf_paths=pdf_paths,
        website_url=website_url,
    )
    # TODO: persist result.extraction / risk_analysis / executive_summary /
    # recommendations / health_score / risk_score into PostgreSQL here,
    # and update the Investigation row's status field.


@router.post("/{investigation_id}")
async def trigger_analysis(
    investigation_id: str,
    background_tasks: BackgroundTasks,
    company_name: str,
    pdf_paths: list[str] | None = None,
    website_url: str | None = None,
    db: Session = Depends(get_database),
):
    if not pdf_paths and not website_url:
        raise HTTPException(
            status_code=400,
            detail="At least one of pdf_paths or website_url is required to identify the company.",
        )

    background_tasks.add_task(
        _run_and_persist, investigation_id, company_name, pdf_paths, website_url, db
    )

    return {
        "message": "Analysis started",
        "investigation_id": investigation_id,
        "status": "processing",
    }