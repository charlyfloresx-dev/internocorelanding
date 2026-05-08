import asyncio
import logging
import signal

# Absolute imports based on PYTHONPATH in Docker
try:
    from scripts.outbox_worker import OutboxWorker
    from scripts.escalation_watcher import EscalationWatcher
except ImportError:
    from outbox_worker import OutboxWorker
    from escalation_watcher import EscalationWatcher

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("unified_worker")

async def main():
    logger.info("Starting Unified Background Worker...")
    
    outbox_worker = OutboxWorker()
    
    # Handle termination signals for graceful shutdown in Docker
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, outbox_worker.stop)
        except NotImplementedError:
            pass

    # Run both background task loops concurrently
    # asyncio.gather will run them together and wait for both
    await asyncio.gather(
        outbox_worker.run_forever(),
        EscalationWatcher.run()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Unified Worker Shutdown gracefully.")
