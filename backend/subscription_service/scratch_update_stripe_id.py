import asyncio
from sqlalchemy import text
from app.infrastructure.database import engine
import uuid

async def main():
    try:
        async with engine.begin() as conn:
            # Forzamos un ID de Stripe para el test manual
            await conn.execute(text(
                "UPDATE subscriptions SET stripe_subscription_id = 'sub_test_123' "
                "WHERE company_id = 'ad6cc8a6-34f9-42df-8f29-28254e0ad242'"
            ))
        print("✅ Stripe Subscription ID updated for test company.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
