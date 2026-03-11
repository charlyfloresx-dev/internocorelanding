import asyncio
import uuid
import logging
import os
import sys

# Adjustment of PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from mes_service.app.db.session import AsyncSessionLocal
from mes_service.app.models.downtime import DowntimeReason
from mes_service.app.models.labor import LaborType
from sqlalchemy import select

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ID DE LA COMPAÑÍA DEMO
COMPANY_A_ID = uuid.UUID("9cd9986b-89da-48b7-8733-26a2a1225b01")
SYSTEM_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")

DOWNTIME_CATEGORIES = {
    "Equipment": [
        "Banda dañada", "Cambio de Rollos", "Equipo Caído", "Falla Eléctrica", 
        "Falta de Herramienta", "Guarda Quebrada", "Herramienta Defectuosa", 
        "Material Atorado", "No Baja Cabezal", "No calienta", "No corta hilo", 
        "Sellado Débil", "Setup", "Sistema de embobinado no funciona", "Sobre Sellado"
    ],
    "Management": ["Sin Plan de Producción"],
    "Material": [
        "Atom Falta de SubEnsamble", "Falta de Insumos", "INDS Discrepancia de Inventario Almacén",
        "INW Discrepancia Inventario WIP", "Lasser Falta de SubEnsamble", 
        "Lectra Falta de SubEnsamble", "Maquinado Falta de SubEnsamble", 
        "Materia Prima Defectuosa", "Materiales no Solicitados a Tiempo", 
        "Moldeo Falta de SubEnsamble", "Pedal/ Botón no funciona", 
        "Prepar Falta de SubEnsamble", "WDL Falta de Surtido de Almacén"
    ],
    "Method": [
        "Método Ineficiente", "Método Inexistente", "Prueba Piloto", 
        "Validación de Equipo", "Validación de Materiales"
    ],
    "Personal": [
        "Auditorías", "Ausencia", "Baños", "Cambio de Módulo", 
        "Despeje/cambio de modelo/Cambio de orden", "Enfermería", 
        "Entrenamiento", "Inventarios", "Juntas", "Recursos Humanos", "Término de Turno"
    ],
    "Service": [
        "Aire Comprimido", "Corriente Eléctrica", "Intranet", "Programa de Computadora"
    ]
}

LABOR_OPTIONS = [
    "Enfermería", "Recursos Humanos", "Auditorías", "Inventarios", 
    "Entrenamiento", "Juntas", "Baños", "Cambio de Módulo", 
    "Ausencia", "Término de Turno", "Falta de Personal", 
    "Espera de Técnico Disponible", "Despeje/cambio de modelo/Cambio de orden"
]

async def seed_fast():
    logger.info("⚡ Running fast MES Industrial Seeding...")
    async with AsyncSessionLocal() as session:
        try:
            # 1. Downtime Reasons
            for category, reasons in DOWNTIME_CATEGORIES.items():
                for reason_name in reasons:
                    stmt = select(DowntimeReason).where(
                        DowntimeReason.name == reason_name, 
                        DowntimeReason.company_id == COMPANY_A_ID
                    )
                    res = await session.execute(stmt)
                    if not res.scalar_one_or_none():
                        code = f"{category[:3].upper()}-{reason_name[:10].replace(' ', '').upper()}"
                        session.add(DowntimeReason(
                            code=code[:20],
                            name=reason_name,
                            category=category,
                            company_id=COMPANY_A_ID,
                            created_by=SYSTEM_USER_ID
                        ))
            
            # 2. Labor Types
            for labor_name in LABOR_OPTIONS:
                stmt = select(LaborType).where(
                    LaborType.name == labor_name,
                    LaborType.company_id == COMPANY_A_ID
                )
                res = await session.execute(stmt)
                if not res.scalar_one_or_none():
                    session.add(LaborType(
                        name=labor_name,
                        description=f"Actividad de {labor_name}",
                        company_id=COMPANY_A_ID,
                        created_by=SYSTEM_USER_ID
                    ))
            
            await session.commit()
            logger.info("✅ Fast MES Industrial Seeding Completed.")
        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(seed_fast())
