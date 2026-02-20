import asyncio
import sys
from sqlalchemy import text

sys.path.append("/app")
sys.path.append("/app/auth_service")

from app.core.database import engine
from common.models import Base
# Importamos todos los modelos para que Base los reconozca
import app.models.user
import app.models.company
import app.models.role
import app.models.permission
import app.models.role_permission
import app.models.user_company_role

async def create_tables():
    print("🚀 [INIT] Creando tablas en la base de datos...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ [SUCCESS] Tablas creadas correctamente.")

if __name__ == "__main__":
    asyncio.run(create_tables())
