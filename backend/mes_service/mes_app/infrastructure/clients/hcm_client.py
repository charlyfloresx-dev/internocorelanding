import uuid
import logging
import httpx
from typing import Optional, Dict, Any

from mes_app.core.config import settings
from common.context import request_context

logger = logging.getLogger(__name__)


class HCMClient:
    """
    HTTP Client for hcm_service.
    Fetches collaborator information to support MES tracking with weak-ref integration.
    """

    def __init__(self) -> None:
        self._base_url = f"{settings.int_hcm_service_url}/api/v1"
        self._timeout = httpx.Timeout(3.0, connect=2.0)

    def _headers(self, company_id: uuid.UUID) -> Dict[str, str]:
        headers = {"X-Company-ID": str(company_id)}
        try:
            ctx = request_context.get()
            if ctx and ctx.token:
                headers["Authorization"] = f"Bearer {ctx.token}"
        except Exception:
            pass
        return headers

    async def resolve_by_internal_id(
        self, internal_id: str, company_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Lookup collaborator by internal_id (gafete/badge number) using the
        validate-scan endpoint in hcm_service.
        Used as fallback in clock-in-by-badge when no CollaboratorBadge record exists.
        Returns minimal dict: {collaborator_id, full_name} or None.
        """
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                url = f"{self._base_url}/staff/validate-scan/{internal_id}"
                response = await client.get(url, headers=self._headers(company_id))
                if response.status_code == 200:
                    body = response.json()
                    data = body.get("data") or body
                    if data.get("collaborator_id"):
                        return {
                            "collaborator_id": data["collaborator_id"],
                            "full_name": data.get("full_name") or data.get("fullName") or internal_id,
                        }
        except Exception as exc:
            logger.error("HCMClient error resolving internal_id %s: %s", internal_id, exc)
        return None

    async def get_collaborator(
        self, collaborator_id: uuid.UUID, company_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves collaborator detail from hcm_service.
        Returns None on any HTTP/timeout error or 4xx/5xx responses (fails closed or degraded).
        """
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                url = f"{self._base_url}/staff/{collaborator_id}"
                response = await client.get(
                    url,
                    headers=self._headers(company_id),
                )
                if response.status_code == 200:
                    # Expect structure {status, data, message, meta}
                    body = response.json()
                    if isinstance(body, dict) and "data" in body:
                        return body["data"]
                    return body
                logger.error(
                    "HCMClient error: collaborator %s not found or API error (HTTP status: %s)",
                    collaborator_id,
                    response.status_code,
                )
        except httpx.TimeoutException as exc:
            logger.error("HCMClient timeout fetching collaborator %s: %s", collaborator_id, exc)
        except httpx.HTTPError as exc:
            logger.error("HCMClient HTTP error fetching collaborator %s: %s", collaborator_id, exc)
        except Exception as exc:
            logger.error("HCMClient unexpected error fetching collaborator %s: %s", collaborator_id, exc)
        return None
