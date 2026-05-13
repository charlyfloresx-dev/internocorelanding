import asyncio
import uuid
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

_BACKEND = os.path.abspath(".")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

# Add service paths to sys.path
sys.path.insert(0, os.path.join(_BACKEND, "hcm_service"))
sys.path.insert(0, os.path.join(_BACKEND, "master_data_service"))

# Manual engines to avoid [db:5432] connection errors from settings
HCM_URL = "postgresql+asyncpg://user:password@localhost:5433/hcm_db"
MASTER_URL = "postgresql+asyncpg://user:password@localhost:5433/master_data_db"

hcm_engine = create_async_engine(HCM_URL, pool_pre_ping=True)
master_engine = create_async_engine(MASTER_URL, pool_pre_ping=True)

HCMSession = async_sessionmaker(hcm_engine, class_=AsyncSession, expire_on_commit=False)
MasterSession = async_sessionmaker(master_engine, class_=AsyncSession, expire_on_commit=False)

from hcm_app.models.collaborator import Collaborator
from common.models.external_contact import ExternalContact

async def get_ids():
    ids = {}
    
    # Collaborator
    try:
        async with HCMSession() as session:
            res = await session.execute(select(Collaborator).limit(1))
            c = res.scalars().first()
            ids["collaborator_id"] = str(c.id) if c else "NONE"
    except Exception as e:
        ids["collaborator_id"] = f"ERROR: {e}"

    # Contact
    try:
        async with MasterSession() as session:
            res = await session.execute(select(ExternalContact).limit(1))
            c = res.scalars().first()
            ids["contact_id"] = str(c.id) if c else "NONE"
    except Exception as e:
        ids["contact_id"] = f"ERROR: {e}"

    print(ids)
    await hcm_engine.dispose()
    await master_engine.dispose()

if __name__ == "__main__":
    asyncio.run(get_ids())
