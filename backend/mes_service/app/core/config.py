from pydantic import Field, AliasChoices
from pydantic_settings import SettingsConfigDict
from common.config import InternoSettings
from typing import Optional

class MESSettings(InternoSettings):
    """
    Configuración para Manufacturing Execution System (MES).
    Hereda del núcleo central para asegurar consistencia en AWS.
    """
    PROJECT_NAME: str = "InternoCore MES Service"
    API_V1_STR: str = "/api/v1"
    
    # Database (Prioridad a la URL ya construida)
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://user:password@db:5432/mes_db",
        validation_alias=AliasChoices("CORE_DATABASE_URL", "DATABASE_URL")
    )
    
    SECRET_KEY: str = Field(
        default="placeholder_security_key",
        validation_alias=AliasChoices("CORE_SECRET_KEY", "SECRET_KEY")
    )

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        if self.DATABASE_URL.startswith("postgresql://"):
            return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self.DATABASE_URL

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=True
    )

settings = MESSettings()
settings.load_aws_secrets()
