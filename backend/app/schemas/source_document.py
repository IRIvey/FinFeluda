"""
Core data contract for the GATHER -> NORMALIZE -> REASON pipeline.

Design principle: no text ever enters the analysis pipeline without
provenance and a confidence tier attached. This is what lets the
reasoning layer correctly weigh "the company's own audited financials"
against "a Reddit comment about the company" instead of treating
all text as equally trustworthy.
"""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from enum import Enum
import hashlib


class SourceType(str, Enum):
    # Tier 1 — authoritative, user-provided or official filings
    UPLOADED_PDF = "uploaded_pdf"

    # Tier 1 — Bangladesh regulatory/exchange
    DSE_FILING = "dse_filing"
    CSE_FILING = "cse_filing"
    RJSC_RECORD = "rjsc_record"        # stubbed -- see bd_regulatory_source.py
    BSEC_FILING = "bsec_filing"
    BANGLADESH_BANK = "bangladesh_bank"

    # Tier 2 — official but third-party-published
    COMPANY_WEBSITE = "company_website"
    WIKIPEDIA = "wikipedia"
    GITHUB = "github"
    GOOGLE_MAPS = "google_maps"
    JOB_LISTING = "job_listing"

    # Tier 3 — public sentiment / unverified signal
    NEWS_ARTICLE = "news_article"
    REDDIT = "reddit"
    YOUTUBE = "youtube"
    GOOGLE_SEARCH = "google_search"
    PRODUCT_HUNT = "product_hunt"
    APP_STORE = "app_store"
    GLASSDOOR = "glassdoor"
    WEB_ARCHIVE = "web_archive"
    CHAMBER_DIRECTORY = "chamber_directory"


class ConfidenceTier(int, Enum):
    """
    Lower number = higher evidentiary weight.
    This number is injected directly into LLM prompts so the model
    is told, explicitly, how much to trust each fact -- not left to
    infer it from context.
    """
    AUTHORITATIVE = 1   # audited filings, uploaded official docs, SEC
    OFFICIAL = 2         # company's own website, GitHub org, Maps listing
    CORROBORATING = 3    # news coverage, Wikipedia
    UNVERIFIED_SIGNAL = 4  # Reddit, YouTube comments, forum chatter


SOURCE_TIER_MAP: dict[SourceType, ConfidenceTier] = {
    SourceType.UPLOADED_PDF: ConfidenceTier.AUTHORITATIVE,
    SourceType.DSE_FILING: ConfidenceTier.AUTHORITATIVE,
    SourceType.CSE_FILING: ConfidenceTier.AUTHORITATIVE,
    SourceType.RJSC_RECORD: ConfidenceTier.AUTHORITATIVE,
    SourceType.BSEC_FILING: ConfidenceTier.AUTHORITATIVE,
    SourceType.BANGLADESH_BANK: ConfidenceTier.AUTHORITATIVE,
    SourceType.COMPANY_WEBSITE: ConfidenceTier.OFFICIAL,
    SourceType.GITHUB: ConfidenceTier.OFFICIAL,
    SourceType.GOOGLE_MAPS: ConfidenceTier.OFFICIAL,
    SourceType.JOB_LISTING: ConfidenceTier.OFFICIAL,
    SourceType.WIKIPEDIA: ConfidenceTier.CORROBORATING,
    SourceType.NEWS_ARTICLE: ConfidenceTier.CORROBORATING,
    SourceType.GOOGLE_SEARCH: ConfidenceTier.CORROBORATING,
    SourceType.WEB_ARCHIVE: ConfidenceTier.CORROBORATING,
    SourceType.CHAMBER_DIRECTORY: ConfidenceTier.CORROBORATING,
    SourceType.REDDIT: ConfidenceTier.UNVERIFIED_SIGNAL,
    SourceType.YOUTUBE: ConfidenceTier.UNVERIFIED_SIGNAL,
    SourceType.PRODUCT_HUNT: ConfidenceTier.UNVERIFIED_SIGNAL,
    SourceType.APP_STORE: ConfidenceTier.UNVERIFIED_SIGNAL,
    SourceType.GLASSDOOR: ConfidenceTier.UNVERIFIED_SIGNAL,
}


class SourceDocument(BaseModel):
    """
    A single unit of gathered content BEFORE chunking/embedding.
    Every fetcher (PDF parser, GitHub client, Reddit client, etc.)
    must produce these, never raw strings.
    """
    source_type: SourceType
    source_name: str                      # e.g. "GitHub", "Annual Report 2024.pdf"
    origin_url: Optional[str] = None       # None for uploaded files
    title: Optional[str] = None
    raw_text: str
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    confidence_tier: ConfidenceTier = ConfidenceTier.UNVERIFIED_SIGNAL
    fetch_succeeded: bool = True
    fetch_error: Optional[str] = None
    extra_metadata: dict = Field(default_factory=dict)

    def model_post_init(self, __context) -> None:
        # Auto-assign confidence tier from source type unless explicitly overridden
        if self.confidence_tier == ConfidenceTier.UNVERIFIED_SIGNAL:
            self.confidence_tier = SOURCE_TIER_MAP.get(
                self.source_type, ConfidenceTier.UNVERIFIED_SIGNAL
            )

    @property
    def content_hash(self) -> str:
        """Used for dedup -- the same fact shouldn't be double-counted
        if two sources happen to surface the same text."""
        return hashlib.sha256(self.raw_text.encode("utf-8")).hexdigest()[:16]


class NormalizedChunk(BaseModel):
    """
    Output of the NORMALIZE stage. This is what actually gets embedded
    and stored in Qdrant. Carries the same provenance as its parent
    SourceDocument so retrieval and reasoning never lose the trail.
    """
    chunk_id: str
    investigation_id: str
    text: str
    source_type: SourceType
    source_name: str
    origin_url: Optional[str] = None
    confidence_tier: ConfidenceTier
    chunk_index: int
    content_hash: str

    def to_qdrant_payload(self) -> dict:
        return {
            "investigation_id": self.investigation_id,
            "text": self.text,
            "source_type": self.source_type.value,
            "source_name": self.source_name,
            "origin_url": self.origin_url,
            "confidence_tier": int(self.confidence_tier),
            "chunk_index": self.chunk_index,
            "content_hash": self.content_hash,
        }