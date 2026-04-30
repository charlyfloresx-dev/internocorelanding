from typing import Optional
from pydantic import Field
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
    SMTP_HOST: str = Field(default="smtp.gmail.com", validation_alias="CORE_SMTP_HOST")
    SMTP_PORT: int = Field(default=587, validation_alias="CORE_SMTP_PORT")
    SMTP_USER: Optional[str] = Field(default=None, validation_alias="CORE_SMTP_USER")
    SMTP_PASSWORD: Optional[str] = Field(default=None, validation_alias="CORE_SMTP_PASSWORD")

    # WHATSAPP BUSINESS API (TWILIO) CONFIG
    TWILIO_ACCOUNT_SID: Optional[str] = Field(default=None, validation_alias="CORE_TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: Optional[str] = Field(default=None, validation_alias="CORE_TWILIO_AUTH_TOKEN")
    WHATSAPP_SENDER_NUMBER: str = Field(default="whatsapp:+14155238886", validation_alias="CORE_WHATSAPP_SENDER_NUMBER")
    WHATSAPP_BASE_URL: str = Field(default="https://api.twilio.com/2010-04-01/Accounts", validation_alias="CORE_WHATSAPP_BASE_URL")

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=True
    )

settings = NotificationSettings()
settings.load_aws_secrets()
