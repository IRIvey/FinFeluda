"""
Website crawler. trafilatura does much better main-content extraction
than raw BeautifulSoup text-stripping -- it correctly drops nav/ads/
boilerplate that would otherwise pollute chunks with noise.
"""
import httpx
import trafilatura
from typing import Dict

CRAWL_PATHS = ["/", "/about", "/products", "/services", "/careers", "/blog", "/news", "/contact"]


async def crawl_website(base_url: str) -> Dict[str, str]:
    results = {}
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        for path in CRAWL_PATHS:
            try:
                url = base_url.rstrip("/") + path
                r = await client.get(url)
                if r.status_code == 200:
                    extracted = trafilatura.extract(r.text, include_comments=False, include_tables=True)
                    if extracted:
                        results[path] = extracted
            except Exception:
                continue
    return results