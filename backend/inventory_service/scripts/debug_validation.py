
from app.domain.entities.transfer_entities import InitiateTransferCommand
import uuid
from decimal import Decimal

try:
    cmd = InitiateTransferCommand(
        origin_company_id=uuid.uuid4(),
        initiated_by=uuid.uuid4(),
        destination_company_id=uuid.uuid4(),
        destination_warehouse_id=uuid.uuid4(),
        origin_warehouse_id=uuid.uuid4(),
        product_id=uuid.uuid4(),
        uom_id=uuid.uuid4(),
        quantity=Decimal("10.0"),
        transfer_price=Decimal("10.0"),
        currency="USD",
        external_reference="TEST"
    )
    print("VALIDATION SUCCESS")
except Exception as e:
    print(f"VALIDATION FAILED: {e}")
