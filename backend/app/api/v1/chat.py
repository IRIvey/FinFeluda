"""
RAG chat endpoint -- one Q&A interface per investigation.

One chat window, internally topic-routed (see
app.services.chat_service.classify_topics) rather than split into
separate finance/risk/business chatbots -- keeps the UX to a single
"Ask AI" box while still grounding each answer in whichever specialized
analysis (financial rows, risk rows, executive summary) plus
RAG-retrieved document chunks is actually relevant to the question
asked. See chat_service.answer_question for the full pipeline:
embed (dense+sparse) -> hybrid search -> rerank -> sufficiency check ->
build prompt -> call Groq.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_database
from app.models.investigation import Investigation
from app.schemas.chat import ChatRequest, ChatResponse, ChatMessageOut
from app.services.chat_service import answer_question, get_chat_history

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_database)):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    investigation = await db.get(Investigation, request.investigation_id)
    if investigation is None:
        raise HTTPException(status_code=404, detail="Investigation not found")

    return await answer_question(db, request.investigation_id, request.question)


@router.get("/{investigation_id}", response_model=list[ChatMessageOut])
async def chat_history(investigation_id: str, db: AsyncSession = Depends(get_database)):
    """Full persisted conversation for this investigation, oldest first --
    lets the frontend reopen a chat and see everything already said,
    the same way Claude/ChatGPT restore a past conversation."""
    investigation = await db.get(Investigation, investigation_id)
    if investigation is None:
        raise HTTPException(status_code=404, detail="Investigation not found")

    return await get_chat_history(db, investigation_id)
