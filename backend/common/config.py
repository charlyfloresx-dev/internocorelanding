import os
import json
import boto3
from typing import Optional, List, Union
from pydantic import Field, field_validator, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict
from botocore.exceptions import ClientError

class ConfigurationError(Exception):
    """Excepción para errores críticos de configuración."""
    pass

class StripeSettings(BaseSettings):
    """Configuración específica para la integración con Stripe."""
    int_stripe_public_key: Optional[str] = Field(None, description="Stripe Publishable Key")
    int_stripe_secret_key: Optional[str] = Field(None, description="Stripe Secret Key")
    int_stripe_webhook_secret: Optional[str] = Field(None, description="Stripe Webhook Secret")
    int_stripe_product_id: Optional[str] = Field(None, description="Stripe Product ID")

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False
    )

class InternoSettings(BaseSettings):
    """
    Núcleo de Configuración de Interno Core.
    Centraliza todas las variables críticas con el prefijo INT_.
    Implementa un enfoque 'Fail-Closed' y carga dinámica de secretos en AWS.
    """
    # Básicos
    int_environment: str = "development"
    int_project_name: str = "Interno Core"
    int_api_v1_str: str = "/api/v1"
    
    # 3. VALIDACIÓN DE TENANT (Solo para rutas PRIVADAS)
    SECRET_KEY: str = Field(
        default="local-dev-secret-key-InternoCore", 
        validation_alias=AliasChoices("INT_SECRET_KEY", "SECRET_KEY"),
        description="Llave secreta para firmado de JWT"
    )
    ALGORITHM: str = Field(
        default="HS256", 
        validation_alias=AliasChoices("INT_ALGORITHM", "ALGORITHM")
    )
    
    # Base de Datos
    DATABASE_URL: str = Field(
        default=os.getenv("INT_DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5433/dbname"), 
        validation_alias=AliasChoices("INT_DATABASE_URL", "DATABASE_URL"),
        description="URL de conexión a la base de datos (asyncpg)"
    )
    
    # Infraestructura & AWS
    int_aws_region: str = "us-east-2"
    int_aws_secret_id: Optional[str] = None
    int_multi_tenant_mode: bool = True
    
    # Mail Config (Notificaciones)
    int_mail_server: Optional[str] = None
    int_mail_port: Optional[int] = 587
    int_mail_username: Optional[str] = None
    int_mail_password: Optional[str] = None
    
    # CORS & Web
    int_backend_cors_origins: List[str] = ["*"]
    int_frontend_url: str = "http://localhost:4200"
 
    # Providers (Wait, better grouped)
    int_resend_api_key: Optional[str] = None

    # SaaS / Stripe
    stripe: StripeSettings = Field(default_factory=StripeSettings)

    # --- Propiedades de Compatibilidad (Legacy) ---
    @property
    def PROJECT_NAME(self) -> str:
        return self.int_project_name
        
    @property
    def API_V1_STR(self) -> str:
        return self.int_api_v1_str

    @property
    def BACKEND_CORS_ORIGINS(self) -> List[str]:
        return self.int_backend_cors_origins

    @property
    def ENV_MODE(self) -> str:
        return self.int_environment

    @property
    def RESEND_API_KEY(self) -> Optional[str]:
        return self.int_resend_api_key

    @property
    def FRONTEND_URL(self) -> str:
        return self.int_frontend_url

    @property
    def DB_POOL_SIZE(self) -> int:
        return 5
        
    @property
    def DB_MAX_OVERFLOW(self) -> int:
        return 10

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False
    )

    def load_aws_secrets(self):
        """
        Si el entorno es producción, intenta cargar secretos desde AWS Secrets Manager.
        """
        if self.int_environment.lower() != "production" or not self.int_aws_secret_id:
            return

        try:
            session = boto3.session.Session()
            client = session.client(
                service_name='secretsmanager',
                region_name=self.int_aws_region
            )
            get_secret_value_response = client.get_secret_value(
                SecretId=self.int_aws_secret_id
            )
            
            if 'SecretString' in get_secret_value_response:
                secrets = json.loads(get_secret_value_response['SecretString'])
                # Mapeo manual de secretos de AWS a los atributos de la clase (quitando prefijo si vienen así)
                for key, value in secrets.items():
                    attr_name = key.lower()
                    if not attr_name.startswith("int_"):
                        attr_name = f"int_{attr_name}"
                    
                    if hasattr(self, attr_name):
                        setattr(self, attr_name, value)
                        
        except ClientError as e:
            print(f"⚠️ Error cargando secretos de AWS: {e.response['Error']['Code']}")
        except Exception as e:
            print(f"⚠️ Error inesperado en carga de secretos AWS: {str(e)}")

# Instanciación global
try:
    settings = InternoSettings()
    settings.load_aws_secrets()
except Exception as e:
    error_msg = f"❌ ERROR CRÍTICO DE CONFIGURACIÓN (Fail-Fast): {str(e)}"
    print(error_msg)
    # En lugar de settings = None, lanzamos excepción para detener el proceso
    raise ConfigurationError(error_msg)
