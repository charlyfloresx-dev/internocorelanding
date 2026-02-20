from fastapi import APIRouter
from .endpoints import users, companies, auth

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(companies.router, prefix="/companies", tags=["Companies"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])