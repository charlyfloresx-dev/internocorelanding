from pydantic import Field
from pydantic_settings import SettingsConfigDict
from common.config import InternoSettings


class AssetManagerSettings(InternoSettings):
    """
    Configuración para el Asset Manager Service.
    Hereda de InternoSettings para alinearse con la convención de AWS Secrets.
    """
    PROJECT_NAME: str = "InternoCore Asset Manager Service"
    API_V1_STR: str = "/api/v1"
    SERVICE_PORT: int = 8006

    # URL del Master Data Service para comunicación interna
    MASTER_DATA_SERVICE_URL: str = Field(
        default="http://master-data-service:8003",
        alias="MASTER_DATA_SERVICE_URL"
    )

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore"
    )


settings = AssetManagerSettings()
settings.load_aws_secrets()
