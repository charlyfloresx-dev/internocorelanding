import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "InternoCore Subscription-Service"
    API_V1_STR: str = "/api/v1"
    
    # --- Configuración de Base de Datos ---
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://user:password@localhost:5433/subscription_db"
    )
    
    # --- CORS ---
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
