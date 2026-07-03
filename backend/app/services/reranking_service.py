"""
Reranking -- the article's "fast rough retriever, then slow precise
reranker" two-stage pattern.

Hybrid search (search_hybrid in qdrant_service.py) is the fast, rough
first pass: it's good at narrowing millions of chunks down to a
double-digit candidate set quickly, using RRF-fused dense+sparse
scores. But RRF rank fusion is itself approximate -- it never actually
reads the query against each candidate's full text together.

A cross-encoder reranker does: it takes the (query, candidate_text)
PAIR and scores how relevant that specific candidate actually is to
that specific query, which is far more precise than comparing
independently-computed embeddings, but too slow to run over a whole
collection. The division of labor: hybrid search narrows millions of
chunks to ~20-30 candidates cheaply, the reranker does a careful
pass over just those ~20-30 to pick the best ~5-8 for the prompt.

Uses fastembed's bundled cross-encoder (same ONNX/no-torch story as
the rest of this app's embedding stack -- no new dependency class).
"""
import asyncio
import logging
from fastembed.rerank.cross_encoder import TextCrossEncoder
from typing import List

logger = logging.getLogger(__name__)

_reranker: TextCrossEncoder | None = None

RERANKER_MODEL_NAME = "Xenova/ms-marco-MiniLM-L-6-v2"  # small, fast, good default cross-encoder


def get_reranker() -> TextCrossEncoder:
    global _reranker
    if _reranker is None:
        _reranker = TextCrossEncoder(model_name=RERANKER_MODEL_NAME)
    return _reranker


def rerank_chunks(query: str, candidates: List[dict], top_n: int = 6) -> List[dict]:
    """
    Sync implementation. Call rerank_chunks_async() from async code.

    candidates: list of chunk payload dicts (as returned by
    qdrant_service.search_hybrid()), each must have a "text" key.

    Returns the top_n candidates re-sorted by the cross-encoder's
    relevance score, with payload["_rerank_score"] attached. This
    score is NOT comparable to "_score" (RRF) or "_dense_score" /
    "_sparse_score" -- it's a separate, more precise judgment and
    should be the one actually trusted for final ordering.

    If candidates is empty, returns empty -- doesn't fabricate results.
    """
    if not candidates:
        return []

    model = get_reranker()
    texts = [c.get("text", "") for c in candidates]

    scores = list(model.rerank(query, texts))

    scored = list(zip(candidates, scores))
    scored.sort(key=lambda pair: pair[1], reverse=True)

    results = []
    for candidate, score in scored[:top_n]:
        enriched = dict(candidate)
        enriched["_rerank_score"] = float(score)
        results.append(enriched)

    return results


async def rerank_chunks_async(query: str, candidates: List[dict], top_n: int = 6) -> List[dict]:
    return await asyncio.to_thread(rerank_chunks, query, candidates, top_n)
