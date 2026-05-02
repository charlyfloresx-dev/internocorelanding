import asyncio
import httpx
import logging
import signal
from datetime import datetime, timezone
from sqlalchemy import select
from tickets_app.dependencies.database import SessionLocal
from tickets_app.models.outbox import OutboxEvent
from common.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("outbox_worker")

# Notification Service URL loaded from environment config
NOTIFICATION_SERVICE_URL = getattr(settings, "int_notification_service_url", "http://notification-service:8000/api/v1/events")

class OutboxWorker:
    """
    Background worker that polls the active Outbox Events
    and delivers them sequentially to the Notification Service over HTTP.
    Provides At-Least-Once delivery semantics with Idempotency handled by the receiver.
    """
    
    def __init__(self):
        self.should_run = True

    def stop(self):
        self.should_run = False
        logger.info("Stopping OutboxWorker...")

    async def process_outbox(self):
        """Processes a single batch of outbox events."""
        async with SessionLocal() as db:
            # 1. Fetch pending events
            stmt = select(OutboxEvent).where(OutboxEvent.is_processed == False).limit(50)
            result = await db.execute(stmt)
            events = result.scalars().all()
            
            if not events:
                return 0

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
                            logger.error(f"[!] Notification Service rejected event {event.id}: {response.text}")
                            event.error_message = f"HTTP {response.status_code}: {response.text}"
                    except Exception as e:
                        logger.error(f"[!] Network Error forwarding event {event.id}: {e}")
                        event.error_message = str(e)
            
            # 3. Commit state changes
            await db.commit()
            return processed_count

    async def run_forever(self):
        """Infinite loop for the worker."""
        logger.info(f"[START] OutboxWorker persistent loop (Interval: 5s, URL: {NOTIFICATION_SERVICE_URL})")
        
        while self.should_run:
            try:
                processed = await self.process_outbox()
                if processed > 0:
                    logger.info(f"Successfully processed {processed} events.")
            except Exception as e:
                logger.error(f"Unexpected error in worker loop: {e}")
            
            await asyncio.sleep(5)

async def main():
    worker = OutboxWorker()
    
    # Handle termination signals for graceful shutdown in Docker
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, worker.stop)
        except NotImplementedError:
            # Signal handlers are not implemented on Windows (common in dev)
            pass

    await worker.run_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
