"""
UC-MES-SEED-156: MES Config Seed — Phase 156-A

Validates against real mes_db (PostgreSQL):
  - seed_mes_config() creates Facility for all 3 companies
  - seed_mes_config() creates 3 ProductionAreas per company
  - seed_mes_config() creates 4 Resources per company with correct types
  - seed_mes_config() creates 3 Shifts per company with correct times
  - seed_mes_config() creates 2 ShiftBreaks per shift with duration_minutes
  - seed_mes_config() creates 5 StandardTimes per company
  - seed_mes_config() is idempotent (second run produces 0 new rows)
  - Shift codes are unique per (company_id, code) after migration 010
"""
import uuid
import pytest
from datetime import time
from sqlalchemy import select, func

from mes_app.models.facility import Facility
from mes_app.models.production_area import ProductionArea
from mes_app.models.resource import Resource
from mes_app.models.shift import Shift
from mes_app.models.shift_break import ShiftBreak
from mes_app.models.standard_time import StandardTime

# Import the seed function (runs against real mes_db via conftest engine)
import sys, os
_scripts_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "scripts")
)
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)


ENTERPRISE_ID   = uuid.UUID("9cd9986b-89da-48b7-8733-26a2a1225b01")
LOGISTICS_MX_ID = uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242")
LOGISTICS_US_ID = uuid.UUID("777cc8a6-34f9-42df-8f29-28254e0ad277")

ALL_COMPANY_IDS = [ENTERPRISE_ID, LOGISTICS_MX_ID, LOGISTICS_US_ID]

_NS = uuid.NAMESPACE_DNS


def _uid(*parts: object) -> uuid.UUID:
    return uuid.uuid5(_NS, "mes156." + ".".join(str(p) for p in parts))


# ── Fixtures ─────────────────────────────────────────────────────────────────
# seed_mes_config.py already ran at container startup (entrypoint.sh → seed.py).
# Tests query the existing committed data — no re-run needed here.

@pytest.fixture()
async def seeded_db(db_session):
    """Yield db_session with existing seed data already committed at container startup."""
    yield db_session


# ── Facility ──────────────────────────────────────────────────────────────────

async def test_seed_creates_facility_for_enterprise(seeded_db):
    fac_id = _uid("facility", ENTERPRISE_ID, "PLT-TIJ")
    fac = await seeded_db.get(Facility, fac_id)
    assert fac is not None
    assert fac.code == "PLT-TIJ"
    assert fac.name == "Planta Tijuana"
    assert fac.company_id == ENTERPRISE_ID


async def test_seed_creates_facility_for_all_companies(seeded_db):
    expected = [
        (ENTERPRISE_ID,   "PLT-TIJ"),
        (LOGISTICS_MX_ID, "PLT-MXC"),
        (LOGISTICS_US_ID, "PLT-SDG"),
    ]
    for company_id, code in expected:
        fac_id = _uid("facility", company_id, code)
        fac = await seeded_db.get(Facility, fac_id)
        assert fac is not None, f"Facility {code} not found for {company_id}"
        assert fac.code == code


# ── ProductionArea ────────────────────────────────────────────────────────────

async def test_seed_creates_3_areas_per_company(seeded_db):
    for company_id in ALL_COMPANY_IDS:
        result = await seeded_db.execute(
            select(func.count()).select_from(ProductionArea)
            .where(ProductionArea.company_id == company_id)
        )
        count = result.scalar_one()
        assert count == 3, f"Expected 3 areas for {company_id}, got {count}"


async def test_seed_areas_linked_to_facility(seeded_db):
    fac_id = _uid("facility", ENTERPRISE_ID, "PLT-TIJ")
    result = await seeded_db.execute(
        select(ProductionArea)
        .where(ProductionArea.company_id == ENTERPRISE_ID,
               ProductionArea.facility_id == fac_id)
    )
    areas = result.scalars().all()
    assert len(areas) == 3
    area_names = {a.name for a in areas}
    assert "Líneas de Ensamble" in area_names
    assert "Área de Calidad" in area_names
    assert "Almacén WIP" in area_names


# ── Resource ──────────────────────────────────────────────────────────────────

async def test_seed_creates_4_resources_per_company(seeded_db):
    for company_id in ALL_COMPANY_IDS:
        result = await seeded_db.execute(
            select(func.count()).select_from(Resource)
            .where(Resource.company_id == company_id)
        )
        count = result.scalar_one()
        assert count == 4, f"Expected 4 resources for {company_id}, got {count}"


async def test_seed_enterprise_resources_have_correct_codes(seeded_db):
    expected_codes = {"CELDA-58D", "CELDA-59A", "TURRET-01", "PRENSA-01"}
    result = await seeded_db.execute(
        select(Resource).where(Resource.company_id == ENTERPRISE_ID)
    )
    resources = result.scalars().all()
    actual_codes = {r.code for r in resources}
    assert actual_codes == expected_codes


async def test_seed_resources_have_resource_type(seeded_db):
    result = await seeded_db.execute(
        select(Resource).where(Resource.company_id == ENTERPRISE_ID)
    )
    resources = result.scalars().all()
    for r in resources:
        assert r.resource_type in {"CELL", "MACHINE", "AREA", "LINE"}, \
            f"Resource {r.code} has invalid type {r.resource_type}"


async def test_seed_resources_linked_to_first_area(seeded_db):
    first_area_id = _uid("area", ENTERPRISE_ID, "Líneas de Ensamble")
    result = await seeded_db.execute(
        select(Resource).where(Resource.company_id == ENTERPRISE_ID)
    )
    resources = result.scalars().all()
    for r in resources:
        assert r.production_area_id == first_area_id, \
            f"Resource {r.code} not linked to Líneas de Ensamble"


# ── Shift ──────────────────────────────────────────────────────────────────────

async def test_seed_creates_3_shifts_per_company(seeded_db):
    for company_id in ALL_COMPANY_IDS:
        result = await seeded_db.execute(
            select(func.count()).select_from(Shift)
            .where(Shift.company_id == company_id)
        )
        count = result.scalar_one()
        assert count == 3, f"Expected 3 shifts for {company_id}, got {count}"


async def test_seed_matutino_shift_times(seeded_db):
    mat_id = _uid("shift", ENTERPRISE_ID, "MAT")
    shift = await seeded_db.get(Shift, mat_id)
    assert shift is not None
    assert shift.start_time == time(6, 0)
    assert shift.end_time == time(14, 0)
    assert shift.is_overnight is False
    assert shift.break_minutes == 60


async def test_seed_nocturno_shift_is_overnight(seeded_db):
    noc_id = _uid("shift", ENTERPRISE_ID, "NOC")
    shift = await seeded_db.get(Shift, noc_id)
    assert shift is not None
    assert shift.start_time == time(22, 0)
    assert shift.end_time == time(6, 0)
    assert shift.is_overnight is True


async def test_seed_shift_codes_are_company_scoped(seeded_db):
    """Companies MAT/VES/NOC codes can coexist after migration 010."""
    for company_id in ALL_COMPANY_IDS:
        mat_id = _uid("shift", company_id, "MAT")
        shift = await seeded_db.get(Shift, mat_id)
        assert shift is not None, f"MAT shift not found for company {company_id}"
        assert shift.company_id == company_id


# ── ShiftBreak ────────────────────────────────────────────────────────────────

async def test_seed_creates_2_breaks_per_shift(seeded_db):
    mat_id = _uid("shift", ENTERPRISE_ID, "MAT")
    result = await seeded_db.execute(
        select(func.count()).select_from(ShiftBreak)
        .where(ShiftBreak.shift_id == mat_id)
    )
    count = result.scalar_one()
    assert count == 2


async def test_seed_break_has_duration_minutes(seeded_db):
    mat_id = _uid("shift", ENTERPRISE_ID, "MAT")
    result = await seeded_db.execute(
        select(ShiftBreak).where(ShiftBreak.shift_id == mat_id)
    )
    breaks = result.scalars().all()
    for b in breaks:
        assert b.duration_minutes == 30
        assert b.break_type in {"BREAK", "MEAL"}
        assert b.start_time < b.end_time


async def test_seed_total_breaks_across_all_companies(seeded_db):
    # 3 companies × 3 shifts × 2 breaks = 18 total breaks
    expected = 3 * 3 * 2
    result = await seeded_db.execute(
        select(func.count()).select_from(ShiftBreak)
        .where(ShiftBreak.company_id.in_(ALL_COMPANY_IDS))
    )
    count = result.scalar_one()
    assert count == expected, f"Expected {expected} total breaks, got {count}"


# ── StandardTime ──────────────────────────────────────────────────────────────

async def test_seed_creates_5_standard_times_per_company(seeded_db):
    for company_id in ALL_COMPANY_IDS:
        result = await seeded_db.execute(
            select(func.count()).select_from(StandardTime)
            .where(StandardTime.company_id == company_id)
        )
        count = result.scalar_one()
        assert count == 5, f"Expected 5 StandardTimes for {company_id}, got {count}"


async def test_seed_standard_times_have_correct_skus(seeded_db):
    expected_skus = {"ECM-600", "TRB-700", "BRK-800", "FLI-900", "SUS-100"}
    result = await seeded_db.execute(
        select(StandardTime).where(StandardTime.company_id == ENTERPRISE_ID)
    )
    times = result.scalars().all()
    actual_skus = {t.item_code for t in times}
    assert actual_skus == expected_skus


async def test_seed_standard_times_have_cycle_time_seconds(seeded_db):
    result = await seeded_db.execute(
        select(StandardTime).where(StandardTime.company_id == ENTERPRISE_ID)
    )
    times = result.scalars().all()
    for t in times:
        assert t.cycle_time_seconds is not None
        assert t.cycle_time_seconds > 0
        assert t.set_time_hours > 0


# ── Idempotency ───────────────────────────────────────────────────────────────

async def test_seed_is_idempotent(seeded_db):
    """Running the seed twice must not raise and must not duplicate rows."""
    import sys, os as _os
    _scripts = _os.path.abspath(
        _os.path.join(_os.path.dirname(__file__), "..", "..", "scripts")
    )
    if _scripts not in sys.path:
        sys.path.insert(0, _scripts)
    from seed_mes_config import seed_mes_config

    # Count before second run
    before = (await seeded_db.execute(
        select(func.count()).select_from(Facility)
        .where(Facility.company_id.in_(ALL_COMPANY_IDS))
    )).scalar_one()

    # Pass explicit URL to avoid picking up CORE_DATABASE_URL from root .env
    from tests.integration.conftest import MES_TEST_DB_URL
    await seed_mes_config(db_url=MES_TEST_DB_URL)

    after = (await seeded_db.execute(
        select(func.count()).select_from(Facility)
        .where(Facility.company_id.in_(ALL_COMPANY_IDS))
    )).scalar_one()

    assert after == before, "Second run created duplicate Facility rows"
