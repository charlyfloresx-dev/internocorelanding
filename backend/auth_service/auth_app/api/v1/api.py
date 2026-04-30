from fastapi import APIRouter
from auth_app.api.v1.endpoints import auth, users, seed, companies, health, admin, collaborator_auth, social_login, biometric

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(collaborator_auth.router, prefix="/auth", tags=["Auth — Kiosk"])
api_router.include_router(social_login.router, prefix="/auth", tags=["Auth — Social"])
api_router.include_router(biometric.router, prefix="/biometric", tags=["Auth — Biometric (WebAuthn)"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(companies.router, prefix="/companies", tags=["Companies"])
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(seed.router, prefix="/seed", tags=["Seed"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin (God Mode)"])
