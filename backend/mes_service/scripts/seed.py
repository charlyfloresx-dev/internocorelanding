"""
MES Service — entrypoint seed orchestrator.
Called by entrypoint.sh after alembic upgrade head.
"""
import asyncio
import logging
import os
import sys

_script_dir = os.path.dirname(os.path.abspath(__file__))
_service_root = os.path.abspath(os.path.join(_script_dir, ".."))
_backend_root = os.path.abspath(os.path.join(_service_root, ".."))
for _p in [_service_root, _backend_root, "/app"]:
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from scripts.seed_mes_config import seed_mes_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("mes-seed")


async def main() -> None:
    log.info(">> [MES Seed] starting...")
    await seed_mes_config()
    log.info(">> [MES Seed] completed.")


if __name__ == "__main__":
    asyncio.run(main())
