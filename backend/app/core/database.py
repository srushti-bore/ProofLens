"""
Asynchronous database setup for ProofLens AI using SQLAlchemy 2.0.
"""

import re
from typing import Any, AsyncGenerator, Dict
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from backend.app.core.config import settings


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy database models."""
    pass


def normalize_async_database_url(url: str) -> str:
    """
    Ensure the database URL is compatible with SQLAlchemy's async engine and asyncpg.
    - Converts postgres:// or postgresql:// to postgresql+asyncpg://
    - Translates sslmode=require to ssl=require (asyncpg parameter)
    """
    if not url:
        return url

    # 1. Normalize scheme for asyncpg
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # 2. Fix asyncpg sslmode incompatibility: asyncpg expects 'ssl' rather than 'sslmode'
    if "sslmode=require" in url:
        url = url.replace("sslmode=require", "ssl=require")
    elif "sslmode=disable" in url:
        url = url.replace("sslmode=disable", "")

    # Clean any trailing '?' or '&' from replacements
    url = re.sub(r"[?&]$", "", url)
    return url


# Normalize connection URL
ASYNC_DATABASE_URL = normalize_async_database_url(settings.DATABASE_URL)

# Configure engine kwargs based on dialect
engine_kwargs: Dict[str, Any] = {
    "echo": settings.DEBUG,
    "future": True,
}

if "postgresql" in ASYNC_DATABASE_URL:
    engine_kwargs.update({
        "pool_pre_ping": True,  # Critical for Supabase pooler connection resets
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 300,    # Recycle connections every 5 minutes to prevent stale sockets
    })

# Global async engine
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    **engine_kwargs,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for providing a transactional async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
