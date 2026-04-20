from typing import Optional
from pydantic import Field, AliasChoices
from pydantic_settings import SettingsConfigDict
from common.config import InternoSettings

class NotificationSettings(InternoSettings):
    """
    Configuración para Notification Service.
    Soporta múltiples proveedores de mensajería (Email, WhatsApp, Push).
    Hereda de InternoSettings para asegurar consistencia en AWS y carga de secretos.
    """
    PROJECT_NAME: str = "InternoCore Notification Service"

    # SMTP / EMAIL CONFIG
    SMTP_HOST: str = Field(default="smtp.gmail.com", validation_alias=AliasChoices("CORE_SMTP_HOST", "SMTP_HOST"))
    SMTP_PORT: int = Field(default=587, validation_alias=AliasChoices("CORE_SMTP_PORT", "SMTP_PORT"))
    SMTP_USER: Optional[str] = Field(default=None, validation_alias=AliasChoices("CORE_SMTP_USER", "SMTP_USER"))
    SMTP_PASSWORD: Optional[str] = Field(default=None, validation_alias=AliasChoices("CORE_SMTP_PASSWORD", "SMTP_PASSWORD"))

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=True
    )

settings = NotificationSettings()
settings.load_aws_secrets()
