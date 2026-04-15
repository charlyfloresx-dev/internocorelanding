import asyncio
import uuid
import os
import sys
from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
DATABASE_URL = str(settings.database_url)

async def force_companies():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        print("🔨 [FIX] Re-creando tabla local de compañías y poblando datos (Schema Recovery)...")
        
        # 1. Re-create the table if CASCADE drop removed it (it did)
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS companies (
                id UUID PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                tax_id VARCHAR(50),
                domain VARCHAR(255),
                logo VARCHAR(500),
                country_code VARCHAR(2) NOT NULL DEFAULT 'MX',
                parent_group_id UUID,
                status VARCHAR(50) DEFAULT 'ACTIVE',
                base_currency VARCHAR(3) NOT NULL DEFAULT 'USD',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE,
                created_by UUID,
                updated_by UUID,
                deleted_at TIMESTAMP WITH TIME ZONE,
                transaction_id UUID,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                version_id INTEGER NOT NULL DEFAULT 1
            );
        """))
        
        # 2. SEED IDs (from master_seed.py)
        companies = [
            ("9cd9986b-89da-48b7-8733-26a2a1225b01", "InternoCorp Enterprise"),
            ("ad6cc8a6-34f9-42df-8f29-28254e0ad242", "Interno Logistics MX"),
            ("777cc8a6-34f9-42df-8f29-28254e0ad277", "Interno Logistics US")
        ]
        
        for cid, name in companies:
            print(f"   [+] Seeding {name} ({cid})")
            await conn.execute(text("""
                INSERT INTO companies (id, name, status, country_code, is_active, version_id)
                VALUES (:id, :name, 'ACTIVE', 'MX', TRUE, 1)
                ON CONFLICT (id) DO NOTHING;
            """), {"id": cid, "name": name})
            
        print("✅ [FIX] Companies logic restored and seeded!")

if __name__ == "__main__":
    asyncio.run(force_companies())
