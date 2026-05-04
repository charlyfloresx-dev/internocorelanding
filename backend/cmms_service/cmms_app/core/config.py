from pydantic_settings import SettingsConfigDict
from common.config import InternoSettings


class CMMSSettings(InternoSettings):
    """
    Configuración para el CMMS Service (Assets & Maintenance).
    Hereda de InternoSettings para garantizar consistencia en AWS y carga de secretos.
    Soporta almacenamiento híbrido: AWS S3 o sistema de archivos local.
    """
    PROJECT_NAME: str = "InternoCore CMMS Service"

    # Storage backend: "s3" | "local"
    STORAGE_TYPE: str = "local"

    # S3 configuration (used when STORAGE_TYPE="s3")
    S3_BUCKET_NAME: str = "interno-core-assets"
    S3_REGION: str = "us-east-1"

    # Local storage path (used when STORAGE_TYPE="local")
    LOCAL_STORAGE_PATH: str = "/app/storage"

    # QR signing secret (HMAC-SHA256)
    QR_SIGNING_SECRET: str = "change-me-in-production"

    # Storage tier limits (bytes)
    TIER_BASIC_BYTES: int = 2 * 1024 * 1024 * 1024       # 2 GB
    TIER_INDUSTRIAL_BYTES: int = 20 * 1024 * 1024 * 1024  # 20 GB
    TIER_ENTERPRISE_BYTES: int = 100 * 1024 * 1024 * 1024 # 100 GB

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=True
    )


settings = CMMSSettings()
settings.load_aws_secrets()
