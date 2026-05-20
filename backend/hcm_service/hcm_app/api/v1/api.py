from fastapi import APIRouter
from hcm_app.api.v1.endpoints import internal, collaborators, departments

api_router = APIRouter()
api_router.include_router(internal.router, prefix="/internal/collaborators", tags=["Internal — Collaborators"])
api_router.include_router(collaborators.router, prefix="/staff", tags=["Staff Management"])
api_router.include_router(departments.router, prefix="/hcm/departments", tags=["Departments Management"])
