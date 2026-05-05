from typing import Optional
from pydantic import Field, AliasChoices
from pydantic_settings import SettingsConfigDict
from common.config import InternoSettings

class WMSSettings(InternoSettings):
    """
    Configuración para Warehouse Management System (WMS).
    Maneja inventario físico, picking y packing.
    Hereda de InternoSettings para asegurar consistencia en AWS y carga de secretos.
    """
    PROJECT_NAME: str = "InternoCore WMS Service"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=True
    )

settings = WMSSettings()
settings.load_aws_secrets()