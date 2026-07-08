"""
YouTube fetcher (Data API v3, free quota -- enable at
console.cloud.google.com, same project as Google Maps works fine)
and Google Search fetcher (via serper.dev free tier -- 2500 free
queries, no credit card; raw Google has no usable free search API
so this is the standard substitute).
"""
import asyncio
import httpx
from app.sources.base import BaseFetcher
from app.schemas.source_document import SourceDocument, SourceType
from app.sources.content_fetch_utils import enrich_with_full_content

MAX_VIDEOS_WITH_COMMENTS = 5
MAX_COMMENTS_PER_VIDEO = 5


class YouTubeFetcher(BaseFetcher):
    source_type = SourceType.YOUTUBE

    async def _fetch_top_comments(
        self, client: httpx.AsyncClient, video_id: str, api_key: str
    ) -> list[str]:
        """Real viewer comments -- genuine personal reactions, unlike the
        video's own title/description (which is the uploader's copy, often
        promotional). Degrades to [] on any failure (comments disabled,
        video not found, quota, etc.) rather than raising -- a missing
        comment thread for one video shouldn't break the whole fetch."""
        try:
            resp = await client.get(
                "https://www.googleapis.com/youtube/v3/commentThreads",
                params={
                    "videoId": video_id,
                    "part": "snippet",
                    "order": "relevance",
                    "maxResults": MAX_COMMENTS_PER_VIDEO,
                    "key": api_key,
                },
            )
            if resp.status_code != 200:
                return []
            items = resp.json().get("items", [])
            # textOriginal, not textDisplay -- textDisplay includes raw
            # HTML markup (<br>, <a href>) for rendering, which is just
            # noise in an LLM prompt.
            return [
                item["snippet"]["topLevelComment"]["snippet"].get("textOriginal", "").strip()
                for item in items
            ]
        except Exception:
            return []

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

            video_ids = [item.get("id", {}).get("videoId") for item in items[:MAX_VIDEOS_WITH_COMMENTS]]
            comment_sets = await asyncio.gather(
                *[self._fetch_top_comments(client, vid, api_key) for vid in video_ids if vid]
            )
            comments_by_video_id = dict(zip([v for v in video_ids if v], comment_sets))

            lines = []
            for item in items:
                snippet = item.get("snippet", {})
                video_id = item.get("id", {}).get("videoId")
                lines.append(
                    f"[{snippet.get('channelTitle')}] {snippet.get('publishedAt', '')[:10]}: "
                    f"\"{snippet.get('title')}\" -- {snippet.get('description') or ''}"
                )
                for comment in comments_by_video_id.get(video_id, []):
                    if comment:
                        lines.append(f"  Comment: {comment}")

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

            # Fetch full page/PDF content for the top results instead of
            # settling for Serper's ~250-char snippet -- arbitrary external
            # domains, so some will still fail (paywalls, blockers); those
            # just keep their original snippet via enrich_with_full_content's
            # per-result fallback.
            organic = await enrich_with_full_content(organic)

            lines = []
            # Knowledge graph (if present) often has clean structured facts -- include first
            kg = data.get("knowledgeGraph")
            if kg:
                lines.append(
                    f"[Knowledge Graph] {kg.get('title')}: {kg.get('description', '')} "
                    f"({kg.get('website', '')})"
                )

            for r in organic:
                # No extra truncation here -- content_fetch_utils already
                # caps enriched full-page/PDF text (3000/6000 chars); a
                # snippet that was never enriched is already short.
                lines.append(f"[{r.get('link')}] {r.get('title')}: {r.get('snippet') or ''}")

            return SourceDocument(
                source_type=self.source_type,
                source_name="Google Search",
                origin_url=f"https://www.google.com/search?q={company_name}",
                title=f"Web search results for {company_name}",
                raw_text="\n\n".join(lines),
                fetch_succeeded=True,
            )
