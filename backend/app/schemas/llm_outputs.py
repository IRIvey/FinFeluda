"""
Strict output schemas for everything we ask Groq to extract or
reason about. These are the validation contract: if the model's
JSON doesn't fit, we retry rather than silently accepting garbage.
"""
from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal


class YearlyFinancials(BaseModel):
    year: int
    revenue: Optional[float] = None
    profit: Optional[float] = None
    expenses: Optional[float] = None
    assets: Optional[float] = None
    liabilities: Optional[float] = None
    cash_flow: Optional[float] = None
    debt: Optional[float] = None
    currency: str = "USD"
    source_confidence: Literal["authoritative", "official", "corroborating", "unverified"] = "authoritative"

    @field_validator("year")
    @classmethod
    def reasonable_year(cls, v: int) -> int:
        if not (1980 <= v <= 2030):
            raise ValueError(f"year {v} outside plausible range")
        return v


class FinancialExtractionResult(BaseModel):
    """Output of Step 7 in the pipeline: structured financial extraction."""
    company_name: str
    industry: Optional[str] = None
    business_model: Optional[str] = None
    products: Optional[str] = None
    headquarters: Optional[str] = None
    yearly_financials: list[YearlyFinancials] = Field(default_factory=list)
    extraction_notes: Optional[str] = Field(
        default=None,
        description="Any caveats, e.g. 'figures only available for FY2023, FY2024'",
    )


class RedFlagItem(BaseModel):
    title: str
    category: Literal["financial", "operational", "business"]
    reason: str
    severity: Literal["low", "medium", "high", "critical"]
    recommendation: str
    supporting_sources: list[str] = Field(
        default_factory=list,
        description="Which sources support this flag, e.g. ['Annual Report 2024.pdf', 'GitHub']",
    )
    is_contradiction: bool = Field(
        default=False,
        description="True if this flag arises from a conflict between "
                     "company-claimed data and independent public sources",
    )


class RiskAnalysisResult(BaseModel):
    overall_risk_score: float = Field(ge=0, le=100)
    financial_risk_score: float = Field(ge=0, le=100)
    operational_risk_score: float = Field(ge=0, le=100)
    business_risk_score: float = Field(ge=0, le=100)
    red_flags: list[RedFlagItem] = Field(default_factory=list)


class ExecutiveSummaryResult(BaseModel):
    company_summary: str
    financial_summary: str
    major_risks: str
    opportunities: str
    future_outlook: str


class RecommendationItem(BaseModel):
    category: Literal["investment", "business", "financial", "operational"]
    recommendation: str
    rationale: str = Field(description="The WHY -- never a bare recommendation with no reasoning")


class RecommendationsResult(BaseModel):
    recommendations: list[RecommendationItem]