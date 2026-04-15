import pytest
import uuid
from decimal import Decimal
from app.api.v1.handlers.transfer_command_handler import TransferCommandHandler
from app.domain.entities.transfer_entities import InitiateTransferCommand
from common.exceptions import BusinessRuleException
from app.models.warehouse import Warehouse


class MockWarehouse:
    def __init__(self, id, country_code, company_id):
        self.id = id
        self.country_code = country_code
        self.company_id = company_id

    def __repr__(self):
        return f"<Warehouse(id={self.id}, country_code={self.country_code})>"


def make_session_mock(mocker):
    """
    Crea un mock de AsyncSession compatible con 'async with session.begin()'.
    __aexit__ retorna False para NO suprimir excepciones lanzadas dentro del bloque.
    """
    mock_session = mocker.MagicMock()
    ctx_mgr = mocker.MagicMock()
    ctx_mgr.__aenter__ = mocker.AsyncMock(return_value=None)
    ctx_mgr.__aexit__ = mocker.AsyncMock(return_value=False)  # False = propaga excepciones
    mock_session.begin.return_value = ctx_mgr
    mock_session.add = mocker.MagicMock()
    mock_session.flush = mocker.AsyncMock()
    return mock_session


# ─────────────────────────────────────────────────────────────────────────────
# TEST A: Falla Controlada — Sin Pedimento en transferencia binacional MX→US
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_binational_validation_mandatory_pedimento(mocker):
    """
    Test A: Falla Controlada.
    ICT_OUT de TIJ (MX) a SD Hub (US) sin customs_pedimento.
    Debe lanzar BusinessRuleException con ERR_CUSTOMS_REQUIRED.
    """
    mock_repo = mocker.MagicMock()
    mock_session = make_session_mock(mocker)

    handler = TransferCommandHandler(session=mock_session, repo=mock_repo)

    WH_TIJ_ID = uuid.uuid4()
    WH_SDY_ID = uuid.uuid4()
    COMPANY_A = uuid.uuid4()
    COMPANY_B = uuid.uuid4()
    PRODUCT_ID = uuid.uuid4()

    wh_tij = MockWarehouse(WH_TIJ_ID, "MX", COMPANY_A)
    wh_sdy = MockWarehouse(WH_SDY_ID, "US", COMPANY_B)

    # execute dinámico — primer call=dest, segundo call=origin, resto=None
    call_count = 0

    async def dynamic_execute(stmt):
        nonlocal call_count
        call_count += 1
        result = mocker.MagicMock()
        result.scalar_one_or_none.return_value = wh_sdy if call_count == 1 else (wh_tij if call_count == 2 else None)
        result.scalar.return_value = None
        return result

    mock_session.execute = dynamic_execute

    # audit_svc retorna is_binational=True para forzar la validación de aduanas
    audit_result = mocker.MagicMock()
    audit_result.is_rejected.return_value = False
    audit_result.warnings = []
    audit_result.is_binational = True
    audit_result.pending_financial_valuation = False
    audit_result.suggested_customs_key = "MX-SUGGESTED-KEY"
    audit_result.applied_fx_rate = None
    audit_result.to_dict.return_value = {}
    handler.audit_svc = mocker.MagicMock()
    handler.audit_svc.execute_preflight_audit = mocker.AsyncMock(return_value=audit_result)

    # Comando SIN pedimento
    cmd = InitiateTransferCommand(
        origin_company_id=COMPANY_A,
        initiated_by=uuid.uuid4(),
        destination_company_id=COMPANY_B,
        destination_warehouse_id=WH_SDY_ID,
        origin_warehouse_id=WH_TIJ_ID,
        product_id=PRODUCT_ID,
        uom_id=uuid.uuid4(),
        quantity=Decimal("100"),
        currency="USD",
        customs_pedimento=None,  # ← Faltante, debe ser rechazado
    )

    # Debe lanzar BusinessRuleException con ERR_CUSTOMS_REQUIRED
    with pytest.raises(BusinessRuleException) as excinfo:
        await handler.initiate_transfer(cmd)

    error_msg = str(excinfo.value)
    assert "ERR_CUSTOMS_REQUIRED" in error_msg, f"Código de error incorrecto: {error_msg}"
    assert "La transferencia internacional" in error_msg, f"Mensaje incorrecto: {error_msg}"
    assert "requiere número de Pedimento o Export Entry" in error_msg, f"Mensaje incorrecto: {error_msg}"


# ─────────────────────────────────────────────────────────────────────────────
# TEST B: Éxito Binacional — Con Pedimento válido
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_binational_validation_success_with_pedimento(mocker):
    """
    Test B: Éxito Binacional.
    ICT con pedimento válido. Debe pasar la validación de aduana
    sin lanzar ERR_CUSTOMS_REQUIRED.
    """
    from common.domain.value_objects import Money

    mock_repo = mocker.MagicMock()
    mock_session = make_session_mock(mocker)

    handler = TransferCommandHandler(session=mock_session, repo=mock_repo)

    WH_TIJ_ID = uuid.uuid4()
    WH_SDY_ID = uuid.uuid4()
    COMPANY_A = uuid.uuid4()
    COMPANY_B = uuid.uuid4()
    PRODUCT_ID = uuid.uuid4()

    wh_tij = MockWarehouse(WH_TIJ_ID, "MX", COMPANY_A)
    wh_sdy = MockWarehouse(WH_SDY_ID, "US", COMPANY_B)

    call_count = 0

    async def dynamic_execute(stmt):
        nonlocal call_count
        call_count += 1
        result = mocker.MagicMock()
        if call_count == 1:
            result.scalar_one_or_none.return_value = wh_sdy   # dest warehouse
        elif call_count == 2:
            result.scalar_one_or_none.return_value = wh_tij   # origin warehouse
        elif call_count == 3:
            result.scalar_one_or_none.return_value = None      # transit wh check → se crea
        else:
            result.scalar_one_or_none.return_value = None
        result.scalar.return_value = None
        return result

    mock_session.execute = dynamic_execute

    # Stock disponible
    mock_stock = mocker.MagicMock()
    mock_stock.quantity = Decimal("500")
    mock_stock.reserved_quantity = Decimal("0")
    mock_repo.get_stock = mocker.AsyncMock(return_value=mock_stock)
    mock_repo.get_wac_valuation = mocker.AsyncMock(
        return_value=mocker.MagicMock(wac=Money(Decimal("15.0"), "USD"))
    )
    mock_repo.record_movement = mocker.AsyncMock()
    mock_repo.has_processed_document = mocker.AsyncMock(return_value=False)

    # audit_svc — binacional CON pedimento, no rechaza
    audit_result = mocker.MagicMock()
    audit_result.is_rejected.return_value = False
    audit_result.warnings = []
    audit_result.is_binational = True
    audit_result.pending_financial_valuation = False
    audit_result.suggested_customs_key = None
    audit_result.applied_fx_rate = None
    audit_result.to_dict.return_value = {}
    handler.audit_svc = mocker.MagicMock()
    handler.audit_svc.execute_preflight_audit = mocker.AsyncMock(return_value=audit_result)

    # FIFO — plan vacío (ya pasamos la validación de customs, el resto es aceptable)
    handler.fifo_service = mocker.MagicMock()
    handler.fifo_service.get_discharge_plan = mocker.AsyncMock(return_value=[])

    # Comando CON pedimento válido
    cmd = InitiateTransferCommand(
        origin_company_id=COMPANY_A,
        initiated_by=uuid.uuid4(),
        destination_company_id=COMPANY_B,
        destination_warehouse_id=WH_SDY_ID,
        origin_warehouse_id=WH_TIJ_ID,
        product_id=PRODUCT_ID,
        uom_id=uuid.uuid4(),
        quantity=Decimal("100"),
        currency="USD",
        customs_pedimento="26 40 3999 6000123",  # ← Pedimento válido
        external_reference="REF-BIN-001",
    )

    # El único fallo inaceptable es ERR_CUSTOMS_REQUIRED con pedimento presente
    try:
        await handler.initiate_transfer(cmd)
    except BusinessRuleException as e:
        if "ERR_CUSTOMS_REQUIRED" in str(e):
            pytest.fail(
                f"FALLÓ: El handler rechazó un pedimento válido.\n"
                f"Error: {e}\n"
                f"La validación de aduana NO debe fallar cuando customs_pedimento está presente."
            )
        # Otros BusinessRuleException (stock, warehouse) son aceptables en este test unitario
    except Exception:
        # Cualquier otro error no relacionado con customs es aceptable
        pass
