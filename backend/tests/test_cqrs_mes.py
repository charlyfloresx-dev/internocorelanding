import asyncio
import os
import sys
import uuid
from datetime import datetime

# Add root to pythonpath
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)

# Add specific service paths to pythonpath
mes_service_dir = os.path.join(backend_dir, "mes_service")
sys.path.append(mes_service_dir)

from mes_app.core.handlers.work_order_handler import WorkOrderHandler, CreateWorkOrderCommand
from common.infrastructure.database import AsyncSessionLocal
from common.exceptions import BusinessRuleException
from common.context import request_context
from common.domain.entities.user_context import UserContext
from mes_app.models.work_order import WorkOrder
from sqlalchemy import select

async def run_cqrs_test():
    company_id = uuid.uuid4()
    ctx = UserContext(
        user_id=str(uuid.uuid4()), 
        company_id=company_id,
        trace_id=str(uuid.uuid4()),
        role="OPERATOR",
        role_names=[],
        accessible_warehouses=[]
    )
    token_ctx = request_context.set(ctx)

    print("--- INICIANDO VALIDACION CQRS (MES) ---")
    
    try:
        async with AsyncSessionLocal() as session:
            handler = WorkOrderHandler(session)
            cmd = CreateWorkOrderCommand(
                order_number="WO-TEST-001",
                item_code="SKU-999",
                order_qty=2500, # This should trigger INSUFFICIENT_STOCK (>1000)
                due_date=datetime.now(),
                company_id=company_id
            )
            
            print("[*] Dispatching CreateWorkOrderCommand with order_qty = 2500...")
            try:
                await handler.handle_create(cmd)
                print("[ERROR] El comando debió fallar por INSUFFICIENT_STOCK!")
                return
            except BusinessRuleException as e:
                print(f"[OK] Excepción atrapada correctamente: {e.code} - {e.detail}")
                assert e.code == "INSUFFICIENT_STOCK"
            
            # Verificar si la base de datos permaneció limpia (Rollback exitoso)
            result = await session.execute(select(WorkOrder).where(WorkOrder.order_number == "WO-TEST-001"))
            record = result.scalars().first()
            
            if record is None:
                print("[OK] ROLLBACK CONFIRMADO: La WorkOrder fantasma no existe en BD.")
            else:
                print("[ERROR] Falla Atómica: La WorkOrder se insertó a pesar del error de inventario.")

            print("--- VALIDACION EXITOSA ---")
            
    finally:
        request_context.reset(token_ctx)

if __name__ == "__main__":
    asyncio.run(run_cqrs_test())
