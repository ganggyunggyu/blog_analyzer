"""봇 헬스체크"""

from fastapi import APIRouter

from .common import get_manuscript_list

router = APIRouter()


@router.get("/health")
async def health():
    """헬스 체크"""
    return {
        "status": "ok",
        "service": "bot-orchestrator",
        "queue": {
            "pending": len(get_manuscript_list("pending")),
            "completed": len(get_manuscript_list("completed")),
            "failed": len(get_manuscript_list("failed")),
        }
    }
