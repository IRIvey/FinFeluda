from pydantic import BaseModel
from typing import Optional


class ReportOut(BaseModel):
    executive_summary: Optional[str]
    financial_summary: Optional[str]
    risk_summary: Optional[str]
    opportunities: Optional[str]
    future_outlook: Optional[str]
    recommendations: Optional[str]
    pdf_url: Optional[str]

    class Config:
        from_attributes = True
