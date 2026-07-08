from datetime import datetime
from pydantic import BaseModel
from typing import List, Literal


class ComparisonChatRequest(BaseModel):
    investigation_id_a: str
    investigation_id_b: str
    question: str


class ComparisonChatSource(BaseModel):
    """Same shape as ChatSource, plus which side of the comparison
    (A or B) this excerpt was retrieved for -- lets the frontend show
    sources grouped/labeled by company instead of one flat list."""
    company: Literal["A", "B"]
    source_name: str
    source_type: str
    confidence_tier: int
    origin_url: str | None = None
    excerpt: str


class ComparisonChatResponse(BaseModel):
    answer: str
    sources: List[ComparisonChatSource] = []


class ComparisonChatMessageOut(BaseModel):
    """One turn in a persisted comparison conversation, returned by
    GET /compare/chat/{id_a}/{id_b} so the frontend can re-open the
    comparison chat panel with full history intact."""
    id: str
    role: str  # "user" | "assistant"
    content: str
    sources: List[ComparisonChatSource] = []
    created_at: datetime
