from pydantic import Field, AliasChoices
from pydantic_settings import SettingsConfigDict
from common.config import InternoSettings
from typing import Optional

class MasterDataSettings(InternoSettings):
    """
    Configuración escalable para Master Data Service.
    Hereda de InternoSettings para asegurar consistencia en AWS y carga de secretos.
    """
    PROJECT_NAME: str = "InternoCore Master Data Service"
    API_V1_STR: str = "/api/v1"

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore"
    )

settings = MasterDataSettings()
settings.load_aws_secrets()
