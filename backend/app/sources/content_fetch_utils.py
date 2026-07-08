"""
Given a URL discovered via search (Serper organic results, NewsAPI
article links, etc.), fetch and extract its full content instead of
settling for the ~250-char search snippet. Two extraction paths:

  - PDF links: download bytes, reuse the exact same pdf_service pipeline
    (pymupdf + OCR fallback) already used for user-uploaded PDFs.
  - Everything else: trafilatura, same tool already used for the company
    website crawl and Wayback Machine snapshots.

Every failure degrades to an empty string rather than raising -- callers
fall back to the original snippet when this comes back empty, so a
blocked/slow/broken individual link never breaks the whole fetch.
"""
import asyncio
import logging
import os
import uuid
import httpx
import trafilatura
from app.services.pdf_service import save_temp_pdf, extract_text_from_pdf

logger = logging.getLogger(__name__)

_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
MAX_PDF_CHARS = 6000
MAX_PAGE_CHARS = 3000
FETCH_TIMEOUT_SECONDS = 15.0


async def _fetch_pdf(client: httpx.AsyncClient, url: str) -> str:
    resp = await client.get(url)
    if resp.status_code != 200:
        return ""
    temp_path = save_temp_pdf(resp.content, f"{uuid.uuid4()}.pdf")
    try:
        text = await asyncio.to_thread(extract_text_from_pdf, temp_path)
        return (text or "")[:MAX_PDF_CHARS]
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass


async def fetch_full_content(client: httpx.AsyncClient, url: str) -> str:
    """Returns extracted text, or "" on any failure/empty result."""
    if not url:
        return ""
    try:
        if url.lower().split("?")[0].endswith(".pdf"):
            return await _fetch_pdf(client, url)
        resp = await client.get(url)
        if resp.status_code != 200:
            return ""
        text = trafilatura.extract(resp.text, include_comments=False, include_tables=False)
        return (text or "")[:MAX_PAGE_CHARS]
    except Exception as exc:
        logger.warning("Full-content fetch failed for %s: %s", url, exc)
        return ""


async def enrich_with_full_content(
    results: list[dict],
    link_field: str = "link",
    content_field: str = "snippet",
    max_full_fetches: int = 5,
) -> list[dict]:
    """
    For the first max_full_fetches results (by whatever order they were
    already ranked in), replaces the short `content_field` value with full
    extracted content when the fetch succeeds -- keeps the original value
    untouched on failure. Remaining results are returned as-is; fetching
    full content for every single result would slow gather down a lot for
    diminishing returns, and search rank already puts the most relevant
    results first.

    link_field/content_field are overridable since result shapes differ
    by caller -- Serper's organic results use "link"/"snippet", NewsAPI
    articles use "url"/"description".
    """
    if not results:
        return results

    to_enrich = results[:max_full_fetches]
    async with httpx.AsyncClient(
        timeout=FETCH_TIMEOUT_SECONDS, headers=_HEADERS, follow_redirects=True
    ) as client:
        full_texts = await asyncio.gather(
            *[fetch_full_content(client, r.get(link_field, "")) for r in to_enrich]
        )

    enriched = []
    for r, full_text in zip(to_enrich, full_texts):
        r = dict(r)
        if full_text.strip():
            r[content_field] = full_text
        enriched.append(r)
    enriched.extend(results[max_full_fetches:])
    return enriched
