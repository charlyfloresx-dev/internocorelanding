import asyncio
import os
import sys

# Path normalization
current = os.path.dirname(os.path.abspath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from app.db.session import engine
from app.models.exchange_rate import Base

async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Currency Exchange tables created successfully!")

if __name__ == "__main__":
    asyncio.run(init_models())
