from fastapi import APIRouter
from asset_app.api.v1.endpoints.opportunities import router as opportunities_router

api_router = APIRouter()

api_router.include_router(
    opportunities_router,
    prefix="/opportunities",
    tags=["Asset Opportunities — CRM Kanban"],
)
