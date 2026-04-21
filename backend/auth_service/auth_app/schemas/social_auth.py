"""
social_login Pydantic schemas for the POST /api/v1/auth/social-login endpoint.
"""
from pydantic import BaseModel
from typing import Literal, Optional


class SocialLoginRequest(BaseModel):
    """Payload de entrada para el flujo de autenticación social."""
    token: str
    provider: Literal["google", "facebook", "microsoft"]
    device_info: Optional[str] = None
