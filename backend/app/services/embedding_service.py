"""
Embedding generation via fastembed (ONNX runtime, no torch -- light
enough for free-tier deploys). Two embedding types are produced:

DENSE (TextEmbedding, bge-small-en-v1.5): captures semantic meaning,
good at synonyms/paraphrasing, weak at exact matches on product
codes, proper nouns, specific figures (this is the dense-retrieval
weakness the article calls out explicitly).

SPARSE (SparseTextEmbedding, BM25): classic keyword-weighted matching,
strong on exact terms, weak on paraphrasing. Combining both (hybrid
retrieval) covers each other's blind spots -- this is what
qdrant_service.py's hybrid search actually merges at query time.

IMPORTANT for the team: this exact dense model/function must also be
used by whoever builds /chat (RAG retrieval), so a user's question is
embedded into the same vector space as the stored chunks. Don't let
anyone re-embed with a different model.

Both fastembed model types run inference synchronously and are
CPU-bound, so calling them directly from async code blocks the event
loop. Use the async wrappers below from any `async def`.
"""
import asyncio
from fastembed import TextEmbedding, SparseTextEmbedding
from fastembed.sparse.sparse_embedding_base import SparseEmbedding
from typing import List
from app.core.config import settings

_dense_model: TextEmbedding | None = None
_sparse_model: SparseTextEmbedding | None = None

SPARSE_MODEL_NAME = "Qdrant/bm25"


def get_model() -> TextEmbedding:
    global _dense_model
    if _dense_model is None:
        # threads=1 + CPU-only provider: keeps onnxruntime's per-session
        # memory arena small, which matters on memory-capped free-tier
        # deploys (Render's 512MB) running dense+sparse+reranker models
        # in the same process.
        _dense_model = TextEmbedding(
            model_name=settings.EMBEDDING_MODEL, threads=1, providers=["CPUExecutionProvider"]
        )
    return _dense_model


def get_sparse_model() -> SparseTextEmbedding:
    global _sparse_model
    if _sparse_model is None:
        _sparse_model = SparseTextEmbedding(
            model_name=SPARSE_MODEL_NAME, threads=1, providers=["CPUExecutionProvider"]
        )
    return _sparse_model


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Sync dense embedding. Call generate_embeddings_async() from async code."""
    model = get_model()
    return [vec.tolist() for vec in model.embed(texts)]


def generate_query_embedding(query: str) -> List[float]:
    """Sync single-text dense embedding. Call generate_query_embedding_async()
    from async code."""
    return generate_embeddings([query])[0]


def generate_sparse_embeddings(texts: List[str]) -> List[dict]:
    """
    Sync sparse (BM25) embedding. Returns a list of {"indices": [...],
    "values": [...]} dicts -- the format Qdrant's SparseVector expects.
    Call generate_sparse_embeddings_async() from async code.
    """
    model = get_sparse_model()
    results: List[SparseEmbedding] = list(model.embed(texts))
    return [
        {"indices": r.indices.tolist(), "values": r.values.tolist()}
        for r in results
    ]


def generate_sparse_query_embedding(query: str) -> dict:
    """Sync single-text sparse embedding. Call generate_sparse_query_embedding_async()
    from async code."""
    return generate_sparse_embeddings([query])[0]


# --- Async wrappers -- use these from any `async def` code ---

async def generate_embeddings_async(texts: List[str]) -> List[List[float]]:
    return await asyncio.to_thread(generate_embeddings, texts)


async def generate_query_embedding_async(query: str) -> List[float]:
    return await asyncio.to_thread(generate_query_embedding, query)


async def generate_sparse_embeddings_async(texts: List[str]) -> List[dict]:
    return await asyncio.to_thread(generate_sparse_embeddings, texts)


async def generate_sparse_query_embedding_async(query: str) -> dict:
    return await asyncio.to_thread(generate_sparse_query_embedding, query)
