"""
Seed script for default Concepts in WMS Service.
Creates standard inventory operation types for each company.

Run this after the Triple Identity migration is applied.

Usage:
    docker exec wms-service-api python -m scripts.seed_concepts
"""
import asyncio
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import engine
from app.models import Concept, ConceptType, Company
from common.models import Base


async def seed_default_concepts():
    """
    Seeds default concepts for all companies in the database.
    
    Default concepts (mirror of legacy .NET Interno.Inventory):
    - ENT: Entrada de Compra (Entry)
    - SAL: Salida por Venta (Output)
    - AJU: Ajuste de Inventario (Adjustment)
    - TRA: Transferencia entre Almacenes (Adjustment)
    - DEV: Devolución de Cliente (Entry)
    - MER: Merma (Output)
    """
    
    default_concepts = [
        {
            "code": "ENT",
            "name": "Entrada de Compra",
            "description": "Recepción de mercancía de proveedores. Incrementa stock.",
            "concept_type": ConceptType.ENTRY,
            "affect_stock": True
        },
        {
            "code": "SAL",
            "name": "Salida por Venta",
            "description": "Despacho de mercancía a clientes. Decrementa stock.",
            "concept_type": ConceptType.OUTPUT,
            "affect_stock": True
        },
        {
            "code": "AJU",
            "name": "Ajuste de Inventario",
            "description": "Corrección de diferencias por conteo físico. Puede incrementar o decrementar.",
            "concept_type": ConceptType.ADJUSTMENT,
            "affect_stock": True
        },
        {
            "code": "TRA",
            "name": "Transferencia entre Almacenes",
            "description": "Movimiento de mercancía entre ubicaciones. No afecta stock total.",
            "concept_type": ConceptType.ADJUSTMENT,
            "affect_stock": False  # Transfers are handled by paired documents
        },
        {
            "code": "DEV",
            "name": "Devolución de Cliente",
            "description": "Retorno de mercancía vendida. Incrementa stock.",
            "concept_type": ConceptType.ENTRY,
            "affect_stock": True
        },
        {
            "code": "MER",
            "name": "Merma",
            "description": "Pérdida de mercancía por daño, vencimiento o robo. Decrementa stock.",
            "concept_type": ConceptType.OUTPUT,
            "affect_stock": True
        }
    ]
    
    async with AsyncSession(engine) as session:
        # Get all companies
        result = await session.execute(select(Company))
        companies = result.scalars().all()
        
        if not companies:
            print("⚠️  No companies found. Please seed companies first.")
            return
        
        print(f"📦 Seeding default concepts for {len(companies)} companies...")
        
        for company in companies:
            print(f"\n🏢 Company: {company.name} ({company.id})")
            
            for concept_data in default_concepts:
                # Check if concept already exists
                existing = await session.execute(
                    select(Concept).where(
                        (Concept.company_id == company.id) & 
                        (Concept.code == concept_data["code"])
                    )
                )
                
                if existing.scalar_one_or_none():
                    print(f"  ⏭️  Concept '{concept_data['code']}' already exists, skipping...")
                    continue
                
                # Create new concept
                concept = Concept(
                    id=uuid.uuid4(),
                    company_id=company.id,
                    code=concept_data["code"],
                    name=concept_data["name"],
                    description=concept_data["description"],
                    concept_type=concept_data["concept_type"],
                    affect_stock=concept_data["affect_stock"],
                    created_at=datetime.now(timezone.utc),
                    is_active=True,
                    version_id=1
                )
                
                session.add(concept)
                print(f"  ✅ Created concept: {concept.code} - {concept.name}")
            
            await session.commit()
        
        print("\n✅ Default concepts seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed_default_concepts())
