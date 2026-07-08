"""
GATHER-stage orchestrator. Runs the uploaded-PDF path and every
public-source fetcher concurrently. Each fetcher is independently
fail-safe, so a dead API never blocks or corrupts the rest.
"""
import asyncio
import logging
from typing import Optional

from app.schemas.source_document import SourceDocument, SourceType, ConfidenceTier
from app.sources.wikipedia_source import WikipediaFetcher
from app.sources.github_source import GitHubFetcher
from app.sources.reddit_source import RedditFetcher
from app.sources.misc_sources import NewsFetcher, GoogleMapsFetcher
from app.sources.youtube_search_sources import YouTubeFetcher, GoogleSearchFetcher
from app.sources.glassdoor_source import GlassdoorFetcher
from app.sources.bd_news_source import BDNewsFetcher
from app.sources.bdjobs_source import BdJobsFetcher
from app.sources.bd_regulatory_source import (
    DSEFetcher, CSEFetcher, RJSCFetcher, BSECFetcher, BangladeshBankFetcher, MCCIFetcher,
)
from app.sources.wayback_source import fetch_wayback_snapshots
from app.services.pdf_service import extract_text_from_pdf, extract_financial_tables
from app.services.crawler_service import crawl_website
from app.core.config import settings

logger = logging.getLogger(__name__)

PUBLIC_FETCHERS = [
    WikipediaFetcher(),
    GitHubFetcher(),
    RedditFetcher(),
    NewsFetcher(),
    GoogleMapsFetcher(),
    YouTubeFetcher(),
    GoogleSearchFetcher(),
    GlassdoorFetcher(),
    BDNewsFetcher(),
    BdJobsFetcher(),
    DSEFetcher(),
    CSEFetcher(),
    RJSCFetcher(),
    BSECFetcher(),
    BangladeshBankFetcher(),
    MCCIFetcher(),
]


async def gather_pdf_documents(pdf_paths: list[str]) -> list[SourceDocument]:
    """Extract text from each uploaded PDF -- tier 1, authoritative.
    extract_text_from_pdf does blocking file I/O + parsing (pymupdf/
    pdfplumber/OCR), so it's run in a thread to avoid stalling the
    event loop, same as the embedding/Qdrant calls in normalizer.py.

    Also runs extract_financial_tables() and prepends its output --
    a large annual report's actual balance sheet/income statement live
    deep in the document, and MAX_CHUNKS_PER_PROMPT in reasoning_service.py
    prioritizes chunks by confidence tier, not by where they fall in the
    original document, but putting the tables first still means they
    survive first if anything downstream truncates by position."""
    docs = []
    for path in pdf_paths:
        try:
            text, tables_text = await asyncio.gather(
                asyncio.to_thread(extract_text_from_pdf, path),
                asyncio.to_thread(extract_financial_tables, path),
            )
            if tables_text:
                text = f"--- FINANCIAL STATEMENT TABLES ---\n{tables_text}\n\n--- FULL DOCUMENT TEXT ---\n{text}"
            docs.append(SourceDocument(
                source_type=SourceType.UPLOADED_PDF,
                source_name=path.split("/")[-1],
                raw_text=text,
                fetch_succeeded=bool(text.strip()),
                confidence_tier=ConfidenceTier.AUTHORITATIVE,
            ))
        except Exception as exc:
            logger.warning("PDF extraction failed for %s: %s", path, exc)
            docs.append(SourceDocument(
                source_type=SourceType.UPLOADED_PDF,
                source_name=path.split("/")[-1],
                raw_text="",
                fetch_succeeded=False,
                fetch_error=str(exc),
            ))
    return docs


async def gather_website_document(website_url: str) -> SourceDocument:
    """Crawl the company's own website -- tier 2, official."""
    try:
        pages = await crawl_website(website_url)
        combined = "\n\n".join(f"--- {path} ---\n{text}" for path, text in pages.items())
        return SourceDocument(
            source_type=SourceType.COMPANY_WEBSITE,
            source_name="Company Website",
            origin_url=website_url,
            raw_text=combined,
            fetch_succeeded=bool(combined.strip()),
        )
    except Exception as exc:
        logger.warning("Website crawl failed for %s: %s", website_url, exc)
        return SourceDocument(
            source_type=SourceType.COMPANY_WEBSITE,
            source_name="Company Website",
            origin_url=website_url,
            raw_text="",
            fetch_succeeded=False,
            fetch_error=str(exc),
        )


async def gather_public_sources(company_name: str) -> list[SourceDocument]:
    """
    Fan out to every public fetcher concurrently. asyncio.gather with
    return_exceptions=True is a second safety net on top of each
    fetcher's own try/catch.
    """
    api_keys = {
        "github_token": settings.GITHUB_TOKEN,
        "reddit_client_id": settings.REDDIT_CLIENT_ID,
        "reddit_client_secret": settings.REDDIT_CLIENT_SECRET,
        "news_api_key": settings.NEWS_API_KEY,
        "google_maps_api_key": settings.GOOGLE_MAPS_API_KEY,
        "youtube_api_key": settings.YOUTUBE_API_KEY,
        "serper_api_key": settings.SERPER_API_KEY,
    }

    tasks = [fetcher.fetch(company_name, **api_keys) for fetcher in PUBLIC_FETCHERS]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    docs: list[SourceDocument] = []
    for fetcher, result in zip(PUBLIC_FETCHERS, results):
        if isinstance(result, Exception):
            logger.error("Unexpected fetcher crash in %s: %s", fetcher.__class__.__name__, result)
            docs.append(SourceDocument(
                source_type=fetcher.source_type,
                source_name=fetcher.__class__.__name__,
                raw_text="",
                fetch_succeeded=False,
                fetch_error=f"unexpected crash: {result}",
            ))
        else:
            docs.append(result)
    return docs


async def gather_all(
    company_name: str,
    pdf_paths: Optional[list[str]] = None,
    website_url: Optional[str] = None,
) -> list[SourceDocument]:
    """
    Top-level entry point for the GATHER stage. Runs PDF extraction,
    website crawl, and all public-source fetchers concurrently.
    """
    tasks = [gather_public_sources(company_name)]

    if pdf_paths:
        tasks.append(gather_pdf_documents(pdf_paths))
    if website_url:
        tasks.append(gather_website_document(website_url))
        tasks.append(fetch_wayback_snapshots(website_url))

    results = await asyncio.gather(*tasks)

    all_docs: list[SourceDocument] = []
    for r in results:
        if isinstance(r, list):
            all_docs.extend(r)
        else:
            all_docs.append(r)

    succeeded = [d for d in all_docs if d.fetch_succeeded]
    failed = [d for d in all_docs if not d.fetch_succeeded]
    logger.info(
        "Gather complete for %r: %d sources succeeded, %d failed (%s)",
        company_name, len(succeeded), len(failed),
        [d.source_name for d in failed],
    )

    return all_docs