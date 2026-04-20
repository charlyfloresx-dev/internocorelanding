import asyncio
from app.core.database import engine
from app.models.package import TravelPackage
from app.models.group import TravelerGroup
from app.models.itinerary import ItineraryItem
from app.models.payment_history import PaymentHistory
from app.models.price_alert import PriceAlert
from common.models import Base

async def create_tables():
    print("⏳ Registrando tablas en viatra_db...")
    async with engine.begin() as conn:
        # Import models here to register them with Base
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tablas creadas exitosamente.")

if __name__ == "__main__":
    asyncio.run(create_tables())
