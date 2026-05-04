"""
Script para sincronizar las clases Enum de Python hacia la tabla Enumeration de la Base de Datos.
Convierte los enums hardcodeados en registros globales (company_id IS NULL) para i18n y flexibilidad.

Uso:
PYTHONPATH=/app python scripts/sync_enums.py
"""
import asyncio
import re

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from common.infrastructure.database import SessionLocal
from common.models.enumeration import Enumeration

# Importación de Enums del Shared Kernel
from common.models.work_order_base import (
    WorkOrderType,
    WorkOrderBaseStatus,
    WorkOrderBasePriority,
)

# Importación de Enums específicos del CMMS
from cmms_app.core.constants import (
    AssetCategory,
    AssetCriticality,
    AssetStatus,
    ToolStatus,
    ToolCondition,
    MaintenanceType,
    MaintenanceFrequencyUnit,
    StorageTier,
    QuotaApprovalStatus,
    TransferType,
)

ENUMS_TO_SYNC = [
    WorkOrderType,
    WorkOrderBaseStatus,
    WorkOrderBasePriority,
    AssetCategory,
    AssetCriticality,
    AssetStatus,
    ToolStatus,
    ToolCondition,
    MaintenanceType,
    MaintenanceFrequencyUnit,
    StorageTier,
    QuotaApprovalStatus,
    TransferType,
]

def camel_to_snake(name: str) -> str:
    """Convierte AssetCategory a asset_category."""
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


async def sync_enums_to_db():
    print("Iniciando sincronización de Enums -> Tabla Enumeration...")
    async with SessionLocal() as db:
        for enum_class in ENUMS_TO_SYNC:
            enum_type = camel_to_snake(enum_class.__name__).upper()
            
            for idx, member in enumerate(enum_class):
                key = member.value
                label = key.replace("_", " ").title()
                translation_key = f"enums.{enum_type.lower()}.{key.lower()}"
                
                stmt = insert(Enumeration).values(
                    company_id=None,  # Registro global
                    type=enum_type,
                    key=key,
                    label=label,
                    translation_key=translation_key,
                    sort_order=idx * 10,  # Espaciado para permitir intercalar en el futuro
                    is_active=True
                )
                
                # Upsert: ON CONFLICT DO UPDATE
                stmt = stmt.on_conflict_do_update(
                    index_elements=['type', 'key', 'company_id'],
                    set_={
                        'label': stmt.excluded.label,
                        'translation_key': stmt.excluded.translation_key,
                        'sort_order': stmt.excluded.sort_order,
                        'is_active': stmt.excluded.is_active,
                    }
                )
                
                await db.execute(stmt)
                
        await db.commit()
    print("¡Sincronización completada exitosamente!")

if __name__ == "__main__":
    asyncio.run(sync_enums_to_db())
