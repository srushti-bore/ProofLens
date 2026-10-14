"""
Main FastAPI application entrypoint for ProofLens AI.
Configures middleware, routers, lifespan hooks, and error handling.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.v1.router import api_v1_router
from backend.app.core.config import settings
from backend.app.core.database import Base, engine
import backend.app.models  # noqa: F401 - Register all models for metadata.create_all


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown events."""
    # Ensure local storage directory exists only when using local storage
    if settings.STORAGE_BACKEND == "local":
        os.makedirs(settings.STORAGE_DIR, exist_ok=True)
    
    # In development/test mode, create tables if they don't exist
    async with engine.begin() as conn:
        if engine.dialect.name == "postgresql":
            from sqlalchemy import text
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        if settings.APP_ENV != "production":
            await conn.run_sync(Base.metadata.create_all)
            try:
                from sqlalchemy import text
                await conn.execute(text("ALTER TABLE query_runs ADD COLUMN conversation_id VARCHAR(36) REFERENCES conversations(id) ON DELETE CASCADE;"))
            except Exception:
                pass
        
    yield
    
    # Clean shutdown
    await engine.dispose()


def create_application() -> FastAPI:
    """Application factory for ProofLens AI."""
    app = FastAPI(
        title=settings.APP_NAME,
        description="Evidence-first document intelligence platform — From documents to verifiable answers.",
        version="0.2.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG or settings.APP_ENV != "production" else None,
        docs_url=f"{settings.API_V1_STR}/docs" if settings.DEBUG or settings.APP_ENV != "production" else None,
        redoc_url=f"{settings.API_V1_STR}/redoc" if settings.DEBUG or settings.APP_ENV != "production" else None,
        lifespan=lifespan,
    )

    # CORS configuration - environment configurable with safe dev defaults
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global safe exception handler: never leak raw stack traces to client
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        # In debug mode allow normal error details, in non-debug return generic safe error
        if settings.DEBUG:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": str(exc)},
            )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal server error occurred. Please contact support."},
        )

    # Root health endpoints for cloud load balancers and deployment monitors (Render/Fly/K8s)
    @app.get("/health", tags=["Health"], include_in_schema=False)
    async def root_health():
        return {
            "status": "ok",
            "app": settings.APP_NAME,
            "environment": settings.APP_ENV,
            "version": "0.2.0",
        }

    @app.get("/", tags=["Health"], include_in_schema=False)
    async def root_index():
        return {
            "status": "ok",
            "app": settings.APP_NAME,
            "version": "0.2.0",
            "docs": f"{settings.API_V1_STR}/docs" if settings.DEBUG or settings.APP_ENV != "production" else None,
        }

    # Include API routers
    app.include_router(api_v1_router, prefix=settings.API_V1_STR)

    return app


app = create_application()
