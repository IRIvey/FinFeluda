"""
NORMALIZE stage. Takes the raw, heterogeneous SourceDocument list from
GATHER and turns it into a single pool of NormalizedChunk objects.

Correctness guards:
  - chunking respects sentence/paragraph boundaries, sized per
    confidence tier (see chunking.py) -- not a flat character slice
  - chunks below a minimum length are dropped (noise, not signal)
  - exact-duplicate chunks (same content_hash) are deduped across
    sources, keeping the highest-confidence-tier copy
  - empty/failed SourceDocuments never reach chunking
"""
import logging
import uuid

from app.schemas.source_document import SourceDocument, NormalizedChunk
from app.sources.chunking import chunk_text_by_boundary
from app.services.embedding_service import generate_embeddings_async, generate_sparse_embeddings_async
from app.services.qdrant_service import store_chunks_async

logger = logging.getLogger(__name__)

MIN_CHUNK_LENGTH = 40  # chars; shorter chunks are mostly noise


def normalize_documents(
    investigation_id: str,
    documents: list[SourceDocument],
) -> list[NormalizedChunk]:
    """
    Pure function: SourceDocument list -> NormalizedChunk list.
    No I/O here -- embedding/storage happens in normalize_and_store().
    """
    usable_docs = [d for d in documents if d.fetch_succeeded and d.raw_text.strip()]

    all_chunks: list[NormalizedChunk] = []
    seen_hashes: dict[str, NormalizedChunk] = {}

    for doc in usable_docs:
        # Tier-aware: dense filings get smaller/more-precise chunks,
        # conversational sources (Reddit etc.) get larger ones so
        # context isn't lost. See chunking.py for the rationale.
        raw_chunks = chunk_text_by_boundary(doc.raw_text, confidence_tier=doc.confidence_tier)

        for idx, chunk_str in enumerate(raw_chunks):
            chunk_str = chunk_str.strip()
            if len(chunk_str) < MIN_CHUNK_LENGTH:
                continue

            nc = NormalizedChunk(
                chunk_id=str(uuid.uuid4()),
                investigation_id=investigation_id,
                text=chunk_str,
                source_type=doc.source_type,
                source_name=doc.source_name,
                origin_url=doc.origin_url,
                confidence_tier=doc.confidence_tier,
                chunk_index=idx,
                content_hash=_chunk_hash(chunk_str),
            )

            existing = seen_hashes.get(nc.content_hash)
            if existing is None:
                seen_hashes[nc.content_hash] = nc
                all_chunks.append(nc)
            elif nc.confidence_tier < existing.confidence_tier:
                # lower enum value == higher trust tier
                all_chunks.remove(existing)
                all_chunks.append(nc)
                seen_hashes[nc.content_hash] = nc

    logger.info(
        "Normalized %d source documents into %d unique chunks for investigation %s",
        len(usable_docs), len(all_chunks), investigation_id,
    )
    return all_chunks


def _chunk_hash(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


async def normalize_and_store(
    investigation_id: str,
    documents: list[SourceDocument],
) -> list[NormalizedChunk]:
    """
    Full NORMALIZE stage: chunk -> dedupe -> embed (dense + sparse) -> store in Qdrant.

    Both embedding types are generated for every chunk so the chat/
    retrieval layer can do hybrid search -- dense alone misses exact
    matches (product codes, specific figures, proper nouns), sparse
    alone misses paraphrasing/synonyms. See qdrant_service.search_hybrid().
    """
    chunks = normalize_documents(investigation_id, documents)

    if not chunks:
        logger.warning("No usable chunks produced for investigation %s -- "
                        "all sources failed or returned empty content", investigation_id)
        return []

    texts = [c.text for c in chunks]
    dense_embeddings = await generate_embeddings_async(texts)
    sparse_embeddings = await generate_sparse_embeddings_async(texts)

    await store_chunks_async(chunks, dense_embeddings, sparse_embeddings)

    return chunks