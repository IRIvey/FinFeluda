from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    # --- App ---
    APP_ENV: str = "development"
    CORS_ORIGINS: str = "http://localhost:5173"

    # --- Database ---
    DATABASE_URL: str

    # --- Groq ---
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # --- Qdrant ---
    QDRANT_URL: str
    QDRANT_API_KEY: str
    QDRANT_COLLECTION: str = "due_diligence"

    # --- Embeddings ---
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"

    # --- Cloudinary ---
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    # --- Optional public-source API keys -- each fetcher degrades
    # gracefully (skips itself) if its key is missing. ---
    GITHUB_TOKEN: Optional[str] = None
    REDDIT_CLIENT_ID: Optional[str] = None
    REDDIT_CLIENT_SECRET: Optional[str] = None
    NEWS_API_KEY: Optional[str] = None
    GOOGLE_MAPS_API_KEY: Optional[str] = None
    YOUTUBE_API_KEY: Optional[str] = None
    SERPER_API_KEY: Optional[str] = None  # Google Search via serper.dev free tier

    class Config:
        env_file = ".env"

    @property
    def allowed_origins(self) -> List[str]:
        """CORS_ORIGINS in .env is a comma-separated string -- split it here
        rather than asking pydantic-settings to parse a List[str] from env,
        which requires JSON-array syntax and trips people up."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
