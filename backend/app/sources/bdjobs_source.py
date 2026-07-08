"""
bdjobs.com fetcher -- hiring-signal source (job postings, growth/expansion
indicators).

bdjobs.com is an Angular SPA: every URL (including the legacy
`jobs.bdjobs.com/jobsearch.asp` path) serves the same client-rendered
app shell over plain HTTP, so a normal httpx GET returns no actual job
listing content -- confirmed by fetching it directly before writing this.
Their `apiv1.bdjobs.com`/`gateway.bdjobs.com` backend has no documented
public API, so guessing at endpoints isn't a safe or reliable route.

Instead this uses serper_site_search() (site: scoped Google Search via
Serper) -- Google's own crawler renders the SPA and indexes the result,
so the search snippet surfaces real job-listing text without this app
needing a headless browser. Verified live: a `site:bdjobs.com` query for
a known company returned an actual hiring page snippet.
"""
from app.sources.base import BaseFetcher
from app.schemas.source_document import SourceDocument, SourceType
from app.sources.serper_utils import serper_site_search, organic_results_to_text, site_search_url


class BdJobsFetcher(BaseFetcher):
    source_type = SourceType.JOB_LISTING

    async def _fetch_impl(self, company_name: str, **kwargs) -> SourceDocument:
        api_key = kwargs.get("serper_api_key")
        if not api_key:
            return SourceDocument(
                source_type=self.source_type,
                source_name="bdjobs.com",
                raw_text="",
                fetch_succeeded=False,
                fetch_error="SERPER_API_KEY not configured -- skipping",
            )

        results = await serper_site_search("bdjobs.com", company_name, api_key)
        if not results:
            return SourceDocument(
                source_type=self.source_type,
                source_name="bdjobs.com",
                raw_text="",
                fetch_succeeded=False,
                fetch_error="no bdjobs.com listings found for this company",
            )

        return SourceDocument(
            source_type=self.source_type,
            source_name="bdjobs.com",
            origin_url=site_search_url("bdjobs.com", company_name),
            title=f"bdjobs.com hiring activity for {company_name}",
            raw_text=organic_results_to_text(results),
            fetch_succeeded=True,
        )
