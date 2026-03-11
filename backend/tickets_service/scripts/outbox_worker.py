import asyncio
import httpx
import logging
from datetime import datetime, timezone
from sqlalchemy import select, update
from app.dependencies.database import SessionLocal
from app.models.outbox import OutboxEvent
from common.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("outbox_worker")

# Notification Service URL loaded from environment config (Docker/AWS compatible)
NOTIFICATION_SERVICE_URL = getattr(settings, "int_notification_service_url", "http://notification-service:8000/api/v1/events")

class OutboxWorker:
    """
    Background worker that polls the active Outbox Events
    and delivers them sequentially to the Notification Service over HTTP.
    Provides At-Least-Once delivery semantics with Idempotency handled by the receiver.
    """

    @classmethod
    async def process_outbox(cls):
        logger.info("[START] Processing Integration Outbox...")
        
        async with SessionLocal() as db:
            # 1. Fetch pending events
            stmt = select(OutboxEvent).where(OutboxEvent.is_processed == False).limit(50)
            result = await db.execute(stmt)
            events = result.scalars().all()
            
            if not events:
                logger.info("[END] No pending outbox events.")
                return

            processed_count = 0
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                for event in events:
                    try:
                        # 2. Forward to Notification Service
                        headers = {
                            "Content-Type": "application/json",
                            "X-Company-ID": str(event.company_id)
                        }
                        
                        response = await client.post(
                            NOTIFICATION_SERVICE_URL, 
                            content=event.payload, 
                            headers=headers
                        )

                        if response.status_code in (200, 201, 202):
                            # Mark as processed
                            event.is_processed = True
                            event.processed_at = datetime.now(timezone.utc)
                            processed_count += 1
                        else:
                            logger.error(f"[!] Notification Service rejected event {event.event_id}: {response.text}")
                            event.error_message = f"HTTP {response.status_code}: {response.text}"
                    except Exception as e:
                        logger.error(f"[!] Network Error forwarding event {event.event_id}: {e}")
                        event.error_message = str(e)
            
            # 3. Commit state changes
            await db.commit()
            logger.info(f"[END] Processed {processed_count} events from outbox.")

if __name__ == "__main__":
    asyncio.run(OutboxWorker.process_outbox())
