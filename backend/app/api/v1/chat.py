"""
TEAMMATE SCOPE -- RAG chat endpoint.

Full retrieval pipeline now available (gather/normalize side is done):

  1. Embed the question, BOTH ways:
     - app.services.embedding_service.generate_query_embedding_async(question)
     - app.services.embedding_service.generate_sparse_query_embedding_async(question)

  2. Hybrid retrieve (dense + sparse merged via RRF -- fixes the
     "dense search misses exact terms" problem for product codes,
     specific figures, proper nouns):
     - app.services.qdrant_service.search_hybrid_async(dense_emb, sparse_emb, investigation_id, top_k=20)

  3. Rerank the hybrid candidates down to the best few for the prompt
     (precision pass, cross-encoder reads query+doc together):
     - app.services.reranking_service.rerank_chunks_async(question, hybrid_results, top_n=6)

  4. Before generating, check there's actually enough to answer from:
     - app.services.qdrant_service.has_sufficient_context_async(dense_emb, sparse_emb, investigation_id)
     If False, return an honest "not enough information" answer instead
     of forcing a response from weak/irrelevant context.

  5. Build the RAG prompt from the reranked chunks, call Groq.

Every returned chunk carries confidence_tier/source_name/origin_url
plus _score (RRF)/_dense_score/_sparse_score/_rerank_score, so chat
answers can cite real sources and you can debug retrieval quality if
answers look off.
"""
from fastapi import APIRouter
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # TODO (teammate): see pipeline above -- embed (dense+sparse) ->
    # search_hybrid_async -> rerank_chunks_async -> build prompt -> call Groq.
    return ChatResponse(answer="Not implemented yet", sources=[])
