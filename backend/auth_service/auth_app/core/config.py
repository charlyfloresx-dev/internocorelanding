from pydantic import Field, AliasChoices
from pydantic_settings import SettingsConfigDict
from common.config import InternoSettings
from typing import Optional

class AuthSettings(InternoSettings):
    """
    Configuración escalable para Auth Service.
    Hereda de InternoSettings para asegurar consistencia en AWS y carga de secretos.
    """
    PROJECT_NAME: str = "InternoCore Auth Service"
    API_V1_STR: str = "/api/v1"
    
    # Token Lifetimes
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days
    SELECTION_TOKEN_EXPIRE_MINUTES: int = 5
    
    # Industrial Connectivity [Phase 94]
    # Manual override for public/LAN IP detection
    INT_API_EXTERNAL_URL: Optional[str] = Field(default=None, validation_alias=AliasChoices("INT_API_EXTERNAL_URL", "CORE_EXTERNAL_URL"))
    
    # Service URLs
    SUBSCRIPTION_SERVICE_URL: str = Field(
        default="http://subscription-service:8000",
        validation_alias=AliasChoices("CORE_SUBSCRIPTION_URL", "SUBSCRIPTION_SERVICE_URL")
    )
    HCM_SERVICE_URL: str = Field(
        default="http://hcm-service:8000",
        validation_alias=AliasChoices("CORE_HCM_URL", "HCM_SERVICE_URL")
    )
    
    # OAuth
    GOOGLE_CLIENT_ID: str = Field(default="", validation_alias=AliasChoices("CORE_GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_ID"))
    FB_APP_ID: str = Field(default="", validation_alias=AliasChoices("CORE_FB_APP_ID", "FB_APP_ID"))
    FB_APP_SECRET: str = ""
    AZURE_CLIENT_ID: str = ""
    
    # WebAuthn
    WEBAUTHN_RP_ID: str = Field(default="", validation_alias=AliasChoices("CORE_WEBAUTHN_RP_ID", "WEBAUTHN_RP_ID"))
    WEBAUTHN_RP_NAME: str = Field(default="Interno Core Biometrics", validation_alias=AliasChoices("CORE_WEBAUTHN_RP_NAME", "WEBAUTHN_RP_NAME"))
    WEBAUTHN_ORIGIN: str = Field(default="", validation_alias=AliasChoices("CORE_WEBAUTHN_ORIGIN", "WEBAUTHN_ORIGIN"))


    @property
    def ASYNC_DATABASE_URL(self) -> str:
        if self.DATABASE_URL.startswith("postgresql://"):
            return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self.DATABASE_URL

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=True
    )

# Singleton instantiation with automatic AWS secret loading
settings = AuthSettings()
settings.load_aws_secrets()
