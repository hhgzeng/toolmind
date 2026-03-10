from fastapi import APIRouter
from toolmind.api.v1 import (
    llm,
    mcp_server,
    mind,
    model_config,
    session,
    usage_stats,
    user,
    web_search,
)

router = APIRouter(prefix="/api/v1")

router.include_router(user.router)
router.include_router(llm.router)
router.include_router(mcp_server.router)
router.include_router(session.router)
router.include_router(mind.router)
router.include_router(usage_stats.router)
router.include_router(model_config.router)
router.include_router(web_search.router)