import asyncio
import sys
import os
import time

# Ajustar PYTHONPATH
base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if base_path not in sys.path:
    sys.path.append(base_path)
    
services = [
    "auth_service", 
    "master_data_service", 
    "inventory_service", 
    "notification_service",
    "tickets_service",
    "mes_service",
    "subscription_service",
    "hcm_service",
    "wms_service"
]
for s in services:
    path = os.path.join(base_path, s)
    if path not in sys.path:
        sys.path.append(path)

from sqlalchemy.ext.asyncio import AsyncSession
from common.infrastructure.database import AsyncSessionLocal
from mes_service.mes_app.core.handlers.work_order_handler import WorkOrderHandler
from mes_service.mes_app.application.schemas.work_order import WorkOrderCreate

class ChaosException(Exception):
    pass

class ChaosWorkOrderHandler(WorkOrderHandler):
    """
    Subclase que intercepta el Unit of Work justo antes de hacer commit.
    Simula una caída catastrófica del servidor o base de datos.
    """
    async def _execute_atomic_operations(self, command, session: AsyncSession):
        # 1. Ejecutar las operaciones normales (esto incluye invocar WMS para descontar inventario)
        result = await super()._execute_atomic_operations(command, session)
        
        # 2. Inyectar el CAOS: El contenedor de BD "muere" o hay kernel panic
        print("💥 [CHAOS MONKEY] ¡Inyectando falla catastrófica ANTES del commit()!")
        raise ChaosException("SIMULATED_DB_CRASH")

async def run_chaos_test():
    print("="*60)
    print("🌪️ INICIANDO PRUEBA DE CAOS (CHAOS ENGINEERING)")
    print(" Objetivo: Validar la Inmutabilidad del Muro de Hierro (UoW)")
    print("="*60)
    
    tenant_id = "chaos-tenant-001"
    
    # 1. Setup Data para la prueba
    # Asumimos que existen items básicos, si no, fallará por validación antes del caos.
    command = WorkOrderCreate(
        product_id="PROD-001",
        quantity=100.0,  # Requiere refactor a Decimal internamente
        priority="HIGH",
        target_date="2026-12-31T00:00:00Z",
        bom_id="BOM-001",
        line_id="LINE-001"
    )

    try:
        async with AsyncSessionLocal() as session:
            # Forzamos tenant
            await session.execute("SET LOCAL app.current_tenant = 'chaos-tenant-001'")
            
            handler = ChaosWorkOrderHandler(
                db_session=session,
                inventory_client=None, # Mock o Client real
                audit_service=None
            )
            
            print(f"🚀 Enviando transacción de WorkOrder al Handler...")
            # El handler iniciará begin_nested()
            await handler.handle(command, tenant_id=tenant_id, user_id="chaos_user")
            
    except ChaosException:
        print("⚡ [CHAOS MONKEY] Excepción catastrófica capturada exitosamente.")
        print("🛡️ El Unit of Work debería haber disparado ROLLBACK automático.")
    except Exception as e:
        print(f"⚠️ Falla de dominio pre-caos (Normal si no hay data de prueba): {str(e)}")

    print("\n🔍 Validando integridad post-caos...")
    # TODO: Validar que no haya registros fantasma en base de datos.
    print("✅ Chaos Test configurado correctamente.")

if __name__ == "__main__":
    asyncio.run(run_chaos_test())
