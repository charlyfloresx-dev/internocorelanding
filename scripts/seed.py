import os
import subprocess
import sys
import logging

# Configuration
SERVICES = [
    {"name": "auth-service", "path": "backend/auth_service"},
    {"name": "master-data-service", "path": "backend/master_data_service"},
    {"name": "subscription-service", "path": "backend/subscription_service"},
    {"name": "inventory-service", "path": "backend/inventory_service", "python_module": "scripts/seed.py", "is_module": False},
    {"name": "wms-service", "path": "backend/wms_service"},
]

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_service_seed(service):
    service_name = service["name"]
    logger.info(f"🌱 Seeding {service_name}...")
    
    python_target = service.get("python_module", "scripts.seed")
    is_module = service.get("is_module", True)
    
    cmd = ["docker-compose", "run", "--rm", service_name]
    if is_module:
        cmd += ["python", "-m", python_target]
    else:
        cmd += ["python", python_target]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"✅ {service_name} seeded successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Error seeding {service_name}: {e.stderr or e.stdout}")
        return False

def main():
    logger.info("🚀 Starting Unified Master Seed Orchestration...")
    
    success_count = 0
    for service in SERVICES:
        if run_service_seed(service):
            success_count += 1
            
    logger.info(f"🏁 Orchestration finished. {success_count}/{len(SERVICES)} services seeded successfully.")
    
    if success_count < len(SERVICES):
        sys.exit(1)

if __name__ == "__main__":
    main()
