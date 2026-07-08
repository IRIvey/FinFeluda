"""
Bangladesh regulatory, exchange, and chamber-of-commerce sources.

dsebd.org (DSE) and cse.com.bd (CSE) serve an incomplete TLS cert chain
(confirmed via openssl s_client: they skip the actual intermediate that
signed their leaf cert). truststore.inject_into_ssl() (see main.py) uses
the OS's own cert store instead of the static certifi bundle, which does
proper AIA chasing and fetches the missing intermediate itself -- fixed
without disabling verification. roc.gov.bd (RJSC) is a different,
unfixable problem: a genuinely self-signed/untrusted root, confirmed
still failing even with the OS trust store.

BSEC (sec.gov.bd), Bangladesh Bank (bb.org.bd), and MCCI (mccibd.org)
never had a TLS problem, but have no per-company search of their own --
they're regulatory/directory hubs, not databases (confirmed by reading
their actual navigation structure).

Every fetcher here therefore goes through Serper's indexed search
(serper_site_search, same mechanism as bdjobs_source.py/reddit_source.py)
scoped to the relevant domain -- this doubles as the missing "search by
company name" feature none of these sites provide themselves, and (now
that the TLS issue is fixed) discovered links get a full-content
follow-up fetch (content_fetch_utils.enrich_with_full_content) for every
domain except RJSC. Verified live: BSEC's PDF filings (e.g. an IPO
prospectus) and DSE/CSE pages/PDFs all download and parse correctly,
turning a 250-char snippet into thousands of chars of real filing text.
RJSC stays a documented "not fetched" stub -- roc.gov.bd also returns
zero indexed results at all, a second, independent reason on top of the
unfixable cert issue.
"""
from app.sources.base import BaseFetcher
from app.schemas.source_document import SourceDocument, SourceType
from app.sources.serper_utils import serper_site_search, organic_results_to_text, site_search_url
from app.sources.content_fetch_utils import enrich_with_full_content


class _SerperSiteFetcher(BaseFetcher):
    """Shared shape for 'search this domain via Serper, or explain why
    not' -- subclasses just set domain/display_name/not_found_hint."""
    domain: str
    display_name: str
    not_found_hint: str = ""
    # False only for RJSC now -- its cert issue is unfixable (genuinely
    # self-signed/untrusted root) and it returns zero indexed results
    # anyway, so a full-content fetch there would be a guaranteed-failed
    # extra request per result for zero benefit.
    fetch_full_content_enabled: bool = True

    async def _fetch_impl(self, company_name: str, **kwargs) -> SourceDocument:
        api_key = kwargs.get("serper_api_key")
        if not api_key:
            return SourceDocument(
                source_type=self.source_type,
                source_name=self.display_name,
                raw_text="",
                fetch_succeeded=False,
                fetch_error="SERPER_API_KEY not configured -- skipping",
            )

        results = await serper_site_search(self.domain, company_name, api_key)
        if self.fetch_full_content_enabled and results:
            results = await enrich_with_full_content(results)
        if not results:
            return SourceDocument(
                source_type=self.source_type,
                source_name=self.display_name,
                raw_text="",
                fetch_succeeded=False,
                fetch_error=f"no indexed {self.domain} results for this company. {self.not_found_hint}".strip(),
            )

        return SourceDocument(
            source_type=self.source_type,
            source_name=self.display_name,
            origin_url=site_search_url(self.domain, company_name),
            title=f"{self.display_name} results for {company_name}",
            raw_text=organic_results_to_text(results),
            fetch_succeeded=True,
        )


class DSEFetcher(_SerperSiteFetcher):
    source_type = SourceType.DSE_FILING
    domain = "dsebd.org"
    display_name = "Dhaka Stock Exchange (DSE)"
    not_found_hint = ""


class CSEFetcher(_SerperSiteFetcher):
    source_type = SourceType.CSE_FILING
    domain = "cse.com.bd"
    display_name = "Chittagong Stock Exchange (CSE)"
    not_found_hint = ""


class RJSCFetcher(_SerperSiteFetcher):
    source_type = SourceType.RJSC_RECORD
    domain = "roc.gov.bd"
    display_name = "RJSC (Registrar of Joint Stock Companies)"
    not_found_hint = "RJSC content doesn't appear to be Google-indexed at all; direct access is also blocked by a genuinely self-signed/untrusted TLS cert (confirmed still failing even with OS-native cert verification)."
    fetch_full_content_enabled = False


class BSECFetcher(_SerperSiteFetcher):
    source_type = SourceType.BSEC_FILING
    domain = "sec.gov.bd"
    display_name = "Bangladesh Securities and Exchange Commission (BSEC)"


class BangladeshBankFetcher(_SerperSiteFetcher):
    source_type = SourceType.BANGLADESH_BANK
    domain = "bb.org.bd"
    display_name = "Bangladesh Bank"


class MCCIFetcher(_SerperSiteFetcher):
    source_type = SourceType.CHAMBER_DIRECTORY
    domain = "mccibd.org"
    display_name = "Metropolitan Chamber of Commerce and Industry (MCCI)"
