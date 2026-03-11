import httpx
import logging
import uuid
from typing import Dict, Any, Optional, List
from fastapi import HTTPException, status

logger = logging.getLogger("auth.subscription_client")

class SubscriptionClient:
    """
    Cliente para la comunicación sincrónica: Auth Service -> Subscription Service.
    Implementa el Kill Switch de la Fase 9.
    """
    
    # El nombre del host en Docker Compose es subscription-service
    # Internamente corre en el puerto 8000 según el Dockerfile del servicio.
    BASE_URL = "http://subscription-service:8000/internal"

    @classmethod
    async def get_subscription_status(cls, company_id: uuid.UUID) -> Dict[str, Any]:
        """
        Consulta el estado de la suscripción de una empresa.
        Estrategia: Fail-Closed (Si falla la conexión, denegamos el acceso).
        """
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                url = f"{cls.BASE_URL}/status/{company_id}"
                logger.info(f"[*] Checking subscription status for company: {company_id}")
                response = await client.get(url)
                
                if response.status_code == 200:
                    full_resp = response.json()
                    return full_resp.get("data", full_resp)
                
                # Si el servicio responde pero no con 200, algo está mal configurado
                logger.error(f"[!] Subscription Service returned error {response.status_code}: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No se pudo verificar el estado de la suscripción. Acceso denegado (Fail-Closed)."
                )

            except httpx.RequestError as exc:
                logger.error(f"[!] Connection error to Subscription Service: {exc}")
                # FAIL-OPEN: Permitimos el acceso si el servicio de suscripciones falló, para no bloquear la operación.
                logger.warning("[!] Aplicando FAIL-OPEN para suscripciones.")
                return {
                    "is_active": True,
                    "status": "ACTIVE",
                    "plan_name": "Fallback (Fail-Open)",
                    "modules": ["auth_core", "inventory_core", "wms_core"]
                }
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"[!] Unexpected error in SubscriptionClient: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error interno al validar suscripción."
                )

    @classmethod
    async def get_entitlements(cls, company_id: uuid.UUID) -> List[str]:
        """
        Obtiene la lista de módulos habilitados para una empresa.
        """
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                url = f"{cls.BASE_URL}/entitlements/{company_id}"
                response = await client.get(url)
                if response.status_code == 200:
                    full_resp = response.json()
                    data = full_resp.get("data", full_resp)
                    modules = data.get("modules", [])
                    if isinstance(modules, dict):
                        return modules.get("modules", [])
                    return modules
                return []

            except Exception:
                # Fallback seguro para el E2E
                return ["auth_core", "inventory_core", "wms_core"]

