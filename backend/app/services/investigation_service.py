"""
Shared REASON-stage runner. Both /upload (chunks already in memory
right after NORMALIZE) and /analyze (chunks re-fetched from Qdrant for
a standalone re-run) call this so the extract -> risk -> summarize+
recommend -> persist sequence and its failure handling exist in one
place instead of two copies. Three sequential Groq calls -- summary and
recommendations used to be separate calls despite depending on
identical inputs (extraction + risk, never raw chunks), so they're
merged into one (see
reasoning_service.generate_summary_and_recommendations), and review
extraction was dropped entirely, purely to cut request overhead given
how easily Groq's free-tier daily quota gets exhausted by a single
investigation.
"""
import asyncio
import gc
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.investigation import Investigation, InvestigationStatus
from app.services.reasoning_service import (
    extract_financials,
    analyze_risk,
    generate_summary_and_recommendations,
)
from app.services.persistence_service import persist_analysis_results, mark_investigation_failed

logger = logging.getLogger(__name__)


async def run_reason_stage(
    db: AsyncSession,
    investigation_id: str,
    company_name: str,
    chunks: list,
) -> None:
    """
    Runs Step 7/9/10/11 of the spec's backend pipeline (structured
    extraction, risk analysis, executive summary, recommendations) and
    persists the result (Step 12). On any failure, marks the
    investigation failed with the error recorded rather than leaving it
    stuck mid-status.
    """
    investigation = await db.get(Investigation, investigation_id)
    if investigation is None:
        return

    investigation.status = InvestigationStatus.analyzing
    await db.commit()

    try:
        if not chunks:
            await mark_investigation_failed(
                db,
                investigation_id,
                "No stored source chunks found for this investigation -- "
                "the gather step may have failed or never ran.",
            )
            return

        # Groq calls are synchronous/blocking -- run off the event loop
        # so a slow analysis doesn't stall other requests (e.g. other
        # investigations' status polling) for the ~10-30s this takes.
        extraction = await asyncio.to_thread(extract_financials, company_name, chunks)
        gc.collect()
        risk = await asyncio.to_thread(analyze_risk, company_name, extraction, chunks)
        gc.collect()
        summary, recommendations = await asyncio.to_thread(
            generate_summary_and_recommendations, company_name, extraction, risk
        )

        await persist_analysis_results(
            db, investigation_id, extraction, risk, summary, recommendations
        )
        logger.info("REASON stage completed for %s (%s)", investigation_id, company_name)

    except Exception as exc:
        logger.exception("REASON stage failed for %s", investigation_id)
        await db.rollback()
        await mark_investigation_failed(db, investigation_id, str(exc))
