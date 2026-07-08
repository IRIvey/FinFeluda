"""
Chat endpoint scoped to exactly two investigations at once -- the
Compare page's counterpart to the single-investigation /chat endpoint.
See comparison_chat_service.answer_comparison_question for the full
pipeline. Deliberately does NOT accept a bare company name or search
beyond these two investigation IDs -- both must already exist in this
system, so every answer stays traceable to real gathered evidence.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_database
from app.models.investigation import Investigation
from app.schemas.comparison_chat import (
    ComparisonChatRequest,
    ComparisonChatResponse,
    ComparisonChatMessageOut,
)
from app.services.comparison_chat_service import (
    answer_comparison_question,
    get_comparison_chat_history,
)

router = APIRouter()


async def _get_or_404(db: AsyncSession, investigation_id: str) -> Investigation:
    investigation = await db.get(Investigation, investigation_id)
    if investigation is None:
        raise HTTPException(status_code=404, detail=f"Investigation {investigation_id} not found")
    return investigation


@router.post("/", response_model=ComparisonChatResponse)
async def comparison_chat(
    request: ComparisonChatRequest, db: AsyncSession = Depends(get_database)
):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    await _get_or_404(db, request.investigation_id_a)
    await _get_or_404(db, request.investigation_id_b)

    return await answer_comparison_question(
        db, request.investigation_id_a, request.investigation_id_b, request.question
    )


@router.get(
    "/{investigation_id_a}/{investigation_id_b}",
    response_model=list[ComparisonChatMessageOut],
)
async def comparison_chat_history(
    investigation_id_a: str,
    investigation_id_b: str,
    db: AsyncSession = Depends(get_database),
):
    """Full persisted conversation for this exact pair, oldest first --
    lets the Compare page's chat widget reopen with history intact."""
    await _get_or_404(db, investigation_id_a)
    await _get_or_404(db, investigation_id_b)
    return await get_comparison_chat_history(db, investigation_id_a, investigation_id_b)
