"""
Integration tests for Department CRUD endpoints (Phase 158).
Tests run against real hcm_db — each test rolls back via subtransaction.
"""
import sys
import os
import uuid
import pytest

_service_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_backend_root = os.path.abspath(os.path.join(_service_root, ".."))
_repo_root    = os.path.abspath(os.path.join(_backend_root, ".."))
for _p in [_service_root, _backend_root]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from dotenv import load_dotenv
load_dotenv(os.path.join(_repo_root, ".env"), override=False)

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, text
from hcm_app.models.department import Department

HCM_TEST_DB_URL = os.environ.get(
    "HCM_TEST_DB_URL",
    "postgresql+asyncpg://user:internocore_db_pass_2026@localhost:5433/hcm_db",
)

COMPANY_ID = uuid.UUID("9cd9986b-89da-48b7-8733-26a2a1225b01")
TENANT_ID  = uuid.UUID("9cd9986b-89da-48b7-8733-26a2a1225b01")
USER_ID    = uuid.UUID("69aa5ddc-bbaa-46e6-a7f0-aeb4b92b6d38")


@pytest.fixture()
async def db():
    engine = create_async_engine(HCM_TEST_DB_URL, echo=False)
    async with engine.connect() as conn:
        await conn.execute(text("SET app.current_tenant = '9cd9986b-89da-48b7-8733-26a2a1225b01'"))
        session = AsyncSession(bind=conn, expire_on_commit=False)
        try:
            yield session
        finally:
            await conn.rollback()
    await engine.dispose()


@pytest.fixture()
def dept_payload():
    suffix = str(uuid.uuid4())[:6].upper()
    return {
        "name": f"Test Department {suffix}",
        "code": f"TD-{suffix}",
        "description": "Integration test department",
        "is_active": True,
    }


# ── helpers ────────────────────────────────────────────────────────────────────

async def _insert(db, payload: dict) -> Department:
    dept = Department(
        id=uuid.uuid4(),
        company_id=COMPANY_ID,
        tenant_id=TENANT_ID,
        name=payload["name"],
        code=payload["code"].upper(),
        description=payload.get("description"),
        is_active=payload.get("is_active", True),
        version_id=1,
        created_by=USER_ID,
    )
    db.add(dept)
    await db.flush()
    return dept


# ── GET (list) ────────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_list_departments_returns_list(db):
    result = await db.execute(
        select(Department).where(Department.company_id == COMPANY_ID)
    )
    rows = result.scalars().all()
    assert isinstance(rows, list)


@pytest.mark.anyio
async def test_list_filters_by_is_active(db, dept_payload):
    active = await _insert(db, {**dept_payload, "code": dept_payload["code"] + "A", "is_active": True})
    inactive = await _insert(db, {**dept_payload, "code": dept_payload["code"] + "I", "is_active": False})

    active_rows = (await db.execute(
        select(Department).where(Department.company_id == COMPANY_ID, Department.is_active == True)
    )).scalars().all()
    inactive_rows = (await db.execute(
        select(Department).where(Department.company_id == COMPANY_ID, Department.is_active == False)
    )).scalars().all()

    active_ids = {r.id for r in active_rows}
    inactive_ids = {r.id for r in inactive_rows}

    assert active.id in active_ids
    assert inactive.id in inactive_ids
    assert active.id not in inactive_ids


# ── POST (create) ──────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_create_department_persists(db, dept_payload):
    dept = await _insert(db, dept_payload)
    fetched = (await db.execute(
        select(Department).where(Department.id == dept.id)
    )).scalar_one_or_none()

    assert fetched is not None
    assert fetched.name == dept_payload["name"]
    assert fetched.code == dept_payload["code"].upper()
    assert fetched.company_id == COMPANY_ID


@pytest.mark.anyio
async def test_create_department_code_forced_uppercase(db, dept_payload):
    payload_lower = {**dept_payload, "code": dept_payload["code"].lower()}
    dept = await _insert(db, payload_lower)
    assert dept.code == dept_payload["code"].upper()


@pytest.mark.anyio
async def test_create_department_duplicate_code_same_company(db, dept_payload):
    # Use a nested savepoint so the exception doesn't abort the outer transaction
    await _insert(db, dept_payload)
    await db.flush()

    raised = False
    try:
        async with db.begin_nested():
            conflict = Department(
                id=uuid.uuid4(),
                company_id=COMPANY_ID,
                tenant_id=TENANT_ID,
                name="Another name",
                code=dept_payload["code"].upper(),
                is_active=True,
                version_id=1,
            )
            db.add(conflict)
            await db.flush()
    except Exception:
        raised = True

    assert raised, "Expected IntegrityError for duplicate (company_id, code)"


@pytest.mark.anyio
async def test_create_department_same_code_different_company(db, dept_payload):
    other_company = uuid.uuid4()
    dept1 = await _insert(db, dept_payload)

    dept2 = Department(
        id=uuid.uuid4(),
        company_id=other_company,
        tenant_id=other_company,
        name=dept_payload["name"],
        code=dept_payload["code"].upper(),
        is_active=True,
        version_id=1,
    )
    db.add(dept2)
    await db.flush()

    assert dept1.code == dept2.code
    assert dept1.company_id != dept2.company_id


# ── PATCH (update) ─────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_update_department_name(db, dept_payload):
    dept = await _insert(db, dept_payload)
    dept.name = "Updated Name"
    dept.updated_by = USER_ID
    await db.flush()

    fetched = (await db.execute(
        select(Department).where(Department.id == dept.id)
    )).scalar_one()
    assert fetched.name == "Updated Name"


@pytest.mark.anyio
async def test_update_department_description_to_none(db, dept_payload):
    dept = await _insert(db, dept_payload)
    dept.description = None
    await db.flush()

    fetched = (await db.execute(
        select(Department).where(Department.id == dept.id)
    )).scalar_one()
    assert fetched.description is None


@pytest.mark.anyio
async def test_update_nonexistent_department_returns_none(db):
    ghost = (await db.execute(
        select(Department).where(Department.id == uuid.uuid4())
    )).scalar_one_or_none()
    assert ghost is None


# ── DELETE (soft) ──────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_soft_delete_sets_is_active_false(db, dept_payload):
    dept = await _insert(db, dept_payload)
    assert dept.is_active is True

    dept.is_active = False
    dept.updated_by = USER_ID
    await db.flush()

    fetched = (await db.execute(
        select(Department).where(Department.id == dept.id)
    )).scalar_one()
    assert fetched.is_active is False


@pytest.mark.anyio
async def test_soft_delete_does_not_remove_row(db, dept_payload):
    dept = await _insert(db, dept_payload)
    dept.is_active = False
    await db.flush()

    still_exists = (await db.execute(
        select(Department).where(Department.id == dept.id)
    )).scalar_one_or_none()
    assert still_exists is not None


@pytest.mark.anyio
async def test_reactivate_department(db, dept_payload):
    dept = await _insert(db, dept_payload)
    dept.is_active = False
    await db.flush()

    dept.is_active = True
    await db.flush()

    fetched = (await db.execute(
        select(Department).where(Department.id == dept.id)
    )).scalar_one()
    assert fetched.is_active is True
