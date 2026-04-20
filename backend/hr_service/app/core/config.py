from pydantic import Field, AliasChoices
from pydantic_settings import SettingsConfigDict
from common.config import InternoSettings
from typing import Optional

class HRSettings(InternoSettings):
    """
    Configuración escalable para HR Service.
    Hereda de InternoSettings para asegurar consistencia en AWS y carga de secretos.
    """
    PROJECT_NAME: str = "InternoCore HR Service"
    API_V1_STR: str = "/api/v1"

    # [Phase 50] Cross-border eligibility grace period in days.
    CROSS_BORDER_EXPIRY_THRESHOLD_DAYS: int = Field(
        default=15,
        validation_alias=AliasChoices("CORE_HR_EXPIRY_THRESHOLD_DAYS", "CROSS_BORDER_EXPIRY_THRESHOLD_DAYS")
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=True
    )

settings = HRSettings()
settings.load_aws_secrets()
