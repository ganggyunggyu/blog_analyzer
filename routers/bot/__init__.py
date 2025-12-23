"""봇 라우터 통합"""

from fastapi import APIRouter

from .auto import router as auto_router
from .publish import router as publish_router
from .start import router as start_router
from .manuscript import router as manuscript_router
from .health import router as health_router

# 통합 라우터
router = APIRouter(prefix="/bot", tags=["bot-orchestrator"])

router.include_router(auto_router)
router.include_router(publish_router)
router.include_router(start_router)
router.include_router(manuscript_router)
router.include_router(health_router)
