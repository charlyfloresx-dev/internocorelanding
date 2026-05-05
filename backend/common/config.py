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
    Centraliza todas las variables críticas con el prefijo CORE_.
    Implementa un enfoque 'Fail-Closed' y carga dinámica de secretos en AWS.
    """
    # Básicos
    int_project_name: str = "Interno Core"
    int_api_v1_str: str = "/api/v1"
    
    # 3. VALIDACIÓN DE TENANT (Solo para rutas PRIVADAS)
    SECRET_KEY: str = Field(
        default="local-dev-secret-key-InternoCore", 
        validation_alias=AliasChoices("CORE_SECRET_KEY", "SECRET_KEY", "JWT_SECRET"),
        description="Llave secreta para firmado de JWT"
    )
    ALGORITHM: str = Field(
        default="HS256", 
        validation_alias=AliasChoices("CORE_ALGORITHM", "ALGORITHM", "JWT_ALGORITHM")
    )
    
    # Base de Datos
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://user:password@db:5432/dbname", 
        validation_alias=AliasChoices("CORE_DATABASE_URL", "DATABASE_URL", "SQLALCHEMY_DATABASE_URI"),
        description="URL de conexión a la base de datos (asyncpg)"
    )
    
    # Almacenamiento (S3 / Local)
    STORAGE_BACKEND: str = Field(
        default="local", 
        validation_alias=AliasChoices("CORE_STORAGE_BACKEND", "STORAGE_BACKEND"),
        description="S3 | LOCAL"
    )
    S3_ENDPOINT: Optional[str] = Field(
        default=None, 
        validation_alias=AliasChoices("CORE_S3_ENDPOINT", "S3_ENDPOINT"),
        description="Endpoint para MinIO/LocalStack (ej. http://localstack:4566)"
    )
    S3_BUCKET: str = Field(
        default="momentos-assets", 
        validation_alias=AliasChoices("CORE_S3_BUCKET", "S3_BUCKET")
    )
    S3_ACCESS_KEY: Optional[str] = Field(
        None, validation_alias=AliasChoices("CORE_S3_ACCESS_KEY", "S3_ACCESS_KEY")
    )
    S3_SECRET_KEY: Optional[str] = Field(
        None, validation_alias=AliasChoices("CORE_S3_SECRET_KEY", "S3_SECRET_KEY")
    )
    S3_PUBLIC_URL: Optional[str] = Field(
        None, 
        validation_alias=AliasChoices("CORE_S3_PUBLIC_URL", "S3_PUBLIC_URL"),
        description="URL pública (CloudFront / MinIO Public Gateway)"
    )
    LOCAL_STORAGE_PATH: str = Field(
        default="/app/storage", 
        validation_alias=AliasChoices("CORE_LOCAL_STORAGE_PATH", "LOCAL_STORAGE_PATH")
    )

    # Infraestructura & AWS
    int_environment: str = Field(
        default="development",
        validation_alias=AliasChoices("CORE_ENV_MODE", "ENV_MODE", "INT_ENVIRONMENT")
    )
    int_aws_region: str = "us-east-2"
    int_aws_secret_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("CORE_AWS_SECRET_ID", "AWS_SECRET_ID", "INT_AWS_SECRET_ID")
    )
    int_multi_tenant_mode: bool = True
    
    # Mail Config (Notificaciones)
    int_mail_server: Optional[str] = None
    int_mail_port: Optional[int] = 587
    int_mail_username: Optional[str] = None
    int_mail_password: Optional[str] = None
    
    # CORS & Web
    int_backend_cors_origins: List[str] = Field(
        default=[
            "http://127.0.0.1:4200",
            "http://localhost:4200",
            "http://dev-frontend.interno.local:4200",
            "http://dev-frontend.interno.local:3000",
            "http://127.0.0.1:3000",
            "https://d3b47jx48onn9j.cloudfront.net",
            "https://jtq5mfp8pj.us-east-2.awsapprunner.com",
            "https://*.vercel.app",
            "https://interno-core-frontend.vercel.app"
        ],
        validation_alias=AliasChoices("CORE_BACKEND_CORS_ORIGINS", "BACKEND_CORS_ORIGINS")
    )
    
    @field_validator("int_backend_cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("["):
                try:
                    import json
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v
    int_cors_allowed_headers: List[str] = [
        "X-Company-ID", "x-company-id",
        "X-User-ID", "x-user-id",
        "X-Trace-Id", "X-Transaction-ID", "x-transaction-id",
        "X-Client-Request-ID", "x-client-request-id",
        "X-Selection-Token", "x-selection-token",
        "X-Admin-Master-Key",
        "X-Silent-Error", "x-silent-error",
        "X-Warehouse-ID", "x-warehouse-id",
        "Authorization", 
        "Content-Type", 
        "Accept", 
        "Origin",
        "X-Correlation-ID", "x-correlation-id",
        "X-Correlation-Id"
    ]
    int_cors_exposed_headers: List[str] = ["X-Transaction-ID", "X-Trace-Id", "X-Selection-Token", "Content-Disposition", "content-disposition"]
    int_frontend_url: str = Field(
        default="http://dev-frontend.interno.local:4200",
        validation_alias=AliasChoices("CORE_FRONTEND_URL", "FRONTEND_URL")
    )
 
    # Providers
    int_resend_api_key: Optional[str] = Field(
        None, 
        validation_alias=AliasChoices("CORE_RESEND_API_KEY", "RESEND_API_KEY")
    )

    # ── [INDUSTRIAL SECURITY] ──────────────────────────────────────────────
    int_internal_api_key: str = Field(
        default="DEV_INTERNAL_API_KEY_CHANGE_ME",
        validation_alias=AliasChoices("CORE_INTERNAL_API_KEY", "INTERNAL_API_KEY")
    )
    int_rfid_static_salt: str = Field(
        default="INTERNO_HR_RFID_DEFAULT_SALT_CHANGE_ME",
        validation_alias=AliasChoices("CORE_HR_RFID_SALT", "RFID_STATIC_SALT")
    )
    int_admin_master_key: str = Field(
        default="GOD_MODE_ACTIVE",
        validation_alias=AliasChoices("CORE_ADMIN_MASTER_KEY", "ADMIN_MASTER_KEY")
    )

    # ── CURRENCY / BANXICO ──────────────────────────────────────────────────
    int_banxico_token: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("CORE_BANXICO_TOKEN", "BANXICO_TOKEN")
    )
    int_banxico_serie_usd: str = "SF43718"  # Dólar FIX (USD → MXN)
    int_currency_variation_threshold: float = 0.10  # 10% = suspicious flag
    int_currency_service_url: str = Field(
        default="http://currency-service:8000", 
        validation_alias=AliasChoices("CORE_CURRENCY_SERVICE_URL", "CURRENCY_SERVICE_URL"),
        description="URL del microservicio de tipos de cambio"
    )
    int_master_data_service_url: str = Field(
        default="http://master-data-service:8000", 
        validation_alias=AliasChoices("CORE_MASTER_DATA_SERVICE_URL", "MASTER_DATA_SERVICE_URL"),
        description="URL del microservicio de datos maestros"
    )
    int_notification_service_url: str = Field(
        default="http://notification-service:8000", 
        validation_alias=AliasChoices("CORE_NOTIFICATION_SERVICE_URL", "NOTIFICATION_SERVICE_URL"),
        description="URL del microservicio de notificaciones"
    )
    int_inventory_service_url: str = Field(
        default="http://inventory-service:8000", 
        validation_alias=AliasChoices("CORE_INVENTORY_SERVICE_URL", "INVENTORY_SERVICE_URL"),
        description="URL del microservicio de inventario"
    )

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
    def INTERNAL_API_KEY(self) -> str:
        return self.int_internal_api_key

    @property
    def RFID_STATIC_SALT(self) -> str:
        return self.int_rfid_static_salt

    @property
    def FRONTEND_URL(self) -> str:
        return self.int_frontend_url

    @property
    def DB_POOL_SIZE(self) -> int:
        return 5
        
    @property
    def CURRENCY_SERVICE_URL(self) -> str:
        return self.int_currency_service_url

    @property
    def MASTER_DATA_SERVICE_URL(self) -> str:
        return self.int_master_data_service_url

    @property
    def NOTIFICATION_SERVICE_URL(self) -> str:
        return self.int_notification_service_url

    @property
    def INVENTORY_SERVICE_URL(self) -> str:
        return self.int_inventory_service_url

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        return self.DATABASE_URL
        
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
        Si el entorno es producción o modo AWS, intenta cargar secretos desde AWS Secrets Manager.
        """
        env = self.int_environment.lower()
        if env not in ["production", "prod", "aws"] or not self.int_aws_secret_id:
            print(f"DEBUG: Skipping AWS secrets loading (Env: {env}, SecretID: {self.int_aws_secret_id})")
            return

        print(f"DEBUG: Loading secrets from AWS ID: {self.int_aws_secret_id} in {self.int_aws_region}...")
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
                for key, value in secrets.items():
                    # Mapeo universal de atributos
                    possible_attrs = [key, key.upper(), key.lower(), f"int_{key.lower()}"]
                    
                    found = False
                    for attr in possible_attrs:
                        if hasattr(self, attr):
                            setattr(self, attr, value)
                            print(f"DEBUG: Mapped AWS secret '{key}' to setting '{attr}'")
                            found = True
                            break
                    
                    if not found:
                        # Si no existe, lo agregamos como atributo dinámico
                        setattr(self, key, value)
                        print(f"DEBUG: Added dynamic AWS secret '{key}'")
                        
        except ClientError as e:
            print(f"WARNING: Error loading AWS secrets: {e.response['Error']['Code']}")
        except Exception as e:
            print(f"WARNING: Unexpected error in AWS secrets loading: {str(e)}")

# Instanciación global
try:
    settings = InternoSettings()
    settings.load_aws_secrets()
except Exception as e:
    error_msg = f"CRITICAL CONFIGURATION ERROR (Fail-Fast): {str(e)}"
    print(error_msg)
    # En lugar de settings = None, lanzamos excepción para detener el proceso
    raise ConfigurationError(error_msg)
