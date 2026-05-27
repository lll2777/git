from fastapi import APIRouter

from app.api.v1.routes.ai import router as ai_router
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.charts import router as charts_router
from app.api.v1.routes.datasets import router as datasets_router
from app.api.v1.routes.health import router as health_router

api_router = APIRouter()
api_router.include_router(auth_router, tags=["auth"])
api_router.include_router(ai_router, tags=["ai"])
api_router.include_router(charts_router, tags=["charts"])
api_router.include_router(datasets_router, tags=["datasets"])
api_router.include_router(health_router, tags=["health"])
