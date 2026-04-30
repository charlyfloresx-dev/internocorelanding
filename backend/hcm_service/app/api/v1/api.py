from fastapi import APIRouter
from app.api.v1.endpoints import internal, collaborators

api_router = APIRouter()
api_router.include_router(internal.router, prefix="/internal/collaborators", tags=["Internal — Collaborators"])
api_router.include_router(collaborators.router, prefix="/staff", tags=["Staff Management"])
