from pydantic import Field, AliasChoices
from pydantic_settings import SettingsConfigDict
from common.config import InternoSettings
from typing import Optional

class KioskSettings(InternoSettings):
    """
    Configuración escalable para Kiosk Service.
    Hereda de InternoSettings para asegurar consistencia en AWS y carga de secretos.
    """
    PROJECT_NAME: str = "InternoCore Kiosk Service"
    
    # MinIO / S3 Storage (Compatibilidad con Kiosk Legacy)
    MINIO_URL: str = "http://minio:9000"
    MINIO_PUBLIC_URL: str = Field(default="http://127.0.0.1:9000", validation_alias="MINIO_PUBLIC_URL")
    MINIO_ACCESS_KEY: str = "admin"
    MINIO_SECRET_KEY: str = "password123"
    MINIO_BUCKET_NAME: str = "kiosk-events"

    PRICE_PER_PHOTO_CENTS: int = 5000 
    CORE_KIOSK_LAN_IP: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="allow",
        case_sensitive=True
    )

settings = KioskSettings()
settings.load_aws_secrets()
