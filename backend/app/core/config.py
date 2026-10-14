"""
Core configuration module for ProofLens AI.
Uses pydantic-settings to validate all environment variables at startup.
No secret values or changeable parameters are hardcoded.
"""

from typing import List, Optional
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    APP_ENV: str = Field(default="development", description="Environment mode: development, production, test")
    APP_NAME: str = Field(default="ProofLens AI", description="Application name")
    API_V1_STR: str = Field(default="/api/v1", description="API v1 prefix")
    DEBUG: bool = Field(default=False, description="Debug mode flag")

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3001",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ],
        description="Allowed CORS origins list, environment-configurable",
    )

    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./storage/prooflens.db",
        description="Async database connection string (PostgreSQL or local SQLite)",
    )
    TEST_DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///:memory:",
        description="In-memory SQLite connection string for unit tests",
    )

    # Security & Authentication
    SECRET_KEY: str = Field(
        default="prooflens-insecure-development-secret-key-replace-in-env-32-chars-min",
        description="Secret key used for signing JWT tokens",
    )
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440, description="Token expiration in minutes (default 24h)")

    # Google Gemini AI Provider
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="Google Gemini API key")
    GEMINI_GENERATION_MODEL: str = Field(default="gemini-3.5-flash", description="Generation model name")
    GEMINI_EMBEDDING_MODEL: str = Field(default="gemini-embedding-2", description="Embedding model candidate")
    EMBEDDING_DIMENSION: int = Field(default=768, description="Vector output dimensions (768, 1536, or 3072)")

    # RAG Parameters
    CHUNK_SIZE_TOKENS: int = Field(default=600, description="Chunk target size in tokens")
    CHUNK_OVERLAP_TOKENS: int = Field(default=100, description="Chunk overlap in tokens")
    RETRIEVAL_TOP_K: int = Field(default=5, description="Number of candidate chunks retrieved")
    SIMILARITY_THRESHOLD: float = Field(default=0.35, description="Cosine similarity threshold for abstention")

    # Limits & Storage
    MAX_FILE_SIZE_MB: int = Field(default=15, description="Maximum upload size in MB")
    MAX_DOCUMENTS_PER_WORKSPACE: int = Field(default=10, description="Maximum documents per workspace")
    STORAGE_DIR: str = Field(default="./storage/docs", description="Base directory for document storage")

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        """Enforces that production deployment fails safely if using insecure development secrets."""
        if self.APP_ENV == "production":
            insecure_signatures = ["insecure", "default", "replace-in-env", "secret-key", "demo"]
            if any(sig in self.SECRET_KEY.lower() for sig in insecure_signatures) or len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "CRITICAL SECURITY CONFIGURATION ERROR: Production mode requires a cryptographically secure, "
                    "non-default SECRET_KEY of at least 32 characters configured via environment variable."
                )
        return self


settings = Settings()
