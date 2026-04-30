import subprocess
import uuid
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("master_seed")

# IDs Homologados
ENTERPRISE_ID  = "9cd9986b-89da-48b7-8733-26a2a1225b01"
LOGISTICS_MX_ID = "ad6cc8a6-34f9-42df-8f29-28254e0ad242"
LOGISTICS_US_ID = "777cc8a6-34f9-42df-8f29-28254e0ad277"
DEMO_ID        = "203e03c9-5d65-43ff-9e83-864ef605426c"

COMPANIES = [ENTERPRISE_ID, LOGISTICS_MX_ID, LOGISTICS_US_ID, DEMO_ID]

SERVICES = [
    {"name": "auth-service-api", "script": "scripts/seed.py", "wipe_flag": False}, # Auth seed manages its own wipe/idempotency
    {"name": "master-data-service-api", "script": "scripts/seed.py", "wipe_flag": True},
    {"name": "inventory-service-api", "script": "scripts/seed.py", "wipe_flag": True},
    {"name": "wms-service-api", "script": "scripts/seed.py", "wipe_flag": True},
    {"name": "hcm-service-api", "script": "scripts/seed.py", "wipe_flag": False}, # HR ID management is sensitive
    {"name": "mes-service-api", "script": "scripts/seed.py", "wipe_flag": False},
    {"name": "subscription-service-api", "script": "scripts/seed.py", "wipe_flag": True},
    {"name": "viatra-service-api", "script": "scripts/seed_demo.py", "wipe_flag": False},
]

def run_command(cmd):
    logger.info(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"Error executing command: {result.stderr}")
        return False
    logger.info(f"Success: {result.stdout.strip()}")
    return True

def main():
    logger.info("🚀 Iniciando Orquestación de Seed Centralizado...")
    
    # 1. Auth Service (Solo una vez, ya maneja las 3 empresas internamente)
    logger.info("--- Sembrando AUTH SERVICE ---")
    run_command(["docker", "exec", "auth-service-api", "python", "scripts/seed.py"])

    # 2. Otros Servicios (Bucle por empresa)
    for service in SERVICES[1:]:
        service_name = service["name"]
        script_path = service["script"]
        
        logger.info(f"--- Sembrando {service_name} ---")
        
        first_run = True
        for company_id in COMPANIES:
            cmd = ["docker", "exec", service_name, "python", script_path, "--company-id", company_id]
            
            # Wipe solo en la primera empresa para limpiar el servicio, luego anexar
            if first_run and service["wipe_flag"]:
                cmd.append("--wipe")
                first_run = False
            
            if not run_command(cmd):
                logger.error(f"Falló el sembrado de {service_name} para {company_id}")
                # Continuamos con el siguiente para intentar completar lo máximo posible

    logger.info("✅ MASTER SEED FINALIZADO")

if __name__ == "__main__":
    main()
