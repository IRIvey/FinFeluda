"""
YouTube fetcher (Data API v3, free quota -- enable at
console.cloud.google.com, same project as Google Maps works fine)
and Google Search fetcher (via serper.dev free tier -- 2500 free
queries, no credit card; raw Google has no usable free search API
so this is the standard substitute).
"""
import httpx
from app.sources.base import BaseFetcher
from app.schemas.source_document import SourceDocument, SourceType


class YouTubeFetcher(BaseFetcher):
    source_type = SourceType.YOUTUBE

    async def _fetch_impl(self, company_name: str, **kwargs) -> SourceDocument:
        api_key = kwargs.get("youtube_api_key")
        if not api_key:
            return SourceDocument(
                source_type=self.source_type,
                source_name="YouTube",
                raw_text="",
                fetch_succeeded=False,
                fetch_error="YOUTUBE_API_KEY not configured -- skipping",
            )

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            resp = await client.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={
                    "q": company_name,
                    "part": "snippet",
                    "type": "video",
                    "order": "relevance",
                    "maxResults": 10,
                    "key": api_key,
                },
            )
            resp.raise_for_status()
            items = resp.json().get("items", [])

            if not items:
                return SourceDocument(
                    source_type=self.source_type,
                    source_name="YouTube",
                    raw_text="",
                    fetch_succeeded=False,
                    fetch_error="no relevant videos found",
                )

            lines = []
            for item in items:
                snippet = item.get("snippet", {})
                lines.append(
                    f"[{snippet.get('channelTitle')}] {snippet.get('publishedAt', '')[:10]}: "
                    f"\"{snippet.get('title')}\" -- {(snippet.get('description') or '')[:200]}"
                )

            return SourceDocument(
                source_type=self.source_type,
                source_name="YouTube",
                origin_url=f"https://www.youtube.com/results?search_query={company_name}",
                title=f"YouTube videos mentioning {company_name}",
                raw_text="\n\n".join(lines),
                fetch_succeeded=True,
            )


class GoogleSearchFetcher(BaseFetcher):
    """
    Catches press releases, third-party mentions, and general web
    presence that doesn't fit cleanly into "news article" -- e.g.
    industry directories, partner announcements, review aggregator
    summaries that show up in plain Google results.
    """
    source_type = SourceType.GOOGLE_SEARCH

    async def _fetch_impl(self, company_name: str, **kwargs) -> SourceDocument:
        api_key = kwargs.get("serper_api_key")
        if not api_key:
            return SourceDocument(
                source_type=self.source_type,
                source_name="Google Search",
                raw_text="",
                fetch_succeeded=False,
                fetch_error="SERPER_API_KEY not configured -- skipping",
            )

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            resp = await client.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
                json={"q": company_name, "num": 10},
            )
            resp.raise_for_status()
            data = resp.json()
            organic = data.get("organic", [])

            if not organic:
                return SourceDocument(
                    source_type=self.source_type,
                    source_name="Google Search",
                    raw_text="",
                    fetch_succeeded=False,
                    fetch_error="no search results found",
                )

            lines = []
            # Knowledge graph (if present) often has clean structured facts -- include first
            kg = data.get("knowledgeGraph")
            if kg:
                lines.append(
                    f"[Knowledge Graph] {kg.get('title')}: {kg.get('description', '')} "
                    f"({kg.get('website', '')})"
                )

            for r in organic:
                lines.append(
                    f"[{r.get('link')}] {r.get('title')}: {(r.get('snippet') or '')[:250]}"
                )

            return SourceDocument(
                source_type=self.source_type,
                source_name="Google Search",
                title=f"Web search results for {company_name}",
                raw_text="\n\n".join(lines),
                fetch_succeeded=True,
            )
