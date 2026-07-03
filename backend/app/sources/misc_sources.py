"""
News fetcher (NewsAPI free tier, register at newsapi.org) and
Google Places fetcher (free tier, enable at console.cloud.google.com).
"""
import httpx
from app.sources.base import BaseFetcher
from app.schemas.source_document import SourceDocument, SourceType


class NewsFetcher(BaseFetcher):
    source_type = SourceType.NEWS_ARTICLE

    async def _fetch_impl(self, company_name: str, **kwargs) -> SourceDocument:
        api_key = kwargs.get("news_api_key")
        if not api_key:
            return SourceDocument(
                source_type=self.source_type,
                source_name="News",
                raw_text="",
                fetch_succeeded=False,
                fetch_error="NEWS_API_KEY not configured -- skipping",
            )

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            resp = await client.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": company_name,
                    "sortBy": "publishedAt",
                    "language": "en",
                    "pageSize": 10,
                    "apiKey": api_key,
                },
            )
            resp.raise_for_status()
            articles = resp.json().get("articles", [])

            if not articles:
                return SourceDocument(
                    source_type=self.source_type,
                    source_name="News",
                    raw_text="",
                    fetch_succeeded=False,
                    fetch_error="no recent articles found",
                )

            lines = []
            for a in articles:
                lines.append(
                    f"[{a.get('source', {}).get('name')}] {a.get('publishedAt')}: "
                    f"{a.get('title')} -- {(a.get('description') or '')[:250]}"
                )

            return SourceDocument(
                source_type=self.source_type,
                source_name="News",
                title=f"News coverage of {company_name}",
                raw_text="\n\n".join(lines),
                fetch_succeeded=True,
            )


class GoogleMapsFetcher(BaseFetcher):
    source_type = SourceType.GOOGLE_MAPS

    async def _fetch_impl(self, company_name: str, **kwargs) -> SourceDocument:
        api_key = kwargs.get("google_maps_api_key")
        if not api_key:
            return SourceDocument(
                source_type=self.source_type,
                source_name="Google Maps",
                raw_text="",
                fetch_succeeded=False,
                fetch_error="GOOGLE_MAPS_API_KEY not configured -- skipping",
            )

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            find_resp = await client.get(
                "https://maps.googleapis.com/maps/api/place/findplacefromtext/json",
                params={
                    "input": company_name,
                    "inputtype": "textquery",
                    "fields": "place_id,name,formatted_address,rating,user_ratings_total",
                    "key": api_key,
                },
            )
            find_resp.raise_for_status()
            candidates = find_resp.json().get("candidates", [])

            if not candidates:
                return SourceDocument(
                    source_type=self.source_type,
                    source_name="Google Maps",
                    raw_text="",
                    fetch_succeeded=False,
                    fetch_error="no matching business listing found",
                )

            place = candidates[0]
            text = (
                f"Business: {place.get('name')}\n"
                f"Address: {place.get('formatted_address')}\n"
                f"Rating: {place.get('rating')} ({place.get('user_ratings_total')} reviews)"
            )

            return SourceDocument(
                source_type=self.source_type,
                source_name="Google Maps",
                title=place.get("name"),
                raw_text=text,
                fetch_succeeded=True,
            )