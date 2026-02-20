from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Interno WMS"
    API_V1_STR: str = "/api/v1"
    ENV_MODE: str = "local"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    
    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    
    # Security & Auth (Replicado de Auth-Service para validación de tokens)
    SECRET_KEY: str = "changeme"
    ALGORITHM: str = "HS256"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

settings = Settings()