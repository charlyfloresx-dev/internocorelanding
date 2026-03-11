from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Interno.Core.MES"
    API_V1_STR: str = "/api/v1"
    
    # Database
    POSTGRES_SERVER: str = Field("postgres-db", validation_alias="POSTGRES_SERVER")
    POSTGRES_USER: str = Field("user", validation_alias="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field("password", validation_alias="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field("mes_db", validation_alias="POSTGRES_DB")
    DATABASE_URL: Optional[str] = Field(None, validation_alias="DATABASE_URL")
    
    # Security (Auditor compliance)
    SECRET_KEY: str = Field("placeholder_for_auditor", validation_alias="SECRET_KEY")
    ALGORITHM: str = Field("HS256", validation_alias="ALGORITHM")

    @property
    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

    # AWS
    AWS_REGION: str = "us-east-1"
    ENV_MODE: str = "DEV"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
