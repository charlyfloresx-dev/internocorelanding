import httpx
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger("interno_auth_client")

class InternoAuthClient:
    """
    Helper para manejar el flujo de autenticación multitenant de InternoCore.
    Soporta:
    1. Login (Handshake con Selection Token)
    2. Selección de Empresa (JWT Final)
    """
    
    def __init__(self, auth_url: str = "http://localhost:8001/api/v1/auth"):
        self.auth_url = auth_url
        self.selection_token: Optional[str] = None
        self.access_token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.companies: List[Dict[str, Any]] = []
        self.current_company_id: Optional[str] = None

    async def login(self, email: str, password: str) -> bool:
        """Realiza el paso 1 (Handshake)"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.auth_url}/login",
                    json={"email": email, "password": password}
                )
                response.raise_for_status()
                data = response.json().get("data", {})
                
                self.selection_token = data.get("selection_token")
                self.user_id = data.get("user_id")
                self.companies = data.get("companies", [])
                
                logger.info(f"Login successful for {email}. Found {len(self.companies)} companies.")
                return True
            except Exception as e:
                logger.error(f"Login failed: {e}")
                if 'response' in locals() and hasattr(response, 'text'): logger.error(f"Response: {response.text}")
                return False

    async def select_company(self, company_id: Optional[str] = None) -> Optional[str]:
        """Realiza el paso 2 (JWT Contextualizado)"""
        if not self.selection_token:
            raise ValueError("Must call login() before select_company()")
        
        # Si no se provee ID, usamos la primera empresa encontrada
        if not company_id and self.companies:
            company_id = self.companies[0]["company_id"]
        
        if not company_id:
            raise ValueError("No company_id provided and no companies found in login response")

        async with httpx.AsyncClient() as client:
            try:
                headers = {
                    "Authorization": f"Bearer {self.selection_token}",
                    "X-Selection-Token": self.selection_token
                }
                response = await client.post(
                    f"{self.auth_url}/select-company",
                    json={"company_id": str(company_id)},
                    headers=headers
                )
                response.raise_for_status()
                data = response.json().get("data", {})
                
                self.access_token = data.get("access_token")
                self.current_company_id = company_id
                
                logger.info(f"Company {company_id} selected. Access token obtained.")
                return self.access_token
            except Exception as e:
                logger.error(f"Select company failed: {e}")
                if 'response' in locals() and hasattr(response, 'text'): logger.error(f"Response: {response.text}")
                return None

    def get_headers(self) -> Dict[str, str]:
        """Retorna los headers necesarios para peticiones autenticadas"""
        if not self.access_token:
            return {}
        return {
            "Authorization": f"Bearer {self.access_token}",
            "X-Company-ID": str(self.current_company_id)
        }

    @classmethod
    async def get_authenticated_headers(cls, email: str, password: str, company_id: Optional[str] = None, auth_url: str = "http://localhost:8001/api/v1/auth"):
        """Shortcut para obtener headers en un solo paso"""
        instance = cls(auth_url)
        if await instance.login(email, password):
            if await instance.select_company(company_id):
                return instance.get_headers()
        return None
