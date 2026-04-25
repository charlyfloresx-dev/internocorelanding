import asyncio
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from asset_app.core.database import AsyncSessionLocal, engine
from asset_app.domain.models.opportunity import ZoneConfig
from common.logger import get_logger

logger = get_logger(__name__)

# Catálogo inicial de colonias estratégicas en Tijuana
# Valores estimados por m2 basados en mercado industrial/residencial actual
TIJUANA_ZONES = [
    {"colonia": "PRESIDENTES", "valor_m2": 4500.00, "municipio": 2},
    {"colonia": "OTAY CONSTITUYENTES", "valor_m2": 6500.00, "municipio": 2},
    {"colonia": "CENTRO", "valor_m2": 12000.00, "municipio": 2},
    {"colonia": "ZONA RIO", "valor_m2": 15000.00, "municipio": 2},
    {"colonia": "EL FLORIDO", "valor_m2": 3500.00, "municipio": 2},
    {"colonia": "VILLA FONTANA", "valor_m2": 4200.00, "municipio": 2},
]

async def seed_zones():
    """
    Puebla el catálogo de zonas de forma idempotente.
    Si la colonia existe, actualiza el valor; si no, la crea.
    """
    logger.info("Iniciando Seed de ZoneConfig (Tijuana)...")
    
    async with AsyncSessionLocal() as session:
        for zone_data in TIJUANA_ZONES:
            # Buscar si ya existe la colonia
            stmt = select(ZoneConfig).where(ZoneConfig.colonia == zone_data["colonia"])
            result = await session.execute(stmt)
            existing_zone = result.scalar_one_or_none()
            
            if existing_zone:
                # Actualizar si el valor cambió
                if float(existing_zone.valor_m2) != zone_data["valor_m2"]:
                    existing_zone.valor_m2 = zone_data["valor_m2"]
                    existing_zone.source = "seed"
                    logger.info(f"Actualizada: {zone_data['colonia']} -> ${zone_data['valor_m2']}")
                else:
                    logger.debug(f"Sin cambios: {zone_data['colonia']}")
            else:
                # Crear nueva zona
                new_zone = ZoneConfig(
                    id=str(uuid.uuid4()),
                    colonia=zone_data["colonia"],
                    valor_m2=zone_data["valor_m2"],
                    municipio=zone_data["municipio"],
                    source="seed"
                )
                session.add(new_zone)
                logger.info(f"Creada: {zone_data['colonia']} -> ${zone_data['valor_m2']}")
        
        await session.commit()
    
    logger.info("Seed de ZoneConfig finalizado con éxito.")

if __name__ == "__main__":
    asyncio.run(seed_zones())
