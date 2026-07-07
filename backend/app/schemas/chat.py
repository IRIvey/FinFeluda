from datetime import datetime
from pydantic import BaseModel
from typing import List


class ChatRequest(BaseModel):
    investigation_id: str
    question: str


class ChatSource(BaseModel):
    source_name: str
    source_type: str
    confidence_tier: int
    origin_url: str | None = None
    excerpt: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[ChatSource] = []


class ChatMessageOut(BaseModel):
    """One turn in a persisted conversation, returned by GET /chat/{investigation_id}
    so the frontend can re-open an investigation's chat with full history intact."""
    id: str
    role: str  # "user" | "assistant"
    content: str
    sources: List[ChatSource] = []
    created_at: datetime
