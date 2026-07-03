"""
Base contract for all GATHER-stage fetchers.

Hard rule: a fetcher must NEVER raise an exception out of .fetch().
If GitHub is down or Reddit rate-limits us, that is a normal,
expected condition -- not a pipeline-ending error.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from app.schemas.source_document import SourceDocument, SourceType
import logging

logger = logging.getLogger(__name__)


class BaseFetcher(ABC):
    source_type: SourceType
    timeout_seconds: float = 12.0

    @abstractmethod
    async def _fetch_impl(self, company_name: str, **kwargs) -> SourceDocument:
        """Actual fetch logic. May raise -- wrapped by fetch()."""
        raise NotImplementedError

    async def fetch(self, company_name: str, **kwargs) -> SourceDocument:
        try:
            doc = await self._fetch_impl(company_name, **kwargs)
            return doc
        except Exception as exc:
            logger.warning(
                "Fetcher %s failed for %r: %s",
                self.__class__.__name__, company_name, exc,
            )
            return SourceDocument(
                source_type=self.source_type,
                source_name=self.__class__.__name__,
                raw_text="",
                fetch_succeeded=False,
                fetch_error=str(exc),
            )

    @staticmethod
    def empty_ok(doc: SourceDocument) -> bool:
        """A successful fetch with no real content is still a failure
        for our purposes -- don't let empty strings pollute the pipeline."""
        return doc.fetch_succeeded and len(doc.raw_text.strip()) >= 50