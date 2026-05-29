"""
UC-MES-RESOURCE-154: Facility, ProductionArea, Resource expanded — Phase 154 Part 1.

Validates against real mes_db (PostgreSQL):
  - Migration 009 applied: mes_facilities, mes_production_areas,
    mes_resource_support_members, mes_shift_breaks tables exist
  - Resource model expanded columns: description, resource_type, warehouse_id,
    production_area_id, unique(company_id, code)
  - Facility and ProductionArea CRUD
  - ProductionArea → Facility FK enforced
  - Resource → ProductionArea FK enforced
  - Resource warehouse_id is optional, no DB FK constraint (Iron Wall)
  - ResourceSupportMember soft FK on collaborator_id (no DB FK)
  - ShiftBreak references mes_shifts (FK)
"""
import uuid
import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from mes_app.models.facility import Facility
from mes_app.models.production_area import ProductionArea
from mes_app.models.resource import Resource
from mes_app.models.resource_support_member import ResourceSupportMember
from mes_app.models.shift_break import ShiftBreak
from mes_app.models.shift import Shift


# ── Helpers ───────────────────────────────────────────────────────────────────

def _company() -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_DNS, "test.company.resource154")


def _make_facility(company_id: uuid.UUID, code: str = "PLT-MX-01") -> Facility:
    return Facility(
        id=uuid.uuid4(),
        company_id=company_id,
        tenant_id=company_id,
        code=code,
        name="Planta Tijuana",
        location_description="Tijuana, BC, México",
    )


def _make_area(company_id: uuid.UUID, facility_id: uuid.UUID,
               name: str = "Líneas de ensamble") -> ProductionArea:
    return ProductionArea(
        id=uuid.uuid4(),
        company_id=company_id,
        tenant_id=company_id,
        name=name,
        description="Área de ensamble final",
        facility_id=facility_id,
    )


def _make_resource(company_id: uuid.UUID,
                   code: str = "CELDA-58D",
                   production_area_id: uuid.UUID | None = None,
                   warehouse_id: uuid.UUID | None = None) -> Resource:
    return Resource(
        id=uuid.uuid4(),
        company_id=company_id,
        tenant_id=company_id,
        code=code,
        name="Celda de ensamble 58D",
        description="Línea de ensamble final, turno matutino",
        resource_type="CELL",
        capacity=240,
        production_area_id=production_area_id,
        warehouse_id=warehouse_id,
        active=True,
    )


# ── Schema verification (migration 009) ──────────────────────────────────────

async def test_mes_facilities_table_exists(db_session):
    result = await db_session.execute(
        text("SELECT table_name FROM information_schema.tables "
             "WHERE table_schema='public' AND table_name='mes_facilities'")
    )
    assert result.scalar() == "mes_facilities", "Migration 009 debe crear mes_facilities"


async def test_mes_production_areas_table_exists(db_session):
    result = await db_session.execute(
        text("SELECT table_name FROM information_schema.tables "
             "WHERE table_schema='public' AND table_name='mes_production_areas'")
    )
    assert result.scalar() == "mes_production_areas"


async def test_mes_resource_support_members_table_exists(db_session):
    result = await db_session.execute(
        text("SELECT table_name FROM information_schema.tables "
             "WHERE table_schema='public' AND table_name='mes_resource_support_members'")
    )
    assert result.scalar() == "mes_resource_support_members"


async def test_mes_shift_breaks_table_exists(db_session):
    result = await db_session.execute(
        text("SELECT table_name FROM information_schema.tables "
             "WHERE table_schema='public' AND table_name='mes_shift_breaks'")
    )
    assert result.scalar() == "mes_shift_breaks"


async def test_resource_has_description_column(db_session):
    result = await db_session.execute(
        text("SELECT column_name FROM information_schema.columns "
             "WHERE table_name='mes_resources' AND column_name='description'")
    )
    assert result.scalar() == "description"


async def test_resource_has_resource_type_column(db_session):
    result = await db_session.execute(
        text("SELECT column_name FROM information_schema.columns "
             "WHERE table_name='mes_resources' AND column_name='resource_type'")
    )
    assert result.scalar() == "resource_type"


async def test_resource_has_warehouse_id_column(db_session):
    result = await db_session.execute(
        text("SELECT column_name FROM information_schema.columns "
             "WHERE table_name='mes_resources' AND column_name='warehouse_id'")
    )
    assert result.scalar() == "warehouse_id"


async def test_resource_warehouse_id_has_no_fk_constraint(db_session):
    """Iron Wall: warehouse_id debe ser UUID libre, sin FK hacia inventory_db."""
    result = await db_session.execute(
        text("""
            SELECT COUNT(*) FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_name = 'mes_resources'
              AND kcu.column_name = 'warehouse_id'
        """)
    )
    count = result.scalar()
    assert count == 0, "warehouse_id no debe tener FK constraint — Iron Wall ADR-02"


# ── Facility CRUD ─────────────────────────────────────────────────────────────

async def test_facility_create_read(db_session):
    company_id = _company()
    facility = _make_facility(company_id)
    db_session.add(facility)
    await db_session.flush()

    result = await db_session.execute(
        select(Facility).where(Facility.id == facility.id)
    )
    found = result.scalar_one()
    assert found.code == "PLT-MX-01"
    assert found.name == "Planta Tijuana"
    assert found.location_description == "Tijuana, BC, México"


async def test_facility_unique_code_per_company(db_session):
    """Dos facilities con el mismo code en la misma empresa deben fallar."""
    company_id = _company()
    db_session.add(_make_facility(company_id, code="PLT-DUP"))
    await db_session.flush()
    db_session.add(_make_facility(company_id, code="PLT-DUP"))
    with pytest.raises(IntegrityError):
        await db_session.flush()


# ── ProductionArea CRUD ───────────────────────────────────────────────────────

async def test_production_area_references_facility(db_session):
    company_id = _company()
    facility = _make_facility(company_id, code="PLT-AREA-TEST")
    db_session.add(facility)
    await db_session.flush()

    area = _make_area(company_id, facility.id)
    db_session.add(area)
    await db_session.flush()

    result = await db_session.execute(
        select(ProductionArea).where(ProductionArea.id == area.id)
    )
    found = result.scalar_one()
    assert found.facility_id == facility.id
    assert found.name == "Líneas de ensamble"


async def test_production_area_fk_facility_enforced(db_session):
    """FK hacia mes_facilities debe rechazar facility_id inexistente."""
    company_id = _company()
    area = _make_area(company_id, facility_id=uuid.uuid4())
    db_session.add(area)
    with pytest.raises(IntegrityError):
        await db_session.flush()


# ── Resource expanded CRUD ────────────────────────────────────────────────────

async def test_resource_create_with_production_area(db_session):
    company_id = _company()
    facility = _make_facility(company_id, code="PLT-RES-TEST")
    db_session.add(facility)
    await db_session.flush()

    area = _make_area(company_id, facility.id)
    db_session.add(area)
    await db_session.flush()

    resource = _make_resource(company_id, production_area_id=area.id)
    db_session.add(resource)
    await db_session.flush()

    result = await db_session.execute(
        select(Resource).where(Resource.id == resource.id)
    )
    found = result.scalar_one()
    assert found.code == "CELDA-58D"
    assert found.resource_type == "CELL"
    assert found.description == "Línea de ensamble final, turno matutino"
    assert found.production_area_id == area.id
    assert found.warehouse_id is None


async def test_resource_warehouse_id_accepts_any_uuid(db_session):
    """warehouse_id acepta cualquier UUID — no valida contra inventory_db (soft FK)."""
    company_id = _company()
    fake_warehouse_id = uuid.uuid4()
    resource = _make_resource(company_id, code="CELDA-WH-TEST",
                              warehouse_id=fake_warehouse_id)
    db_session.add(resource)
    await db_session.flush()  # debe pasar sin error

    result = await db_session.execute(
        select(Resource).where(Resource.id == resource.id)
    )
    found = result.scalar_one()
    assert found.warehouse_id == fake_warehouse_id


async def test_resource_unique_code_per_company(db_session):
    """UniqueConstraint(company_id, code) impide duplicados."""
    company_id = _company()
    db_session.add(_make_resource(company_id, code="CELDA-DUP"))
    await db_session.flush()
    db_session.add(_make_resource(company_id, code="CELDA-DUP"))
    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_resource_type_values(db_session):
    """resource_type acepta CELL, MACHINE, AREA, LINE."""
    company_id = _company()
    for rtype, code in [("CELL", "R-CELL"), ("MACHINE", "R-MACH"),
                         ("AREA", "R-AREA"), ("LINE", "R-LINE")]:
        r = Resource(
            id=uuid.uuid4(),
            company_id=company_id,
            tenant_id=company_id,
            code=code,
            name=f"Resource {rtype}",
            resource_type=rtype,
            active=True,
        )
        db_session.add(r)
    await db_session.flush()  # todos deben pasar


# ── ResourceSupportMember ─────────────────────────────────────────────────────

async def test_resource_support_member_create(db_session):
    company_id = _company()
    resource = _make_resource(company_id, code="CELDA-SUP")
    db_session.add(resource)
    await db_session.flush()

    member = ResourceSupportMember(
        id=uuid.uuid4(),
        company_id=company_id,
        tenant_id=company_id,
        resource_id=resource.id,
        collaborator_id=uuid.uuid4(),  # soft FK — no existe en hcm_db
        role="SUPERVISOR",
    )
    db_session.add(member)
    await db_session.flush()  # debe pasar — collaborator_id es soft FK

    result = await db_session.execute(
        select(ResourceSupportMember).where(ResourceSupportMember.resource_id == resource.id)
    )
    found = result.scalars().all()
    assert len(found) == 1
    assert found[0].role == "SUPERVISOR"


# ── ShiftBreak ────────────────────────────────────────────────────────────────

async def test_shift_break_references_shift(db_session):
    from datetime import time
    company_id = _company()

    shift = Shift(
        id=uuid.uuid4(),
        company_id=company_id,
        tenant_id=company_id,
        code="T1-154",
        name="Matutino 154",
        start_time=time(6, 0),
        end_time=time(14, 0),
        is_overnight=False,
        break_minutes=60,
        is_active=True,
    )
    db_session.add(shift)
    await db_session.flush()

    sb = ShiftBreak(
        id=uuid.uuid4(),
        company_id=company_id,
        tenant_id=company_id,
        shift_id=shift.id,
        code="R1",
        label="Primer descanso",
        break_type="BREAK",
        start_time=time(8, 35),
        end_time=time(9, 5),
        duration_minutes=30,
    )
    db_session.add(sb)
    await db_session.flush()

    result = await db_session.execute(
        select(ShiftBreak).where(ShiftBreak.shift_id == shift.id)
    )
    found = result.scalars().all()
    assert len(found) == 1
    assert found[0].label == "Primer descanso"
    assert found[0].duration_minutes == 30
    assert found[0].break_type == "BREAK"
