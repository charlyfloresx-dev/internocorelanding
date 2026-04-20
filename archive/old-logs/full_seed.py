import asyncio
import os
import sys
import uuid
import logging
from datetime import datetime, timezone

# Add backend to path
backend_root = os.path.join(os.getcwd(), 'backend')
sys.path.insert(0, backend_root)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("FullSeed")

# --- MASTER CONFIGURATION ---
COMPANY_ID = uuid.UUID("9cd9986b-89da-48b7-8733-26a2a1225b01")            # InternoCorp Enterprise
LOGISTICS_COMPANY_ID = uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242")  # Interno Logistics
CHARLY_USER_ID = uuid.UUID("69aa5ddc-bbaa-46e6-a7f0-aeb4b92b6d38")


async def run_sub_seed(service_name: str, script_path: str):
    logger.info(f"🚀 Running seed for {service_name}...")

    # Build PYTHONPATH: backend root + service root (for 'app.*' imports)
    service_root = os.path.join(backend_root, service_name)
    python_path = os.pathsep.join([backend_root, service_root])
    env = {**os.environ, "PYTHONPATH": python_path}

    process = await asyncio.create_subprocess_exec(
        sys.executable, script_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=service_root,
        env=env
    )

    stdout, stderr = await process.communicate()

    if stdout:
        logger.info(f"[{service_name} STDOUT]\n{stdout.decode().strip()}")
    if stderr:
        # SQLAlchemy echos DDL to stderr even on success; only log as error on non-zero exit
        if process.returncode != 0:
            logger.error(f"[{service_name} STDERR]\n{stderr.decode().strip()}")
        else:
            logger.debug(f"[{service_name} STDERR (debug)]\n{stderr.decode().strip()[:500]}")

    if process.returncode == 0:
        logger.info(f"✅ {service_name} seed completed successfully.")
    else:
        logger.error(f"❌ {service_name} seed failed with exit code {process.returncode}")


async def main():
    logger.info("🎬 Starting Full System Seeding...")
    logger.info(f"   Backend root: {backend_root}")

    # 1. Auth Service Seed (Users/Companies — Source of Truth for IDs)
    auth_seed = os.path.join(backend_root, 'auth_service', 'scripts', 'seed.py')
    await run_sub_seed('auth_service', auth_seed)

    # 2. Master Data Service Seed (Products, Warehouses, Concepts)
    md_seed = os.path.join(backend_root, 'master_data_service', 'scripts', 'seed.py')
    await run_sub_seed('master_data_service', md_seed)

    # 3. Inventory Service Seed (Stock Levels, Movements, Documents)
    inv_seed = os.path.join(backend_root, 'inventory_service', 'scripts', 'seed.py')
    await run_sub_seed('inventory_service', inv_seed)

    logger.info("🏁 Full Seeding Process Finished.")


if __name__ == "__main__":
    asyncio.run(main())
