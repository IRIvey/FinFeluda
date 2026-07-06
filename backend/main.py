from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine
from app.api.v1.router import api_router
import app.models  # noqa: F401 -- registers all tables on Base.metadata

app = FastAPI(title="AI Due Diligence Copilot", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
async def create_tables():
    # No Alembic migrations exist yet for this project -- create_all is
    # idempotent (checkfirst) and enough to get a hackathon demo running
    # against a fresh Postgres instance.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0", "env": settings.APP_ENV}
