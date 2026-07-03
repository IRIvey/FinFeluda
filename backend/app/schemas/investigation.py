from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.investigation import InvestigationStatus


class InvestigationCreate(BaseModel):
    company_name: str
    website_url: Optional[str] = None


class InvestigationOut(BaseModel):
    id: str
    company_name: Optional[str]
    status: InvestigationStatus
    health_score: Optional[float]
    risk_score: Optional[float]
    source_type: str
    created_at: datetime

    class Config:
        from_attributes = True
