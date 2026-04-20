"""
social_auth_service.py — Interno Core Auth Service
Valida tokens OAuth de Google, Facebook y Microsoft.
Devuelve un perfil de usuario social unificado (email, nombre, avatar).
"""
import httpx
from typing import Optional
from dataclasses import dataclass
from app.core.config import settings


@dataclass
class SocialProfile:
    email: str
    full_name: str
    avatar_url: Optional[str] = None
    provider: str = "unknown"
    provider_user_id: Optional[str] = None


class SocialAuthService:
    """
    Intermediario entre los proveedores OAuth externos (Google, Facebook, Microsoft)
    y el ecosistema de Interno Core.
    """

    async def validate_google_token(self, token: str) -> Optional[SocialProfile]:
        """
        Valida el ID token de Google usando el tokeninfo endpoint.
        En producción, usar google-auth-library para validación criptográfica.
        """
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": token},
                timeout=10.0,
            )

        if resp.status_code != 200:
            return None

        data = resp.json()

        # Validar que el aud coincida con nuestro GOOGLE_CLIENT_ID
        expected_aud = settings.GOOGLE_CLIENT_ID
        if expected_aud and data.get("aud") != expected_aud:
            return None

        email = data.get("email")
        if not email:
            return None

        return SocialProfile(
            email=email,
            full_name=data.get("name", email.split("@")[0]),
            avatar_url=data.get("picture"),
            provider="google",
            provider_user_id=data.get("sub"),
        )

    async def validate_facebook_token(self, token: str) -> Optional[SocialProfile]:
        """
        Valida el access token de Facebook usando el Graph API.
        """
        fb_app_id = settings.FB_APP_ID
        fb_app_secret = settings.FB_APP_SECRET

        async with httpx.AsyncClient() as client:
            # 1. Verificar token
            app_token = f"{fb_app_id}|{fb_app_secret}"
            debug_resp = await client.get(
                "https://graph.facebook.com/debug_token",
                params={"input_token": token, "access_token": app_token},
                timeout=10.0,
            )
            if debug_resp.status_code != 200:
                return None
            
            debug_data = debug_resp.json().get("data", {})
            if not debug_data.get("is_valid"):
                return None

            # 2. Obtener perfil
            profile_resp = await client.get(
                "https://graph.facebook.com/me",
                params={"access_token": token, "fields": "id,name,email,picture.type(large)"},
                timeout=10.0,
            )
            if profile_resp.status_code != 200:
                return None

        data = profile_resp.json()
        email = data.get("email")
        if not email:
            return None

        return SocialProfile(
            email=email,
            full_name=data.get("name", email.split("@")[0]),
            avatar_url=data.get("picture", {}).get("data", {}).get("url"),
            provider="facebook",
            provider_user_id=data.get("id"),
        )

    async def validate_microsoft_token(self, token: str) -> Optional[SocialProfile]:
        """
        Valida el access token de Microsoft usando Microsoft Graph /me.
        """
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://graph.microsoft.com/v1.0/me",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0,
            )

        if resp.status_code != 200:
            return None

        data = resp.json()
        email = data.get("mail") or data.get("userPrincipalName")
        if not email:
            return None

        full_name = data.get("displayName", email.split("@")[0])

        return SocialProfile(
            email=email,
            full_name=full_name,
            avatar_url=None,  # MS Graph requiere un endpoint separado para la foto
            provider="microsoft",
            provider_user_id=data.get("id"),
        )

    async def validate(self, token: str, provider: str) -> Optional[SocialProfile]:
        """Entry point unificado. Delega al validador correcto según el proveedor."""
        if provider == "google":
            return await self.validate_google_token(token)
        elif provider == "facebook":
            return await self.validate_facebook_token(token)
        elif provider == "microsoft":
            return await self.validate_microsoft_token(token)
        return None
