"""
Website crawler. trafilatura does much better main-content extraction
than raw BeautifulSoup text-stripping -- it correctly drops nav/ads/
boilerplate that would otherwise pollute chunks with noise.

Also detects PDF links on each crawled page (annual reports, investor
decks, financial statements are routinely linked from an "Investor
Relations" or "About" page rather than embedded as HTML) and downloads
+parses them via the same pipeline used for user uploads -- previously
these links were completely invisible to the pipeline; the company's
own published financials sat one click away and were never read.
"""
import httpx
import trafilatura
from bs4 import BeautifulSoup
from typing import Dict
from app.sources.content_fetch_utils import fetch_full_content

CRAWL_PATHS = ["/", "/about", "/products", "/services", "/careers", "/blog", "/news", "/contact",
               "/investor-relations", "/investors", "/media", "/press"]
MAX_PDFS_PER_SITE = 5


def _extract_pdf_links(html: str, page_url: str) -> set[str]:
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        return set()
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.lower().split("?")[0].endswith(".pdf"):
            links.add(str(httpx.URL(page_url).join(href)))
    return links


async def crawl_website(base_url: str) -> Dict[str, str]:
    results = {}
    pdf_links: set[str] = set()

    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        for path in CRAWL_PATHS:
            try:
                url = base_url.rstrip("/") + path
                r = await client.get(url)
                if r.status_code == 200:
                    extracted = trafilatura.extract(r.text, include_comments=False, include_tables=True)
                    if extracted:
                        results[path] = extracted
                    pdf_links |= _extract_pdf_links(r.text, url)
            except Exception:
                continue

        for pdf_url in list(pdf_links)[:MAX_PDFS_PER_SITE]:
            text = await fetch_full_content(client, pdf_url)
            if text.strip():
                results[f"pdf:{pdf_url}"] = text

    return results
