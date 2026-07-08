"""
Shared helper for fetchers that stand in for a site with no company-level
search of its own (bdjobs.com's SPA, BSEC/Bangladesh Bank/MCCI's lack of
any per-company lookup) by scoping a Serper Google Search to that domain
via `site:`. Google's own crawler already indexed and rendered whatever
JS/dynamic content the site has, so this surfaces real per-company hits
without this app needing a headless browser or reverse-engineering an
undocumented API.
"""
import asyncio
import httpx


async def serper_site_search(domain: str, company_name: str, api_key: str, num: int = 10) -> list[dict]:
    """Returns Serper's raw `organic` result list for `site:{domain} {company_name}`.
    Raises on transport/HTTP errors -- callers already run inside
    BaseFetcher.fetch()'s try/except, so this doesn't need its own."""
    async with httpx.AsyncClient(timeout=12.0) as client:
        resp = await client.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={"q": f"site:{domain} {company_name}", "num": num},
        )
        resp.raise_for_status()
        return resp.json().get("organic", [])


async def serper_multi_query_search(
    domain: str,
    company_name: str,
    api_key: str,
    extra_terms: list[str],
    num: int = 10,
) -> list[dict]:
    """
    Runs the base `site:{domain} {company_name}` query plus one variant per
    term in extra_terms (e.g. "review", "complaint"), concurrently, then
    merges and dedupes by link. A single query only surfaces whatever
    Google ranks best for the bare company name -- adding opinion-shaped
    terms surfaces posts a plain name search misses, without needing any
    site-specific credentials.

    num defaults to 10 -- Serper's free tier rejects num>10 outright with
    "Query pattern not allowed for free accounts" (confirmed via direct
    testing), so more coverage has to come from more queries, not deeper
    pagination of one query.
    """
    queries = [company_name] + [f"{company_name} {term}" for term in extra_terms]

    async def run_one(q: str) -> list[dict]:
        try:
            return await serper_site_search(domain, q, api_key, num=num)
        except Exception:
            return []

    result_sets = await asyncio.gather(*[run_one(q) for q in queries])

    seen_links = set()
    merged: list[dict] = []
    for results in result_sets:
        for r in results:
            link = r.get("link")
            if link in seen_links:
                continue
            seen_links.add(link)
            merged.append(r)

    return merged


def organic_results_to_text(results: list[dict]) -> str:
    # No extra truncation here -- content_fetch_utils.enrich_with_full_content
    # already caps enriched full-page/PDF text; an un-enriched snippet is
    # already short. An earlier [:250] here silently discarded almost all
    # of the enriched content before it ever reached a chunk.
    return "\n\n".join(
        f"[{r.get('link')}] {r.get('title')}: {r.get('snippet') or ''}"
        for r in results
    )


def site_search_url(domain: str, company_name: str) -> str:
    """A link the user can actually click to re-run the same site: search
    themselves -- used as origin_url since these fetchers aggregate
    multiple results with no single canonical source link."""
    return f"https://www.google.com/search?q=site:{domain}+{company_name}"
