import pytest
import uuid
from decimal import Decimal
from inventory_app.api.v1.handlers.transfer_command_handler import TransferCommandHandler
from inventory_app.infrastructure.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository
from inventory_app.domain.entities.transfer_entities import (
    InitiateTransferCommand, 
    CompleteTransferCommand,
    TransferStatusEnum
)
from common.exceptions import SelfTransferReceiptException, UnauthorizedException
from inventory_app.models.inventory import InventoryLevel
from inventory_app.models.warehouse import Warehouse

@pytest.mark.asyncio
async def test_ict_anti_fraud_handshake(db_session):
    """
    Test del protocolo Anti-Fraude ICT:
    1. test_self_reception_blocked: Usuario A no puede recibir lo que él mismo envió.
    2. test_cross_user_reception_success: Usuario B sí puede recibir lo que envió Usuario A.
    3. test_stolen_identity_multitenancy: Empresa C no puede ver ni recibir lo de Empresa B.
    """
    repo = SQLAlchemyInventoryRepository(db_session)
    handler = TransferCommandHandler(session=db_session, repo=repo)
    
    # ── Datos de Prueba ──
    company_a_id = uuid.uuid4()
    company_b_id = uuid.uuid4()
    company_c_id = uuid.uuid4()
    
    user_a_id = uuid.uuid4()
    user_b_id = uuid.uuid4()
    user_c_id = uuid.uuid4()
    
    warehouse_a_id = uuid.uuid4()
    warehouse_b_id = uuid.uuid4()
    product_id = uuid.uuid4()
    uom_id = uuid.uuid4()
    
    # Preparar Almacén A con Stock
    wh_a = Warehouse(id=warehouse_a_id, company_id=company_a_id, code="WH-A", name="Origin")
    db_session.add(wh_a)
    
    # Preparar Almacén B en Empresa B
    wh_b = Warehouse(id=warehouse_b_id, company_id=company_b_id, code="WH-B", name="Destination")
    db_session.add(wh_b)
    
    item_a = InventoryLevel(
        id=uuid.uuid4(),
        company_id=company_a_id,
        warehouse_id=warehouse_a_id,
        product_id=product_id,
        quantity=Decimal("100.0"),
        uom_id=uom_id
    )
    db_session.add(item_a)
    await db_session.flush()
    
    # ── 1. Iniciar Transferencia (Empresa A -> Empresa B) ──
    init_cmd = InitiateTransferCommand(
        origin_company_id=company_a_id,
        initiated_by=user_a_id,
        destination_company_id=company_b_id,
        destination_warehouse_id=warehouse_b_id,
        origin_warehouse_id=warehouse_a_id,
        product_id=product_id,
        uom_id=uom_id,
        quantity=Decimal("10.0"),
        transfer_price=Decimal("50.0"),
        currency="USD"
    )
    
    transfer_doc = await handler.initiate_transfer(init_cmd)
    assert transfer_doc.status == TransferStatusEnum.SHIPPED
    
    # ── SCENARIO 1: Block Self-Receipt ──
    # Usuario A intenta recibir su propio despacho
    receive_self_cmd = CompleteTransferCommand(
        receiver_company_id=company_b_id,
        received_by=user_a_id, # MISMO USER ID que inició (created_by)
        transfer_id=transfer_doc.id
    )
    
    # Forzar que el created_by del doc sea user_a_id (ya lo es por initiate)
    with pytest.raises(SelfTransferReceiptException) as excinfo:
        await handler.complete_transfer(receive_self_cmd)
    assert "ERR_SELF_RECEIPT_NOT_ALLOWED" in str(excinfo.value)

    # ── SCENARIO 2: Stolen Identity (Multitenancy) ──
    # Empresa C intenta recibir un traspaso dirigido a Empresa B
    receive_stolen_cmd = CompleteTransferCommand(
        receiver_company_id=company_c_id, # EMPRESA EQUIVOCADA
        received_by=user_c_id,
        transfer_id=transfer_doc.id
    )
    
    with pytest.raises(UnauthorizedException) as excinfo:
        await handler.complete_transfer(receive_stolen_cmd)
    assert "ERR_UNAUTHORIZED_RECEIVER" in str(excinfo.value)

    # ── SCENARIO 3: Cross-User Success (The Handshake) ──
    # Usuario B recibe el despacho del Usuario A
    receive_ok_cmd = CompleteTransferCommand(
        receiver_company_id=company_b_id,
        received_by=user_b_id, # DIFERENTE USER ID
        transfer_id=transfer_doc.id
    )
    
    result = await handler.complete_transfer(receive_ok_cmd)
    assert result.status == TransferStatusEnum.DELIVERED
    assert result.received_quantity == Decimal("10.0")
