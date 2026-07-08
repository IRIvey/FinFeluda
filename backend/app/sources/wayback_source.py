"""
Internet Archive Wayback Machine fetcher -- historical snapshots of the
company's own website.

Unlike the other fetchers in this package, this one takes a website URL
rather than a company name (no free-text search API exists for the
Wayback Machine), so it isn't a BaseFetcher/PUBLIC_FETCHERS member --
it's called directly from orchestrator.gather_all() alongside
gather_website_document(), only when a website_url was actually
provided. Useful for the "does the current story match what the
company said before" angle: a claim on the site today can be checked
against what it said a year or several years ago.

CDX API confirmed live (returns 200 JSON) -- see
https://web.archive.org/cdx/search/cdx for the query format used below.
"""
import logging
import httpx
import trafilatura
from app.schemas.source_document import SourceDocument, SourceType, ConfidenceTier

logger = logging.getLogger(__name__)

CDX_URL = "https://web.archive.org/cdx/search/cdx"
MAX_SNAPSHOTS = 2  # earliest + most recent -- enough to spot drift without over-fetching
TIMEOUT_SECONDS = 15.0


def _pick_snapshots(rows: list[list[str]]) -> list[tuple[str, str]]:
    """rows are [timestamp, original] pairs (matches the `fl` param
    requested below), already sorted oldest-first by the CDX API.
    Returns (timestamp, original_url) pairs to fetch -- the earliest
    snapshot and, if there's enough history, the most recent one too."""
    if not rows:
        return []
    if len(rows) == 1:
        return [(rows[0][0], rows[0][1])]
    return [(rows[0][0], rows[0][1]), (rows[-1][0], rows[-1][1])]


async def fetch_wayback_snapshots(website_url: str) -> SourceDocument:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            cdx_resp = await client.get(
                CDX_URL,
                params={
                    "url": website_url,
                    "output": "json",
                    "fl": "timestamp,original",  # only the 2 columns _pick_snapshots expects
                    "filter": "statuscode:200",
                    "collapse": "timestamp:8",  # one snapshot per day max
                    "limit": 50,
                },
            )
            cdx_resp.raise_for_status()
            data = cdx_resp.json()

            if not data or len(data) < 2:
                return SourceDocument(
                    source_type=SourceType.WEB_ARCHIVE,
                    source_name="Wayback Machine",
                    origin_url=website_url,
                    raw_text="",
                    fetch_succeeded=False,
                    fetch_error="no archived snapshots found for this URL",
                )

            rows = data[1:]  # first row is the column header
            snapshots = _pick_snapshots(rows)

            sections = []
            for timestamp, original in snapshots:
                snapshot_url = f"https://web.archive.org/web/{timestamp}/{original}"
                try:
                    page_resp = await client.get(snapshot_url)
                    if page_resp.status_code != 200:
                        continue
                    text = trafilatura.extract(page_resp.text, include_comments=False, include_tables=False)
                    if text:
                        year = timestamp[:4]
                        sections.append(f"--- Snapshot from {year} ({snapshot_url}) ---\n{text[:3000]}")
                except Exception as exc:
                    logger.warning("Wayback snapshot fetch failed for %s: %s", snapshot_url, exc)
                    continue

            if not sections:
                return SourceDocument(
                    source_type=SourceType.WEB_ARCHIVE,
                    source_name="Wayback Machine",
                    origin_url=website_url,
                    raw_text="",
                    fetch_succeeded=False,
                    fetch_error="snapshots found but none had extractable content",
                )

            return SourceDocument(
                source_type=SourceType.WEB_ARCHIVE,
                source_name="Wayback Machine",
                origin_url=website_url,
                title=f"Historical snapshots of {website_url}",
                raw_text="\n\n".join(sections),
                fetch_succeeded=True,
                confidence_tier=ConfidenceTier.CORROBORATING,
            )
    except Exception as exc:
        # str(exc) is empty for some httpx exception types (e.g. InvalidURL) --
        # include the class name too so this is actually debuggable.
        error_detail = f"{type(exc).__name__}: {exc}" if str(exc) else type(exc).__name__
        logger.warning("Wayback Machine fetch failed for %s: %s", website_url, error_detail)
        return SourceDocument(
            source_type=SourceType.WEB_ARCHIVE,
            source_name="Wayback Machine",
            origin_url=website_url,
            raw_text="",
            fetch_succeeded=False,
            fetch_error=error_detail,
        )
