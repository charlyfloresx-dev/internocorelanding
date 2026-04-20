from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from common.config import settings

def setup_cors(app: FastAPI):
    """
    Standardizes CORS configuration across all microservices using Global Settings.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.int_backend_cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=settings.int_cors_allowed_headers,
        expose_headers=settings.int_cors_exposed_headers,
    )
