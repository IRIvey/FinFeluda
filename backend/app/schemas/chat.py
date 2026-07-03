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
