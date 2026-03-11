from common.config import settings as base_settings
from typing import List

class AuthSettingsWrapper:
    def __init__(self, base):
        if not base:
            # Fallback for initialization phase if necessary, though base should exist
            self._base = None
            self.DATABASE_URL = ""
            self.SECRET_KEY = "changeme"
        else:
            self._base = base
            # Mapping required by auth_service
            self.DATABASE_URL = getattr(base, "DATABASE_URL", "")
            self.SECRET_KEY = getattr(base, "SECRET_KEY", "changeme")
        
        self.ALGORITHM = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7
        self.SELECTION_TOKEN_EXPIRE_MINUTES = 5
        self.BACKEND_CORS_ORIGINS = getattr(base, "int_backend_cors_origins", ["*"])
        self.SUBSCRIPTION_SERVICE_URL = "http://subscription-service:8000"

    def __getattr__(self, name):
        if self._base:
            return getattr(self._base, name)
        raise AttributeError(f"AuthSettingsWrapper has no attribute {name}")

# Create the singleton wrapper
settings = AuthSettingsWrapper(base_settings)