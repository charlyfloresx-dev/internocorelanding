import asyncio
import uuid
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from master_app.models.uom import UOM
from master_app.models.uom_conversion import UOMConversion
from master_app.models.movement_concept import MovementConcept, MovementType
from common.config import settings

# Database setup
engine = create_async_engine(settings.database_url, pool_pre_ping=True)
AsyncSessionLocal = sessionmaker(engine, pool_pre_ping=True, class_=AsyncSession, expire_on_commit=False)

SYSTEM_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")

async def seed_data():
    async with AsyncSessionLocal() as session:
        print("🌱 Seeding Master Data...")
        
        # 1. Seed UOMs
        uoms_data = [
            {"code": "PZ", "name": "Pieza", "abbreviation": "PZ"},
            {"code": "KG", "name": "Kilogramo", "abbreviation": "KG"},
            {"code": "LB", "name": "Libra", "abbreviation": "LB"},
            {"code": "RL", "name": "Rollo", "abbreviation": "RL"},
            {"code": "M", "name": "Metro", "abbreviation": "M"},
            {"code": "FT", "name": "Pie", "abbreviation": "FT"} # Needed for FT->M conversion
        ]
        
        uom_map = {}
        for uom_in in uoms_data:
            uom = UOM(
                id=uuid.uuid4(),
                code=uom_in["code"],
                name=uom_in["name"],
                abbreviation=uom_in["abbreviation"],
                company_id=None, # Global UOMs
                created_by=SYSTEM_USER_ID,
                updated_by=SYSTEM_USER_ID
            )
            session.add(uom)
            uom_map[uom_in["code"]] = uom
        
        await session.flush()
        
        # 2. Seed UOM Conversions
        conversions = [
            {"from": "LB", "to": "KG", "factor": Decimal("0.4535")},
            {"from": "FT", "to": "M", "factor": Decimal("0.3048")}
        ]
        
        for conv in conversions:
            conversion = UOMConversion(
                id=uuid.uuid4(),
                from_uom_id=uom_map[conv["from"]].id,
                to_uom_id=uom_map[conv["to"]].id,
                factor=conv["factor"],
                company_id=None,
                created_by=SYSTEM_USER_ID,
                updated_by=SYSTEM_USER_ID
            )
            session.add(conversion)
            
        # 3. Seed Movement Concepts
        concepts = [
            {"name": "COMPRA", "type": MovementType.ENTRADA, "external": True},
            {"name": "VENTA", "type": MovementType.SALIDA, "external": True},
            {"name": "TRASPASO", "type": MovementType.TRASPASO, "external": False, "target_wh": True}
        ]
        
        for concept_in in concepts:
            concept = MovementConcept(
                id=uuid.uuid4(),
                name=concept_in["name"],
                type=concept_in["type"],
                requires_external_entity=concept_in.get("external", False),
                requires_target_warehouse=concept_in.get("target_wh", False),
                company_id=None, # Default concepts
                created_by=SYSTEM_USER_ID,
                updated_by=SYSTEM_USER_ID
            )
            session.add(concept)
            
        await session.commit()
        print("✅ Master Data Seeding Completed.")

if __name__ == "__main__":
    asyncio.run(seed_data())
