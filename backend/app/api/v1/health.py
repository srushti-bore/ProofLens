"""
Health check and status API routes.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.schemas.health import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def check_health(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """
    Service health check endpoint.
    Verifies API readiness, environment info, and database connectivity.
    """
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"

    return HealthResponse(
        status="ok" if db_status == "connected" else "degraded",
        app_name=settings.APP_NAME,
        environment=settings.APP_ENV,
        version="0.2.0",
        database=db_status,
    )
