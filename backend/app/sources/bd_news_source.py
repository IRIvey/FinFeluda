"""
Bangladesh news fetcher -- RSS, no API key required.

NewsAPI's free tier (misc_sources.py's NewsFetcher) has thin coverage of
Bangladeshi outlets, so this fetcher goes straight to the outlets'
own RSS feeds instead. Feed URLs were verified live (httpx, the same
client used here) rather than assumed. Working: Daily Star, Prothom
Alo's English feed, and TBS News (correct path is /rss.xml -- an
earlier /feed guess 404'd). Still not working: bdnews24 blocks
non-browser clients with 403; Financial Express serves a JS-app-shell
page at every guessed feed path instead of real RSS (same problem as
bdjobs.com); Dhaka Tribune's guessed paths 404'd. Left out rather than
shipping a broken fetch -- revisit if the real feed URLs surface.
"""
import asyncio
import httpx
import feedparser
import trafilatura
from app.sources.base import BaseFetcher
from app.schemas.source_document import SourceDocument, SourceType

FEEDS = {
    "The Daily Star": "https://www.thedailystar.net/rss.xml",
    "Prothom Alo (English)": "https://en.prothomalo.com/feed",
    "The Business Standard": "https://www.tbsnews.net/rss.xml",
}

MAX_MATCHED_ARTICLES = 6
_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def _mentions_company(entry, company_name: str) -> bool:
    haystack = f"{entry.get('title', '')} {entry.get('summary', '')}".lower()
    return company_name.lower() in haystack


async def _fetch_full_text(client: httpx.AsyncClient, url: str) -> str:
    try:
        resp = await client.get(url)
        if resp.status_code != 200:
            return ""
        return trafilatura.extract(resp.text, include_comments=False, include_tables=False) or ""
    except Exception:
        return ""


class BDNewsFetcher(BaseFetcher):
    source_type = SourceType.NEWS_ARTICLE

    async def _fetch_impl(self, company_name: str, **kwargs) -> SourceDocument:
        async with httpx.AsyncClient(timeout=self.timeout_seconds, headers=_HEADERS) as client:
            matched: list[tuple[str, object]] = []  # (feed_name, entry)

            for feed_name, feed_url in FEEDS.items():
                try:
                    resp = await client.get(feed_url)
                    if resp.status_code != 200:
                        continue
                    parsed = feedparser.parse(resp.content)
                    for entry in parsed.entries:
                        if _mentions_company(entry, company_name):
                            matched.append((feed_name, entry))
                except Exception:
                    continue

            if not matched:
                return SourceDocument(
                    source_type=self.source_type,
                    source_name="Bangladesh News (RSS)",
                    raw_text="",
                    fetch_succeeded=False,
                    fetch_error=f"no articles mentioning {company_name!r} in current RSS feeds",
                )

            matched = matched[:MAX_MATCHED_ARTICLES]
            full_texts = await asyncio.gather(
                *[_fetch_full_text(client, entry.get("link", "")) for _, entry in matched]
            )

            lines = []
            for (feed_name, entry), full_text in zip(matched, full_texts):
                body = full_text.strip() if full_text.strip() else (entry.get("summary", "") or "")
                lines.append(
                    f"[{feed_name}] {entry.get('published', '')}: {entry.get('title', '')}\n{body[:2000]}"
                )

            return SourceDocument(
                source_type=self.source_type,
                source_name="Bangladesh News (RSS)",
                origin_url=f"https://news.google.com/search?q={company_name}",
                title=f"Bangladeshi news coverage of {company_name}",
                raw_text="\n\n".join(lines),
                fetch_succeeded=True,
            )
