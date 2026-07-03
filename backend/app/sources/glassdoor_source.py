"""
Glassdoor has no free public API and scraping it violates their ToS
(aggressive bot detection, legal risk for a hackathon project). This
fetcher exists so Glassdoor shows up explicitly in the sources list
with a clear reason -- rather than silently being absent, which would
look like an oversight instead of a deliberate call.

If a paid Glassdoor data provider (e.g. via a data broker API) becomes
available, swap the body of _fetch_impl -- the SourceDocument contract
stays the same so nothing else in the pipeline needs to change.
"""
from app.sources.base import BaseFetcher
from app.schemas.source_document import SourceDocument, SourceType


class GlassdoorFetcher(BaseFetcher):
    source_type = SourceType.GLASSDOOR

    async def _fetch_impl(self, company_name: str, **kwargs) -> SourceDocument:
        return SourceDocument(
            source_type=self.source_type,
            source_name="Glassdoor",
            raw_text="",
            fetch_succeeded=False,
            fetch_error=(
                "Glassdoor has no free public API and scraping violates its ToS -- "
                "deliberately not fetched. Consider a licensed data provider for production."
            ),
        )
