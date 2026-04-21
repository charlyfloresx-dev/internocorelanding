from fastapi import APIRouter
from auth_app.api.v2.endpoints import admin, public

api_router = APIRouter()
api_router.include_router(admin.router, prefix="/admin", tags=["admin-v2"])
api_router.include_router(public.router, prefix="/public", tags=["public-v2"])
