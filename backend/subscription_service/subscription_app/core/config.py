from typing import Optional
from pydantic import Field, AliasChoices
from pydantic_settings import SettingsConfigDict
from common.config import InternoSettings

class SubscriptionSettings(InternoSettings):
    """
    Configuración escalable para Subscription Service.
    Incluye integración con Stripe y gestión de planes.
    Hereda de InternoSettings para asegurar consistencia en AWS y carga de secretos.
    """
    PROJECT_NAME: str = "InternoCore Subscription Service"
    
    # STRIPE CONFIGURATION
    STRIPE_API_KEY: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("CORE_STRIPE_SECRET_KEY", "STRIPE_API_KEY")
    )
    STRIPE_WEBHOOK_SECRET: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("CORE_STRIPE_WEBHOOK_SECRET", "STRIPE_WEBHOOK_SECRET")
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=True
    )

settings = SubscriptionSettings()
settings.load_aws_secrets()
