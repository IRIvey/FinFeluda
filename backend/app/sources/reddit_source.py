"""
Reddit fetcher. Requires a free Reddit "script" app (client_id +
client_secret) registered at reddit.com/prefs/apps, no review needed.
"""
import httpx
from app.sources.base import BaseFetcher
from app.schemas.source_document import SourceDocument, SourceType


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

    async def _fetch_impl(self, company_name: str, **kwargs) -> SourceDocument:
        client_id = kwargs.get("reddit_client_id")
        client_secret = kwargs.get("reddit_client_secret")

        if not client_id or not client_secret:
            return SourceDocument(
                source_type=self.source_type,
                source_name="Reddit",
                raw_text="",
                fetch_succeeded=False,
                fetch_error="Reddit credentials not configured -- skipping",
            )

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