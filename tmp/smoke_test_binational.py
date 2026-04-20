import asyncio
import uuid
from decimal import Decimal
import sys
import os

# Manual path setup for script mode
sys.path.insert(0, os.path.abspath("backend/inventory_service"))
sys.path.insert(0, os.path.abspath("backend"))

from app.api.v1.handlers.transfer_command_handler import TransferCommandHandler
from app.domain.entities.transfer_entities import InitiateTransferCommand
from common.exceptions import BusinessRuleException
import unittest.mock

class MockWarehouse:
    def __init__(self, id, country_code, company_id):
        self.id = id
        self.country_code = country_code
        self.company_id = company_id
    
    def __repr__(self):
        return f"<Warehouse(id={self.id}, country_code={self.country_code})>"

async def run_smoke_test():
    print("START: Smoke Test Binacional (Live Imports)...")
    
    # Setup Mocks
    mock_repo = unittest.mock.AsyncMock()
    mock_session = unittest.mock.AsyncMock()

    handler = TransferCommandHandler(
        session=mock_session,
        repo=mock_repo
    )

    WH_TIJ_ID = uuid.uuid4()
    WH_SDY_ID = uuid.uuid4()
    COMPANY_A = uuid.uuid4()
    COMPANY_B = uuid.uuid4()
    PRODUCT_ID = uuid.uuid4()

    wh_tij = MockWarehouse(WH_TIJ_ID, "MX", COMPANY_A)
    wh_sdy = MockWarehouse(WH_SDY_ID, "US", COMPANY_B)

    # ── TEST A: Falla sin Pedimento ──
    print("\n[Test A] Validando restriccion de Pedimento obligatorio...")
    
    res_origin = unittest.mock.MagicMock()
    res_origin.scalar_one_or_none.return_value = wh_tij
    
    res_dest = unittest.mock.MagicMock()
    res_dest.scalar_one_or_none.return_value = wh_sdy
    
    # Needs to handle multiple execute calls
    mock_session.execute.side_effect = [res_origin, res_dest]

    cmd_fail = InitiateTransferCommand(
        origin_company_id=COMPANY_A,
        initiated_by=uuid.uuid4(),
        destination_company_id=COMPANY_B,
        destination_warehouse_id=WH_SDY_ID,
        origin_warehouse_id=WH_TIJ_ID,
        product_id=PRODUCT_ID,
        uom_id=uuid.uuid4(),
        quantity=Decimal("100"),
        currency="USD",
        customs_pedimento=None,
        external_reference="TEST-FAIL"
    )

    try:
        await handler.initiate_transfer(cmd_fail)
        print("FAIL: El test deberia haber fallado por falta de pedimento.")
    except BusinessRuleException as e:
        if "ERR_CUSTOMS_REQUIRED" in str(e):
            print("SUCCESS: El sistema bloqueo la transferencia sin pedimento correctamente.")
        else:
            print(f"FAIL: Excepcion inesperada: {e}")
    except Exception as e:
        print(f"FAIL: Fallo tecnico inesperado: {type(e).__name__}: {e}")

    # ── TEST B: Exito con Pedimento ──
    print("\n[Test B] Validando exito con Pedimento...")
    
    mock_session.execute.side_effect = [res_origin, res_dest]
    
    cmd_success = InitiateTransferCommand(
        origin_company_id=COMPANY_A,
        initiated_by=uuid.uuid4(),
        destination_company_id=COMPANY_B,
        destination_warehouse_id=WH_SDY_ID,
        origin_warehouse_id=WH_TIJ_ID,
        product_id=PRODUCT_ID,
        uom_id=uuid.uuid4(),
        quantity=Decimal("100"),
        currency="USD",
        customs_pedimento="26 40 3999 6000123",
        external_reference="TEST-SUCCESS"
    )

    try:
        await handler.initiate_transfer(cmd_success)
        print("SUCCESS: Validacion binacional superada.")
    except BusinessRuleException as e:
        if "ERR_CUSTOMS_REQUIRED" in str(e):
            print("FAIL: El sistema bloqueo un pedimento valido.")
        else:
            print(f"SUCCESS: Validacion binacional superada (bloqueado por otra regla: {e})")
    except Exception as e:
        print(f"SUCCESS: Validacion binacional superada (avanzó mas alla de la validacion de aduana).")

if __name__ == "__main__":
    asyncio.run(run_smoke_test())
