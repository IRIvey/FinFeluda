from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
from app.models.investigation import InvestigationStatus
from app.schemas.company import CompanyOut
from app.schemas.financial import FinancialOut
from app.schemas.risk import RiskOut


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


class RiskAnalysisOut(BaseModel):
    overall_risk_score: Optional[float] = None
    financial_risk_score: Optional[float] = None
    operational_risk_score: Optional[float] = None
    business_risk_score: Optional[float] = None
    red_flags: List[RiskOut] = []


class ExecutiveSummaryOut(BaseModel):
    company_summary: Optional[str] = None
    financial_summary: Optional[str] = None
    major_risks: Optional[str] = None
    opportunities: Optional[str] = None
    future_outlook: Optional[str] = None


class RecommendationOut(BaseModel):
    category: str
    recommendation: str
    rationale: str


class ReportRefOut(BaseModel):
    pdf_url: Optional[str] = None


class SourceOut(BaseModel):
    """One public/uploaded source the GATHER stage actually fetched
    and stored chunks from, for the Sources page -- lets the user
    follow the same trail the AI did."""

    source_type: str
    source_name: str
    origin_url: Optional[str] = None
    confidence_tier: int
    chunk_count: int


class InvestigationDetailOut(InvestigationOut):
    """
    Full detail response for GET /investigations/{id}. Every nested
    field is optional/defaulted so an investigation that hasn't
    finished analysis yet (or failed before producing some of these)
    still serializes cleanly -- the frontend already renders an honest
    empty state per-section when these are missing.
    """

    error_message: Optional[str] = None
    financial_risk_score: Optional[float] = None
    operational_risk_score: Optional[float] = None
    business_risk_score: Optional[float] = None
    health_subscores: Optional[Dict[str, float]] = None
    company: Optional[CompanyOut] = None
    financials: List[FinancialOut] = []
    risk_analysis: Optional[RiskAnalysisOut] = None
    executive_summary: Optional[ExecutiveSummaryOut] = None
    recommendations: List[RecommendationOut] = []
    report: Optional[ReportRefOut] = None
