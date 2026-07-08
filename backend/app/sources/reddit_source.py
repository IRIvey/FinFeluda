"""
Reddit fetcher. Prefers the real Reddit API (free "script" app,
client_id + client_secret registered at reddit.com/prefs/apps, no
review needed) for full post text + score/comment counts. Falls back
to a Serper `site:reddit.com` search when those aren't configured --
same mechanism as bdjobs_source.py -- so this still returns real
Reddit content (title + snippet) with zero extra credentials, just
less detail than the native API gives (no score/comment counts, no
full selftext).

Neither path can currently fetch full posts or comment threads directly
-- every reddit.com subdomain (www/old/api/oauth) was confirmed network-
unreachable from this dev environment even with a plain HTML request, so
this is capped at whatever Google's snippet preview shows. To widen
coverage within that constraint, the search fallback runs several query
variants (plain company name, plus "+ review", "+ complaint", etc.)
concurrently and merges the results, rather than relying on a single
generic query.
"""
import httpx
from app.sources.base import BaseFetcher
from app.schemas.source_document import SourceDocument, SourceType
from app.sources.serper_utils import serper_multi_query_search, organic_results_to_text

REVIEW_QUERY_TERMS = ["review", "complaint", "experience", "scam"]


class RedditFetcher(BaseFetcher):
    source_type = SourceType.REDDIT

    async def _get_token(self, client: httpx.AsyncClient, client_id: str, client_secret: str) -> str:
        resp = await client.post(
            "https://www.reddit.com/api/v1/access_token",
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret),
            headers={"User-Agent": "due-diligence-copilot/1.0"},
        )
        resp.raise_for_status()
        return resp.json()["access_token"]

    async def _fetch_via_search(self, company_name: str, serper_api_key: str) -> SourceDocument:
        results = await serper_multi_query_search(
            "reddit.com", company_name, serper_api_key, extra_terms=REVIEW_QUERY_TERMS
        )
        if not results:
            return SourceDocument(
                source_type=self.source_type,
                source_name="Reddit (via search)",
                raw_text="",
                fetch_succeeded=False,
                fetch_error="no Reddit mentions found via search",
            )
        return SourceDocument(
            source_type=self.source_type,
            source_name="Reddit (via search)",
            origin_url=f"https://www.reddit.com/search/?q={company_name}",
            title=f"Reddit mentions of {company_name}",
            raw_text=organic_results_to_text(results),
            fetch_succeeded=True,
        )

    async def _fetch_impl(self, company_name: str, **kwargs) -> SourceDocument:
        client_id = kwargs.get("reddit_client_id")
        client_secret = kwargs.get("reddit_client_secret")

        if not client_id or not client_secret:
            serper_api_key = kwargs.get("serper_api_key")
            if not serper_api_key:
                return SourceDocument(
                    source_type=self.source_type,
                    source_name="Reddit",
                    raw_text="",
                    fetch_succeeded=False,
                    fetch_error="Reddit credentials and SERPER_API_KEY both not configured -- skipping",
                )
            return await self._fetch_via_search(company_name, serper_api_key)

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            token = await self._get_token(client, client_id, client_secret)
            search_resp = await client.get(
                "https://oauth.reddit.com/search",
                params={"q": company_name, "sort": "relevance", "limit": 15, "t": "year"},
                headers={
                    "Authorization": f"Bearer {token}",
                    "User-Agent": "due-diligence-copilot/1.0",
                },
            )
            search_resp.raise_for_status()
            posts = search_resp.json().get("data", {}).get("children", [])

            if not posts:
                return SourceDocument(
                    source_type=self.source_type,
                    source_name="Reddit",
                    raw_text="",
                    fetch_succeeded=False,
                    fetch_error="no relevant posts found",
                )

            lines = []
            for p in posts:
                d = p["data"]
                lines.append(
                    f"[r/{d.get('subreddit')}] \"{d.get('title')}\" "
                    f"(score={d.get('score')}, comments={d.get('num_comments')}): "
                    f"{(d.get('selftext') or '')[:300]}"
                )

            return SourceDocument(
                source_type=self.source_type,
                source_name="Reddit",
                origin_url=f"https://www.reddit.com/search/?q={company_name}",
                title=f"Reddit mentions of {company_name}",
                raw_text="\n\n".join(lines),
                fetch_succeeded=True,
            )