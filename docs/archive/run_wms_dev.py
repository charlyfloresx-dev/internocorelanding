import uvicorn
import os
import sys

# Standard paths for WMS
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "backend", "wms_service")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))

# Force SQLite for local API verification if Postgres is not available
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./wms_api_test.db"

if __name__ == "__main__":
    from app.core.database import engine
    from app.models import Base
    from common.models import BaseEntity, AuditBase
    from sqlalchemy.orm import Mapped, mapped_column
    from sqlalchemy import String
    import asyncio

    # Temporary Company model for SQLite constraint satisfaction
    class Company(Base, BaseEntity, AuditBase):
        __tablename__ = "companies"
        name: Mapped[str] = mapped_column(String(100))

    async def init_db():
        async with engine.begin() as conn:
            # Drop everything to start fresh
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        print("✅ SQLite Database initialized for API test.")

    # Run init_db synchronously
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_db())

    print("🚀 Starting WMS Dev Server on port 8001...")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8001, reload=False)
