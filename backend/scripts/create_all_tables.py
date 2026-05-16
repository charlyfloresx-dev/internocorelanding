import asyncio
import sys
import os

# Set up paths
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_dir)
for service in ['auth_service', 'master_data_service', 'inventory_service', 'tickets_service', 'subscription_service', 'hcm_service', 'mes_service', 'notification_service']:
    sys.path.append(os.path.join(backend_dir, service))

from common.infrastructure.database import engine
from common.infrastructure.models.base import Base

# Import all models to register with Base
import auth_app.models
import auth_app.models.user
import auth_app.models.user_credential
import auth_app.models.role
import auth_app.models.user_company_role
import master_app.models
import master_app.models.uom
import master_app.models.movement_concept
import master_app.models.warehouse
import master_app.models.location
import master_app.models.product
import master_app.models.partner
import inventory_app.models
import inventory_app.models.warehouse
import inventory_app.models.location
import tickets_app.models
import tickets_app.models.ticket
import hcm_app.models
import hcm_app.models.collaborator
import subscription_app.models
import subscription_app.models.subscription
import common.models
import common.models.enumeration
import common.models.external_contact

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("All tables created successfully.")

if __name__ == "__main__":
    asyncio.run(create_tables())
