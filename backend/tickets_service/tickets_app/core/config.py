from typing import Optional
from pydantic import Field, AliasChoices
from pydantic_settings import SettingsConfigDict
from common.config import InternoSettings

class TicketsSettings(InternoSettings):
    """
    Configuración para Tickets Service.
    Gestiona el sistema de soporte y tickets internos.
    Hereda de InternoSettings para asegurar consistencia en AWS y carga de secretos.
    """
    PROJECT_NAME: str = "InternoCore Tickets Service"
    CORE_EXTERNAL_TOKEN_SECRET: str = "DEV_DEFAULT_INDUSTRIAL_SECRET_2026"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=True
    )

settings = TicketsSettings()
settings.load_aws_secrets()
