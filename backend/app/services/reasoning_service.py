"""
REASON stage. Consumes NormalizedChunks (already provenance-tagged),
runs validated structured extraction, then risk analysis that
explicitly cross-references tier 1/2 claims against tier 3/4 public
signal.
"""
import logging
from app.schemas.source_document import NormalizedChunk
from app.schemas.llm_outputs import (
    FinancialExtractionResult,
    RiskAnalysisResult,
    ExecutiveSummaryResult,
    RecommendationsResult,
)
from app.prompts.extraction import build_extraction_prompt
from app.prompts.analysis import build_risk_analysis_prompt
from app.prompts.summary import build_executive_summary_prompt
from app.prompts.recommendations import build_recommendations_prompt
from app.services.groq_service import call_groq_structured

logger = logging.getLogger(__name__)

# Cap how much raw text goes into a single prompt; prioritize
# highest-confidence-tier chunks first if we have to truncate.
MAX_CHUNKS_PER_PROMPT = 60


def _chunks_to_tagged_dicts(chunks: list[NormalizedChunk]) -> list[dict]:
    sorted_chunks = sorted(chunks, key=lambda c: c.confidence_tier)
    selected = sorted_chunks[:MAX_CHUNKS_PER_PROMPT]
    return [
        {
            "source_name": c.source_name,
            "confidence_tier": int(c.confidence_tier),
            "text": c.text,
        }
        for c in selected
    ]


def extract_financials(company_name: str, chunks: list[NormalizedChunk]) -> FinancialExtractionResult:
    """Step 7: structured extraction, validated against schema with retry."""
    if not chunks:
        logger.warning("No chunks available for %s -- returning empty extraction", company_name)
        return FinancialExtractionResult(
            company_name=company_name,
            extraction_notes="No usable source material was gathered for this investigation.",
        )

    tagged = _chunks_to_tagged_dicts(chunks)
    prompt = build_extraction_prompt(company_name, tagged)

    return call_groq_structured(
        prompt=prompt,
        schema=FinancialExtractionResult,
        system="You are a meticulous financial analyst who never reports unverified "
               "figures as fact and always flags data quality issues.",
    )


def analyze_risk(
    company_name: str,
    extraction: FinancialExtractionResult,
    chunks: list[NormalizedChunk],
) -> RiskAnalysisResult:
    """Step 10/11: risk analysis with explicit cross-referencing instruction."""
    tagged = _chunks_to_tagged_dicts(chunks)
    prompt = build_risk_analysis_prompt(
        company_name=company_name,
        extracted_financials=extraction.model_dump(),
        tagged_chunks=tagged,
    )

    return call_groq_structured(
        prompt=prompt,
        schema=RiskAnalysisResult,
        system="You are a skeptical due diligence analyst. Your job is to find what "
               "doesn't add up between what a company claims and what independent "
               "evidence shows. Never fabricate risks; ground every finding in the data.",
        max_tokens=6000,
    )


def generate_executive_summary(
    company_name: str,
    extraction: FinancialExtractionResult,
    risk: RiskAnalysisResult,
) -> ExecutiveSummaryResult:
    prompt = build_executive_summary_prompt(
        company_name=company_name,
        extracted_financials=extraction.model_dump(),
        risk_analysis=risk.model_dump(),
    )
    return call_groq_structured(
        prompt=prompt,
        schema=ExecutiveSummaryResult,
        system="You are writing for sophisticated investors. Be precise and specific.",
    )


def generate_recommendations(
    company_name: str,
    extraction: FinancialExtractionResult,
    risk: RiskAnalysisResult,
) -> RecommendationsResult:
    prompt = build_recommendations_prompt(
        company_name=company_name,
        extracted_financials=extraction.model_dump(),
        risk_analysis=risk.model_dump(),
    )
    return call_groq_structured(
        prompt=prompt,
        schema=RecommendationsResult,
        system="Every recommendation must include a concrete rationale tied to the data. "
               "Never output a recommendation without explaining why.",
    )