import truststore
truststore.inject_into_ssl()
# Must run before any other import that might create an httpx/SSL client
# (e.g. qdrant_service.py's module-level QdrantClient). Uses the OS's own
# certificate store instead of the static certifi bundle -- some sites
# (confirmed: Bangladesh's DSE, CSE stock exchanges) serve an incomplete
# cert chain that certifi can't complete but the OS trust store can
# (via AIA chasing), without disabling verification.

import asyncio
import gc
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text
from app.core.config import settings
from app.core.database import Base, engine
from app.api.v1.router import api_router
import app.models  # noqa: F401 -- registers all tables on Base.metadata

logger = logging.getLogger(__name__)

app = FastAPI(title="AI Due Diligence Copilot", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


def _add_missing_columns(sync_conn):
    """
    No Alembic migrations exist yet. create_all() only creates tables
    that don't exist at all -- it never adds columns to a table that's
    already there (e.g. the Investigation/Risk/Financial tables already
    created against a real cloud Postgres in earlier testing). This
    diffs each model's columns against what's actually in the DB and
    issues ADD COLUMN for anything missing, so schema changes here
    don't require a manual migration or a destructive drop/recreate.
    """
    inspector = inspect(sync_conn)
    existing_tables = set(inspector.get_table_names())
    for table in Base.metadata.sorted_tables:
        if table.name not in existing_tables:
            continue
        existing_cols = {col["name"] for col in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name in existing_cols:
                continue
            col_type = column.type.compile(dialect=sync_conn.dialect)
            sync_conn.execute(
                text(f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {col_type}')
            )
            logger.info("Added missing column %s.%s", table.name, column.name)


def _preload_rag_models():
    """
    Loads the dense/sparse embedding models once, at boot, instead of
    lazily on the first request that needs them (upload's NORMALIZE
    stage, or chat). If the instance's memory is too tight for these,
    it fails loudly at deploy time instead of crashing mid-request for
    whichever user happens to trigger it first.

    The reranker (chat_service/comparison_chat_service's cross-encoder)
    is deliberately NOT preloaded here -- on Render's 512MB free tier,
    eagerly loading all three ONNX models at once left too little
    headroom and caused boot-time OOM kills. It stays lazily loaded on
    first chat use instead, same as before this preload step existed.

    gemini_service is ALSO deliberately not preloaded, despite an
    earlier attempt to do so here -- reverted. `from google import
    genai` pulls in grpcio/protobuf/google-auth/cryptography (~346
    modules), and preloading it raised the permanent baseline enough
    that GATHER -- which runs unconditionally on every single upload --
    started failing far more often than the conditional, less-frequent
    Gemini-fallback crash it was meant to fix. GATHER's memory need
    matters more since it's on every request path, not just the ones
    where Groq's quota gets exhausted. Stays lazy; see groq_service.py.

    gc.collect() after loading drops the transient download buffers
    that huggingface_hub/onnxruntime allocate while unpacking model
    files, which otherwise linger as peak (not steady-state) memory.
    """
    from app.services.embedding_service import get_model, get_sparse_model
    from app.core.memory_debug import log_memory

    get_model()
    get_sparse_model()
    gc.collect()
    logger.info("RAG embedding models (dense, sparse) preloaded at startup")
    log_memory("baseline after startup preload")


@app.on_event("startup")
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_add_missing_columns)
    await asyncio.to_thread(_preload_rag_models)


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0", "env": settings.APP_ENV}
