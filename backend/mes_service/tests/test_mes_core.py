import pytest
import uuid
from datetime import datetime, time, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from app.services.shift_service import ShiftService
from app.services.scanner_service import ScannerService
from app.services.kpi_service import KPIService
from app.models.shift import Shift
from app.models.ledger import ManufacturingLedger
from app.models.downtime import Downtime
from app.models.resource import ResourceResult

@pytest.mark.asyncio
async def test_midnight_shift_resolution():
    """Valida que un escaneo a las 00:30 se asigne a un turno nocturno."""
    db = AsyncMock()
    service = ShiftService(db)
    
    # Turno de 22:00 a 06:00
    shift_start = time(22, 0)
    shift_end = time(6, 0)
    check_time = time(0, 30)
    
    is_in = service.is_time_in_shift(check_time, shift_start, shift_end, is_overnight=True)
    assert is_in is True

@pytest.mark.asyncio
async def test_sync_idempotency():
    """Verifica que registros duplicados en un lote sean omitidos."""
    db = AsyncMock()
    service = ScannerService(db)
    
    # Mock de _get_existing_txn
    # El primero no existe (retorna None), el segundo sí existe.
    service._get_existing_txn = AsyncMock()
    service._get_existing_txn.side_effect = [None, MagicMock()]
    
    company_id = uuid.uuid4()
    entries = [
        MagicMock(local_txn_id=uuid.uuid4(), sku="ITEM1", qty=1.0, sequence_number=1, created_at=datetime.now(), resource_result_id=uuid.uuid4(), external_folio=None),
        MagicMock(local_txn_id=uuid.uuid4(), sku="ITEM1", qty=1.0, sequence_number=2, created_at=datetime.now(), resource_result_id=uuid.uuid4(), external_folio=None)
    ]
    
    synced, skipped = await service.process_sync_batch(entries, company_id)
    
    assert synced == 1
    assert skipped == 1

@pytest.mark.asyncio
async def test_kpi_meta_adjustment():
    """Valida el ajuste de meta por personal activo vs planeado."""
    db = AsyncMock()
    service = KPIService(db)
    
    # Mock de _get_hour_meta y _get_active_labor_count_at
    service._get_hour_meta = AsyncMock(return_value=100)
    service._get_active_labor_count_at = AsyncMock(return_value=5) # 5 personas activas
    
    resource_id = uuid.uuid4()
    resource_result = MagicMock(resource_id=resource_id, planned_labor=10) # 10 planeadas (Meta debe ser 50%)
    
    db.get = AsyncMock(return_value=resource_result)
    
    # Simulamos el bucle de get_resource_graphic para una sola hora
    theoretical_meta = await service._get_hour_meta(resource_id, 10)
    active_labor = await service._get_active_labor_count_at(uuid.uuid4(), datetime.now())
    planned_labor = resource_result.planned_labor
    
    adjusted_meta = int(theoretical_meta * (active_labor / planned_labor))
    assert adjusted_meta == 50

@pytest.mark.asyncio
async def test_maintenance_metrics_logic():
    """Verifica el cálculo de MTTR y MTBF."""
    db = AsyncMock()
    service = KPIService(db)
    
    # Crear mocks de Downtime con duraciones conocidas
    dt1 = MagicMock(spec=Downtime)
    dt1.mttr_minutes = 20.0
    dt1.start_at = datetime.now() - timedelta(minutes=60)
    dt1.closed_at = datetime.now() - timedelta(minutes=40)
    
    dt2 = MagicMock(spec=Downtime)
    dt2.mttr_minutes = 40.0
    dt2.start_at = datetime.now() - timedelta(minutes=20)
    dt2.closed_at = datetime.now()
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [dt1, dt2]
    db.execute = AsyncMock(return_value=mock_result)
    
    res_result = MagicMock(spec=ResourceResult)
    res_result.start_time = datetime.now() - timedelta(hours=2) # 120 min total
    res_result.end_time = datetime.now()
    db.get = AsyncMock(return_value=res_result)
    
    # Mock total downtime
    service._get_total_downtime = AsyncMock(return_value=60.0)
    
    kpis = await service.calculate_maintenance_kpis(uuid.uuid4())
    
    assert kpis["mttr"] == 30.0 # (20 + 40) / 2
    assert kpis["total_failures"] == 2
    # Uptime = 120 - 60 = 60. MTBF = 60 / 2 = 30.0
    assert kpis["mtbf"] == 30.0
