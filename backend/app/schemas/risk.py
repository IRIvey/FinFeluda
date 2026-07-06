from pydantic import BaseModel, field_validator
from typing import List


class RiskOut(BaseModel):
    category: str
    title: str
    reason: str
    severity: str
    recommendation: str
    score: float
    is_contradiction: bool = False
    supporting_sources: List[str] = []

    @field_validator("supporting_sources", mode="before")
    @classmethod
    def _split_sources(cls, v):
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v or []

    class Config:
        from_attributes = True
