import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from common.config import settings

async def main():
    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    async with engine.begin() as conn:
        await conn.execute(text("UPDATE movement_concepts SET translation_key = 'CONCEPT_PUR_REC' WHERE code = 'PUR-REC';"))
        await conn.execute(text("UPDATE movement_concepts SET translation_key = 'CONCEPT_SAL_DIS' WHERE code = 'SAL-DIS';"))
        await conn.execute(text("UPDATE movement_concepts SET translation_key = 'CONCEPT_INT_TRA' WHERE code = 'INT-TRA';"))
    await engine.dispose()
    print('Translations Updated')

if __name__ == "__main__":
    asyncio.run(main())
