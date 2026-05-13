import asyncio
import sys
import os

base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if base_path not in sys.path:
    sys.path.append(base_path)

services = [
    "auth_service", 
    "master_data_service", 
    "inventory_service", 
    "notification_service",
    "tickets_service",
    "mes_service",
    "subscription_service",
    "hcm_service",
    "wms_service"
]
for s in services:
    path = os.path.join(base_path, s)
    if path not in sys.path:
        sys.path.append(path)

from common.infrastructure.database import engine
from common.models import Base
# Importar main_monolith asegura que todas las rutas y por ende todos los modelos sean registrados
import main_monolith

async def init_db():
    print("Initializing Database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables initialized successfully!")

if __name__ == "__main__":
    asyncio.run(init_db())
