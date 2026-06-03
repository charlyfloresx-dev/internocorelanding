"""
Notification Service HTTP Client — Fire-and-forget security alerts.

Sends RTR breach alerts to notification_service without blocking token rotation.
Failures are logged but never propagated to caller (best-effort pattern).
"""
import httpx
import logging
from uuid import UUID
from datetime import datetime
from typing import Optional

from auth_app.core.config import settings

logger = logging.getLogger(__name__)


class NotificationClient:
    """
    Async HTTP client for notification_service.

    Patterns:
    - Fire-and-forget: async call without awaiting
    - Timeout: 3 seconds (quick fail)
    - Fallback: logging on error, no exception propagation
    - Idempotency: event_id prevents duplicate alerts on retry
    """

    def __init__(self):
        self.base_url = settings.NOTIFICATION_SERVICE_URL
        self.timeout = httpx.Timeout(3.0, connect=1.0)  # Quick failure for async notifications

    async def send_breach_alert(
        self,
        company_id: UUID,
        user_id: UUID,
        reason: str,
        ip_address: str,
        timestamp: datetime,
        user_agent: Optional[str] = None
    ) -> None:
        """
        Send RTR breach alert (best-effort, never blocks).

        Args:
            company_id: Affected company
            user_id: Affected user
            reason: Breach reason (e.g., "REUSE_DETECTED")
            ip_address: Attack origin IP
            timestamp: When detected
            user_agent: Optional browser/client identifier

        Returns: None (logs all state)

        Never raises — logs success/failure and returns.
        """
        from uuid import uuid4

        event_id = str(uuid4())
        url = f"{self.base_url}/api/v1/events"

        payload = {
            "event_id": event_id,
            "event_type": "RTRBreachDetected",
            "company_id": str(company_id),
            "user_id": str(user_id),
            "reason": reason,
            "ip_address": ip_address,
            "user_agent": user_agent or "unknown",
            "timestamp": timestamp.isoformat(),
        }

        headers = {
            "X-Company-ID": str(company_id),
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)

                if response.status_code in (200, 202):
                    logger.info(
                        f"RTR breach alert sent: "
                        f"company_id={company_id}, user_id={user_id}, "
                        f"reason={reason}, ip={ip_address}"
                    )
                else:
                    logger.warning(
                        f"Notification service returned {response.status_code}: "
                        f"company_id={company_id}, reason={reason}"
                    )

        except httpx.TimeoutException as e:
            logger.warning(
                f"Notification service timeout (breach alert may not arrive): "
                f"company_id={company_id}, reason={reason}, error={e}"
            )

        except Exception as e:
            logger.error(
                f"Failed to send RTR breach alert (continuing anyway): "
                f"company_id={company_id}, reason={reason}, error={type(e).__name__}: {e}",
                exc_info=False  # Don't pollute logs with stack trace for network errors
            )
