"""
Qdrant storage layer -- HYBRID retrieval (dense + sparse merged).

Every point stores TWO vectors under named vector slots:
  "dense"  -- semantic embedding (bge-small-en-v1.5), good at meaning/
              synonyms, weak at exact terms (the article's named
              dense-retrieval weakness: product codes, proper nouns,
              specific figures get missed by pure semantic search).
  "sparse" -- BM25 keyword-weighted embedding, the classic fix for
              exactly that weakness -- strong on literal term matches,
              weak on paraphrasing.

search_hybrid() queries both and merges with Reciprocal Rank Fusion
(RRF), the standard way to combine two differently-scaled ranking
systems (cosine similarity and BM25 scores aren't on the same scale,
so naively averaging them is wrong -- RRF sidesteps that by fusing on
RANK position instead of raw score).

Every point still carries full source provenance (source_type,
source_name, origin_url, confidence_tier) via
NormalizedChunk.to_qdrant_payload().

IMPORTANT: qdrant-client's sync client does blocking network I/O.
Every call here is wrapped with asyncio.to_thread() in the async
section at the bottom -- use those wrappers from async code, never
the sync functions directly.
"""
import asyncio
from collections import defaultdict
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, SparseVectorParams, PointStruct,
    Filter, FieldCondition, MatchValue, NamedVector, NamedSparseVector,
    SparseVector,
)
from app.core.config import settings
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.source_document import NormalizedChunk

EMBEDDING_DIM = 384  # BAAI/bge-small-en-v1.5 dense output size

client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)


def ensure_collection():
    collections = [c.name for c in client.get_collections().collections]
    if settings.QDRANT_COLLECTION not in collections:
        client.create_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vectors_config={
                "dense": VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
            },
            sparse_vectors_config={
                "sparse": SparseVectorParams(),
            },
        )


def store_normalized_chunks(
    chunks: List["NormalizedChunk"],
    dense_embeddings: List[List[float]],
    sparse_embeddings: List[dict],
) -> None:
    """
    Sync implementation. Call store_chunks_async() from async code.

    sparse_embeddings: list of {"indices": [...], "values": [...]} dicts,
    as produced by embedding_service.generate_sparse_embeddings().
    """
    ensure_collection()
    points = [
        PointStruct(
            id=chunk.chunk_id,
            vector={
                "dense": dense_vec,
                "sparse": SparseVector(
                    indices=sparse_vec["indices"],
                    values=sparse_vec["values"],
                ),
            },
            payload=chunk.to_qdrant_payload(),
        )
        for chunk, dense_vec, sparse_vec in zip(chunks, dense_embeddings, sparse_embeddings)
    ]
    if points:
        client.upsert(collection_name=settings.QDRANT_COLLECTION, points=points)


def _dense_search(
    query_embedding: List[float],
    investigation_id: str,
    limit: int,
    min_score: float,
) -> list:
    must_conditions = [
        FieldCondition(key="investigation_id", match=MatchValue(value=investigation_id))
    ]
    return client.search(
        collection_name=settings.QDRANT_COLLECTION,
        query_vector=NamedVector(name="dense", vector=query_embedding),
        query_filter=Filter(must=must_conditions),
        limit=limit,
        score_threshold=min_score,
    )


def _sparse_search(
    query_sparse: dict,
    investigation_id: str,
    limit: int,
) -> list:
    must_conditions = [
        FieldCondition(key="investigation_id", match=MatchValue(value=investigation_id))
    ]
    return client.search(
        collection_name=settings.QDRANT_COLLECTION,
        query_vector=NamedSparseVector(
            name="sparse",
            vector=SparseVector(indices=query_sparse["indices"], values=query_sparse["values"]),
        ),
        query_filter=Filter(must=must_conditions),
        limit=limit,
        # No score_threshold here -- BM25 scores aren't bounded 0-1 like
        # cosine similarity, so a fixed floor doesn't translate. Sparse
        # results are filtered downstream via RRF rank fusion instead.
    )


def search_hybrid(
    dense_query_embedding: List[float],
    sparse_query_embedding: dict,
    investigation_id: str,
    top_k: int = 8,
    max_confidence_tier: Optional[int] = None,
    min_score: float = 0.35,
    rrf_k: int = 60,
) -> List[dict]:
    """
    Hybrid retrieval: runs dense (semantic) and sparse (BM25 keyword)
    search in parallel, merges results with Reciprocal Rank Fusion.

    This is the fix for the article's named dense-retrieval weakness --
    a query like "what was the debt ratio for SKU-4471X" might rank
    poorly on pure semantic similarity but will be caught by the sparse
    side because "SKU-4471X" is a literal token match.

    RRF formula: score(doc) = sum over each ranker of 1 / (rrf_k + rank).
    A doc that ranks well in EITHER list gets a high fused score; a doc
    only mediocre in both still surfaces if it's the best available
    middle ground. rrf_k=60 is the standard default from the original
    RRF paper -- higher values flatten the rank-position effect, lower
    values weight top ranks more heavily.

    Returns chunks with "_score" set to the fused RRF score (not a
    cosine similarity -- don't compare it across calls with different
    rrf_k) and "_dense_score"/"_sparse_score" set when available, so
    callers can see which side of the hybrid search actually found it.
    """
    fetch_limit = top_k * 3  # overfetch on each side before fusing/filtering

    dense_results = _dense_search(dense_query_embedding, investigation_id, fetch_limit, min_score)
    sparse_results = _sparse_search(sparse_query_embedding, investigation_id, fetch_limit)

    # Reciprocal Rank Fusion across the two ranked lists, keyed by point id.
    rrf_scores: dict = defaultdict(float)
    payload_by_id: dict = {}
    dense_score_by_id: dict = {}
    sparse_score_by_id: dict = {}

    for rank, r in enumerate(dense_results):
        rrf_scores[r.id] += 1.0 / (rrf_k + rank + 1)
        payload_by_id[r.id] = r.payload
        dense_score_by_id[r.id] = r.score

    for rank, r in enumerate(sparse_results):
        rrf_scores[r.id] += 1.0 / (rrf_k + rank + 1)
        payload_by_id.setdefault(r.id, r.payload)
        sparse_score_by_id[r.id] = r.score

    fused = sorted(rrf_scores.items(), key=lambda kv: kv[1], reverse=True)

    results = []
    for point_id, fused_score in fused:
        payload = dict(payload_by_id[point_id])
        payload["_score"] = fused_score
        if point_id in dense_score_by_id:
            payload["_dense_score"] = dense_score_by_id[point_id]
        if point_id in sparse_score_by_id:
            payload["_sparse_score"] = sparse_score_by_id[point_id]
        results.append(payload)

    if max_confidence_tier is not None:
        results = [p for p in results if p.get("confidence_tier", 4) <= max_confidence_tier]

    return results[:top_k]


def search_similar(
    query_embedding: List[float],
    investigation_id: str,
    top_k: int = 8,
    max_confidence_tier: Optional[int] = None,
    min_score: float = 0.35,
) -> List[dict]:
    """
    Dense-only search. Kept for callers that only have a dense query
    embedding on hand (e.g. quick relevance checks). Prefer
    search_hybrid() for actual RAG retrieval -- this alone still has
    the dense-retrieval blind spot on exact terms that hybrid fixes.
    """
    results = _dense_search(query_embedding, investigation_id, top_k * 3, min_score)

    payloads = []
    for r in results:
        payload = dict(r.payload)
        payload["_score"] = r.score
        payloads.append(payload)

    if max_confidence_tier is not None:
        payloads = [p for p in payloads if p.get("confidence_tier", 4) <= max_confidence_tier]

    return payloads[:top_k]


def has_sufficient_context(
    dense_query_embedding: List[float],
    sparse_query_embedding: dict,
    investigation_id: str,
    min_results: int = 1,
) -> bool:
    """
    Quick check for "is there even enough relevant material to answer
    this question at all" -- use before generation to decide whether
    to attempt an answer or honestly say "not enough information"
    instead of forcing the model to generate from weak/irrelevant context.
    Uses hybrid search so a query that only matches on exact terms
    (which dense-only would miss) still counts as sufficient context.
    """
    results = search_hybrid(
        dense_query_embedding, sparse_query_embedding, investigation_id, top_k=min_results
    )
    return len(results) >= min_results


def get_all_chunks_for_investigation(investigation_id: str, limit: int = 500) -> List[dict]:
    """Sync implementation. Call get_all_chunks_for_investigation_async()
    from async code (e.g. the REASON-stage /analyze endpoint)."""
    ensure_collection()
    results, _ = client.scroll(
        collection_name=settings.QDRANT_COLLECTION,
        scroll_filter=Filter(must=[
            FieldCondition(key="investigation_id", match=MatchValue(value=investigation_id))
        ]),
        limit=limit,
        with_payload=True,
        with_vectors=False,
    )
    payloads = [r.payload for r in results]
    payloads.sort(key=lambda p: p.get("confidence_tier", 4))
    return payloads


def get_tier_coverage_summary(investigation_id: str) -> dict:
    """
    Structural metadata about what confidence tiers actually have data
    for this investigation -- NOT a contradiction detector (that
    requires semantic comparison, which belongs in the REASON stage's
    prompts). What this DOES tell the caller: whether cross-referencing
    claims against independent signal is even possible for this
    investigation.
    """
    chunks = get_all_chunks_for_investigation(investigation_id)

    tier_counts: dict[int, int] = {}
    tier_sources: dict[int, set] = {}
    for c in chunks:
        tier = c.get("confidence_tier", 4)
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
        tier_sources.setdefault(tier, set()).add(c.get("source_name", "unknown"))

    has_authoritative_or_official = any(t in tier_counts for t in (1, 2))
    has_corroborating_or_signal = any(t in tier_counts for t in (3, 4))

    return {
        "total_chunks": len(chunks),
        "chunk_count_by_tier": tier_counts,
        "sources_by_tier": {t: sorted(s) for t, s in tier_sources.items()},
        "cross_referencing_possible": has_authoritative_or_official and has_corroborating_or_signal,
        "note": (
            "Both company-claimed (tier 1/2) and independent (tier 3/4) data exist -- "
            "cross-referencing for contradictions is meaningful here."
            if has_authoritative_or_official and has_corroborating_or_signal
            else "Only one side of the evidence exists for this investigation "
                 "(either just company-claimed data, or just independent signal). "
                 "Contradiction detection is not possible -- the analysis should "
                 "say so rather than imply a cross-check was performed."
        ),
    }


# --- Async wrappers -- use these from any `async def` code ---

async def store_chunks_async(
    chunks: List["NormalizedChunk"],
    dense_embeddings: List[List[float]],
    sparse_embeddings: List[dict],
) -> None:
    await asyncio.to_thread(store_normalized_chunks, chunks, dense_embeddings, sparse_embeddings)


async def search_hybrid_async(
    dense_query_embedding: List[float],
    sparse_query_embedding: dict,
    investigation_id: str,
    top_k: int = 8,
    max_confidence_tier: Optional[int] = None,
    min_score: float = 0.35,
    rrf_k: int = 60,
) -> List[dict]:
    return await asyncio.to_thread(
        search_hybrid, dense_query_embedding, sparse_query_embedding, investigation_id,
        top_k, max_confidence_tier, min_score, rrf_k,
    )


async def search_similar_async(
    query_embedding: List[float],
    investigation_id: str,
    top_k: int = 8,
    max_confidence_tier: Optional[int] = None,
    min_score: float = 0.35,
) -> List[dict]:
    return await asyncio.to_thread(
        search_similar, query_embedding, investigation_id, top_k, max_confidence_tier, min_score
    )


async def has_sufficient_context_async(
    dense_query_embedding: List[float],
    sparse_query_embedding: dict,
    investigation_id: str,
    min_results: int = 1,
) -> bool:
    return await asyncio.to_thread(
        has_sufficient_context, dense_query_embedding, sparse_query_embedding,
        investigation_id, min_results,
    )


async def get_all_chunks_for_investigation_async(investigation_id: str, limit: int = 500) -> List[dict]:
    return await asyncio.to_thread(get_all_chunks_for_investigation, investigation_id, limit)


async def get_tier_coverage_summary_async(investigation_id: str) -> dict:
    return await asyncio.to_thread(get_tier_coverage_summary, investigation_id)
