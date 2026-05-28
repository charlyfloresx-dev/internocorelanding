import uuid
import logging
import httpx
from typing import List

from common.config import settings
from common.context import request_context
from mes_app.schemas.scan_pattern import ScanPatternRead

logger = logging.getLogger(__name__)


class MasterDataClient:
    """
    HTTP client for master_data_service.
    Fetches per-item scan patterns for validation at scan time.
    """

    def __init__(self):
        self._base_url = f"{settings.int_master_data_service_url}/api/v1"
        self._timeout = httpx.Timeout(3.0, connect=2.0)

    def _headers(self, company_id: uuid.UUID) -> dict:
        headers = {"X-Company-ID": str(company_id)}
        try:
            ctx = request_context.get()
            if ctx and ctx.token:
                headers["Authorization"] = f"Bearer {ctx.token}"
        except Exception:
            pass
        return headers

    async def get_scan_patterns(
        self, item_code: str, company_id: uuid.UUID
    ) -> List[ScanPatternRead]:
        """
        Returns active scan patterns for item_code from master_data_service.
        Returns [] on any error (best-effort — caller decides how to handle empty list).
        """
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(
                    f"{self._base_url}/products/{item_code}/scan-patterns",
                    headers=self._headers(company_id),
                )
                if response.status_code == 200:
                    data = response.json().get("data", [])
                    return [ScanPatternRead(**p) for p in data]
                logger.debug(
                    "get_scan_patterns(%s) → HTTP %s", item_code, response.status_code
                )
        except (httpx.RequestError, httpx.TimeoutException) as exc:
            logger.debug("get_scan_patterns(%s) network error: %s", item_code, exc)
        except Exception as exc:
            logger.warning("get_scan_patterns(%s) unexpected error: %s", item_code, exc)
        return []
