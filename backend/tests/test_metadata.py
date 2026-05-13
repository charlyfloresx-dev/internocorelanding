import sys
import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

# Simula env.py setup
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, "mes_service"))

from common.infrastructure.models.base import Base
import app.models 

print("Tabelas registradas em Base.metadata:", list(Base.metadata.tables.keys()))

async def check_db():
    url = "postgresql+asyncpg://user:password@localhost:5432/mes_db"
    try:
        engine = create_async_engine(url, pool_pre_ping=True)
        async with engine.connect() as conn:
            print("Conn OK")
            # Podemos fazer queries aqui se estiver conectado
    except Exception as e:
        print("Erro de DB:", e)

if __name__ == "__main__":
    asyncio.run(check_db())
