import pytest
import uuid
from datetime import datetime, time, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from mes_app.services.shift_service import ShiftService
from mes_app.services.scanner_service import ScannerService, _MULTI_COUNT_PATTERN
from mes_app.services.kpi_service import KPIService
from mes_app.models.downtime import Downtime


# ── ShiftService ──────────────────────────────────────────────────────────────

def test_midnight_shift_resolution():
    """Turno nocturno 22:00–06:00: escaneo a las 00:30 cae dentro del turno."""
    assert ShiftService.is_time_in_shift(time(0, 30),  time(22, 0), time(6, 0), True)  is True
    assert ShiftService.is_time_in_shift(time(23, 0),  time(22, 0), time(6, 0), True)  is True
    assert ShiftService.is_time_in_shift(time(5, 59),  time(22, 0), time(6, 0), True)  is True
    assert ShiftService.is_time_in_shift(time(12, 0),  time(22, 0), time(6, 0), True)  is False


def test_daytime_shift_boundary():
    """Turno diurno 08:00–16:00: límites inclusivos."""
    assert ShiftService.is_time_in_shift(time(8, 0),  time(8, 0), time(16, 0), False) is True
    assert ShiftService.is_time_in_shift(time(16, 0), time(8, 0), time(16, 0), False) is True
    assert ShiftService.is_time_in_shift(time(7, 59), time(8, 0), time(16, 0), False) is False


# ── ScannerService — multiplicador ───────────────────────────────────────────

def test_multi_count_pattern_parses_qty_and_sku():
    """_MULTI_COUNT_PATTERN extrae qty y SKU de '5*ITEM-001'."""
    m = _MULTI_COUNT_PATTERN.match("5*ITEM-001")
    assert m is not None
    assert m.group(1) == "5"
    assert m.group(2) == "ITEM-001"


def test_multi_count_pattern_no_match_without_asterisk():
    """`_MULTI_COUNT_PATTERN` no coincide con SKU sin multiplicador."""
    assert _MULTI_COUNT_PATTERN.match("ITEM-001") is None


# ── KPIService — _get_total_downtime ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_total_downtime_sums_closed_events():
    """_get_total_downtime suma duración de paros cerrados."""
    run_repo    = AsyncMock()
    ledger_repo = AsyncMock()
    labor_repo  = AsyncMock()
    goal_repo   = AsyncMock()
    downtime_repo = AsyncMock()

    now = datetime.now()
    dt1 = MagicMock(spec=Downtime)
    dt1.start_at   = now - timedelta(minutes=30)
    dt1.closed_at  = now - timedelta(minutes=10)  # 20 min

    dt2 = MagicMock(spec=Downtime)
    dt2.start_at   = now - timedelta(minutes=10)
    dt2.closed_at  = now                           # 10 min

    downtime_repo.get_by_run_id = AsyncMock(return_value=[dt1, dt2])

    svc = KPIService(run_repo, ledger_repo, downtime_repo, labor_repo, goal_repo)
    total = await svc._get_total_downtime(uuid.uuid4())

    assert pytest.approx(total, abs=0.5) == 30.0


@pytest.mark.asyncio
async def test_get_total_downtime_open_event_uses_now():
    """_get_total_downtime usa datetime.now() para paros aún abiertos (closed_at=None)."""
    run_repo    = AsyncMock()
    ledger_repo = AsyncMock()
    labor_repo  = AsyncMock()
    goal_repo   = AsyncMock()
    downtime_repo = AsyncMock()

    now = datetime.now()
    dt_open = MagicMock(spec=Downtime)
    dt_open.start_at  = now - timedelta(minutes=15)
    dt_open.closed_at = None  # evento abierto

    downtime_repo.get_by_run_id = AsyncMock(return_value=[dt_open])

    svc = KPIService(run_repo, ledger_repo, downtime_repo, labor_repo, goal_repo)
    total = await svc._get_total_downtime(uuid.uuid4())

    assert total >= 14.9  # al menos 15 min (tolerancia de ejecución)
