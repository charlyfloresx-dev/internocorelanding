from functools import lru_cache
from typing import Optional
from pydantic import Field, AliasChoices
from pydantic_settings import SettingsConfigDict
from common.config import InternoSettings

class ViatraSettings(InternoSettings):
    """
    Configuración para Viatra Service (Integración con transportistas y logística).
    Hereda de InternoSettings para asegurar consistencia en AWS y carga de secretos.
    """
    PROJECT_NAME: str = "InternoCore Viatra Service"

    # STRIPE (Pagos de fletes)
    STRIPE_SECRET_KEY: str = Field(default="", validation_alias=AliasChoices("CORE_STRIPE_KEY", "STRIPE_SECRET_KEY"))
    STRIPE_WEBHOOK_SECRET: str = Field(default="", validation_alias=AliasChoices("CORE_STRIPE_WEBHOOK", "STRIPE_WEBHOOK_SECRET"))

    # AWS S3 (Documentación de transporte)
    AWS_S3_BUCKET: str = Field(default="viatra-documents", validation_alias=AliasChoices("CORE_AWS_S3_BUCKET", "AWS_S3_BUCKET"))
    AWS_REGION: str = Field(default="us-east-1", validation_alias=AliasChoices("CORE_AWS_REGION", "AWS_REGION"))

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=True
    )

settings = ViatraSettings()
settings.load_aws_secrets()

@lru_cache()
def get_settings():
    return settings
