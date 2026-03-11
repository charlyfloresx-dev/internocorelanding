from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, seed, companies, health, admin

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(companies.router, prefix="/companies", tags=["Companies"])
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(seed.router, prefix="/seed", tags=["Seed"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin (God Mode)"])