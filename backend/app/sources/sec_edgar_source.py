"""
SEC EDGAR fetcher. Free, official, no auth -- highest-value public
source for any US-listed company. Gets AUTHORITATIVE tier, same as
uploaded PDFs.
"""
import httpx
from app.sources.base import BaseFetcher
from app.schemas.source_document import SourceDocument, SourceType, ConfidenceTier

SEC_HEADERS = {
    "User-Agent": "AI Due Diligence Copilot research@example.com"
}


class SECEdgarFetcher(BaseFetcher):
    source_type = SourceType.SEC_FILING

    async def _fetch_impl(self, company_name: str, **kwargs) -> SourceDocument:
        async with httpx.AsyncClient(timeout=self.timeout_seconds, headers=SEC_HEADERS) as client:
            search_resp = await client.get(
                "https://www.sec.gov/cgi-bin/browse-edgar",
                params={
                    "action": "getcompany",
                    "company": company_name,
                    "type": "10-K",
                    "dateb": "",
                    "owner": "include",
                    "count": "5",
                    "output": "atom",
                },
            )
            if search_resp.status_code != 200 or "CIK" not in search_resp.text:
                return SourceDocument(
                    source_type=self.source_type,
                    source_name="SEC EDGAR",
                    raw_text="",
                    fetch_succeeded=False,
                    fetch_error="company not found in EDGAR (likely not US-public)",
                    confidence_tier=ConfidenceTier.AUTHORITATIVE,
                )

            filings_summary = search_resp.text[:6000]

            return SourceDocument(
                source_type=self.source_type,
                source_name="SEC EDGAR",
                origin_url=f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company={company_name}&type=10-K",
                title=f"{company_name} SEC Filings",
                raw_text=(
                    f"SEC EDGAR filing search results for '{company_name}' "
                    f"(10-K filings, most recent first):\n\n{filings_summary}"
                ),
                fetch_succeeded=True,
                confidence_tier=ConfidenceTier.AUTHORITATIVE,
            )