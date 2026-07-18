from fastapi import APIRouter
from app.api.v1.endpoints import auth, predict, history, food_log, food_catalog

api_router = APIRouter()

# Include endpoint sub-routers under appropriate route paths
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(predict.router, prefix="/predict", tags=["predict"])
api_router.include_router(history.router, prefix="/history", tags=["history"])
api_router.include_router(food_log.router, prefix="/food-log", tags=["food-log"])
api_router.include_router(food_catalog.router, prefix="/food-catalog", tags=["food-catalog"])
