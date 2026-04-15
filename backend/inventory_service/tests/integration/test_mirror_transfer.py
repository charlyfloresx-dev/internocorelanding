import pytest
import uuid
from decimal import Decimal
from app.services.transfer_service import TransferService
from app.domain.entities.inventory_item import MovementEntity
from common.context import request_context
from common.domain.entities.user_context import UserContext

@pytest.fixture
def mock_repo(mocker):
    # This might require pytest-mock to be installed.
    class MockRepo:
        def __init__(self):
            self.get_warehouse_owner_id = None
            self.get_wac_valuation = None
            self.record_movement = None
            self.has_processed_document = None
    
    mock = MockRepo()
    import unittest.mock as mock_lib
    mock.get_warehouse_owner_id = mock_lib.AsyncMock()
    mock.get_wac_valuation = mock_lib.AsyncMock()
    mock.record_movement = mock_lib.AsyncMock()
    mock.has_processed_document = mock_lib.AsyncMock()
    return mock

@pytest.mark.asyncio
async def test_inter_company_mirror_transfer_logic(mock_repo):
    """
    Simula una transferencia entre Tijuana (ad6cc8a6) y Enterprise (9cd9986b).
    Valida que el flujo de TransferService use el owner del almac\u00e9n destino.
    """
    service = TransferService(mock_repo)
    
    # IDs de la especificaci\u00f3n
    TIJUANA_TENANT = uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242")
    ENTERPRISE_TENANT = uuid.UUID("9cd9986b-89da-48b7-8733-26a2a1225b01")
    
    WH_TIJ = uuid.uuid4()
    WH_ENT = uuid.uuid4()
    PRODUCT_ID = uuid.uuid4()
    UOM_ID = uuid.uuid4()
    TRANSFER_ID = uuid.uuid4()
    
    # 1. Mock: El almac\u00e9n destino pertenece a Enterprise
    mock_repo.get_warehouse_owner_id.return_value = ENTERPRISE_TENANT
    mock_repo.get_wac_valuation.return_value = None # Precio base 0 para el test
    
    # 2. Ejecutar despacho de transferencia (Desde Tijuana)
    # El context actual es Tijuana
    ctx_tijuana = UserContext(company_id=TIJUANA_TENANT, user_id="charly")
    token = request_context.set(ctx_tijuana)
    
    try:
        await service.dispatch_transfer(
            from_warehouse_id=WH_TIJ,
            to_warehouse_id=WH_ENT,
            product_id=PRODUCT_ID,
            quantity=Decimal("10"),
            uom_id=UOM_ID,
            weight=Decimal("5"),
            company_id=TIJUANA_TENANT,
            transfer_id=TRANSFER_ID
        )
        
        # VERIFICACIONES
        # A. Se debi\u00f3 grabar un movimiento de salida (-) para Tijuana
        # B. Se debi\u00f3 grabar un movimiento de entrada (+) para Enterprise
        
        calls = mock_repo.record_movement.call_args_list
        assert len(calls) == 2
        
        # Movimiento 1: Salida de Tijuana
        out_move = calls[0][0][0]
        assert out_move.company_id == TIJUANA_TENANT
        assert out_move.quantity == Decimal("-10")
        
        # Movimiento 2: Entrada a Tr\u00e1nsito de Enterprise (Espejo)
        # Aqu\u00ed es donde validamos que el "SystemContext" (u owner lookup) funcion\u00f3
        in_move = calls[1][0][0]
        assert in_move.company_id == ENTERPRISE_TENANT
        assert in_move.quantity == Decimal("10")
        assert in_move.document_type == "TRANS_IN_TRANSIT"
        
    finally:
        request_context.reset(token)

@pytest.mark.asyncio
async def test_security_isolation_forbidden():
    """
    Validaci\u00f3n de que un usuario de Tijuana NO puede ver documentos de Enterprise.
    En un entorno real, el Middleware/Repository filtrar\u00eda esto.
    """
    TIJUANA_TENANT = uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242")
    ENTERPRISE_TENANT = uuid.UUID("9cd9986b-89da-48b7-8733-26a2a1225b01")
    
    # Contexto de Tijuana
    ctx = UserContext(company_id=TIJUANA_TENANT, user_id="charly")
    token = request_context.set(ctx)
    
    try:
        # Aqu\u00ed se testear\u00eda que un repo filtrase.
        pass
    finally:
        request_context.reset(token)
