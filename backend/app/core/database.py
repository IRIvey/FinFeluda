"""
Async SQLAlchemy setup using asyncpg (Supabase/Neon) in production.

Falls back to a local SQLite file when DATABASE_URL is still the
`.env.example` placeholder, so the app can run end-to-end for local
dev/demo without a cloud Postgres instance provisioned first. Put a
real DATABASE_URL in backend/.env for anything beyond local testing --
the project spec calls for cloud Postgres, not this fallback.
"""
import logging
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

logger = logging.getLogger(__name__)

_PLACEHOLDER_URL = "postgresql+asyncpg://user:password@host:5432/dbname"
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


def _to_asyncpg_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


_resolved_url = _to_asyncpg_url(settings.DATABASE_URL)

if _resolved_url == _PLACEHOLDER_URL:
    logger.warning(
        "DATABASE_URL is still the .env.example placeholder -- falling back "
        "to a local SQLite file (backend/dev.db) for this run. Set a real "
        "Postgres URL in backend/.env before deploying."
    )
    engine = create_async_engine(f"sqlite+aiosqlite:///{_BACKEND_DIR / 'dev.db'}")
else:
    # Supabase's pooled connection string (port 6543, PgBouncer in
    # transaction mode) doesn't support asyncpg's server-side prepared
    # statement cache -- reusing a statement name across pooled backend
    # connections raises DuplicatePreparedStatementError. Disabling the
    # cache (statement_cache_size=0) is the documented fix and is a
    # no-op for direct (non-pooled) Postgres connections too.
    engine = create_async_engine(
        _resolved_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
        connect_args={"statement_cache_size": 0},
    )

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()