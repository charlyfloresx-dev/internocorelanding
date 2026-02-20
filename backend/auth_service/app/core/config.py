import os
import json
import boto3
from botocore.exceptions import ClientError
from pydantic_settings import BaseSettings
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator

def get_aws_secrets(secret_id: str, region: str):
    """
    Intenta obtener secretos de AWS. 
    Si no hay región o falla la conexión, retorna un dict vacío 
    para que el sistema use las variables de entorno locales (Modo On-Premise).
    """
    if not region or region.strip() == "":
        return {}
    
    try:
        session = boto3.session.Session()
        client = session.client(service_name='secretsmanager', region_name=region)
        response = client.get_secret_value(SecretId=secret_id)
        return json.loads(response['SecretString'])
    except Exception as e:
        print(f"⚠️ AWS Secrets Manager no disponible (usando config local): {e}")
        return {}

class Settings(BaseSettings):
    PROJECT_NAME: str = "InternoCore Auth-Service"
    API_V1_STR: str = "/api/v1"

    ENV_MODE: str = os.getenv("ENV_MODE", "local") # Add ENV_MODE

    # --- Configuración de AWS ---
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-2") # Default to user specified region
    AWS_SECRET_ID: str = os.getenv("AWS_SECRET_ID", "nexosuite/auth-service/db") # Default to user specified secret

    _aws = {}
    if ENV_MODE == "aws": # Conditional AWS secrets loading
        _aws = get_aws_secrets(AWS_SECRET_ID, AWS_REGION)

    # --- Variables Críticas (Prioridad: AWS -> Env Var -> Default) ---
    DATABASE_URL: str = _aws.get("DATABASE_URL") or os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://user:password@localhost:5433/auth_db"
    )

    SECRET_KEY: str = _aws.get("SECRET_KEY") or os.getenv(
        "SECRET_KEY",
        "DEV_SECRET_KEY_CAMBIAME_EN_PROD_12345"
    )

    # --- JWT Configuration ---
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(_aws.get("ACCESS_TOKEN_EXPIRE_MINUTES") or os.getenv(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "60" # Default to 60 minutes
    ))
    SELECTION_TOKEN_EXPIRE_MINUTES: int = int(_aws.get("SELECTION_TOKEN_EXPIRE_MINUTES") or os.getenv(
        "SELECTION_TOKEN_EXPIRE_MINUTES",
        "5" # Default to 5 minutes for selection token
    ))
    ALGORITHM: str = _aws.get("ALGORITHM") or os.getenv(
        "ALGORITHM",
        "HS256"
    )

    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # --- CORS ---
    # Esto soluciona el AttributeError que vimos en el log de Docker
    BACKEND_CORS_ORIGINS: List[str] = ["*"] 

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        # 1. Start with explicit origins
        origins = []
        
        if isinstance(v, str) and not v.startswith("["):
            origins = [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
             origins = v if isinstance(v, list) else []

        # 2. Dynamic AWS/CloudFront Injection
        # If FRONTEND_URL env var exists (e.g. from AWS App Runner), add it automatically
        frontend_url = os.getenv("FRONTEND_URL")
        if frontend_url:
            print(f"🌍 Injecting dynamic CORS origin: {frontend_url}")
            if frontend_url not in origins:
                origins.append(frontend_url)
        
        return origins

    # --- Configuración de Base de Datos ---
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    class Config:
        case_sensitive = True
        env_file = ".env" # Opcional: lee de un archivo .env si existe

settings = Settings()