"""
API v1 root router aggregating all resource sub-routers.
"""

from fastapi import APIRouter

from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.claims import router as claims_router
from backend.app.api.v1.conversations import router as conversations_router
from backend.app.api.v1.documents import router as documents_router
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.history import router as history_router
from backend.app.api.v1.qa import router as qa_router
from backend.app.api.v1.retrieval import router as retrieval_router
from backend.app.api.v1.workspaces import router as workspaces_router

api_v1_router = APIRouter()

api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(workspaces_router)
api_v1_router.include_router(documents_router)
api_v1_router.include_router(retrieval_router)
api_v1_router.include_router(qa_router)
api_v1_router.include_router(conversations_router)
api_v1_router.include_router(claims_router)
api_v1_router.include_router(history_router)
