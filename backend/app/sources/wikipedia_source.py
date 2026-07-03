"""
Wikipedia fetcher. Free, no auth required, high reliability.
"""
import httpx
from app.sources.base import BaseFetcher
from app.schemas.source_document import SourceDocument, SourceType


class WikipediaFetcher(BaseFetcher):
    source_type = SourceType.WIKIPEDIA

    async def _fetch_impl(self, company_name: str, **kwargs) -> SourceDocument:
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            search_resp = await client.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": f"{company_name} company",
                    "format": "json",
                    "srlimit": 1,
                },
            )
            search_resp.raise_for_status()
            results = search_resp.json().get("query", {}).get("search", [])
            if not results:
                return SourceDocument(
                    source_type=self.source_type,
                    source_name="Wikipedia",
                    raw_text="",
                    fetch_succeeded=False,
                    fetch_error="no matching page found",
                )

            page_title = results[0]["title"]

            extract_resp = await client.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "prop": "extracts",
                    "explaintext": 1,
                    "titles": page_title,
                    "format": "json",
                },
            )
            extract_resp.raise_for_status()
            pages = extract_resp.json().get("query", {}).get("pages", {})
            page = next(iter(pages.values()), {})
            extract = page.get("extract", "")

            return SourceDocument(
                source_type=self.source_type,
                source_name="Wikipedia",
                origin_url=f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}",
                title=page_title,
                raw_text=extract[:8000],
                fetch_succeeded=bool(extract.strip()),
            )