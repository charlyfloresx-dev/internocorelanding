import sys
import os
import pytest
import uuid
from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

# ── Path resolution ────────────────────────────────────────────────────────────
_service_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_backend_root = os.path.abspath(os.path.join(_service_root, ".."))
_repo_root    = os.path.abspath(os.path.join(_backend_root, ".."))
for _p in [_service_root, _backend_root]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Load root .env before importing common (which validates config at import time)
from dotenv import load_dotenv
load_dotenv(os.path.join(_repo_root, ".env"), override=False)

# Imports from hcm_service and common
from hcm_app.models.collaborator import Collaborator
from hcm_app.models.tenant_settings import HrTenantConfig
from hcm_app.api.v1.endpoints.collaborators import _calculate_eligibility
from hcm_app.schemas.collaborator import EligibilityResponse
from hcm_app.infrastructure.repositories.collaborator_repository import SQLAlchemyCollaboratorRepository
from hcm_app.domain.entities.collaborator_entities import Collaborator as DomainCollaborator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

# ── Real PostgreSQL (hcm_db) ───────────────────────────────────────────────────
HCM_TEST_DB_URL = os.environ.get(
    "HCM_TEST_DB_URL",
    "postgresql+asyncpg://user:internocore_db_pass_2026@localhost:5433/hcm_db",
)


@pytest.fixture()
async def db_session():
    """Session contra hcm_db real; rollback al finalizar — no contamina datos."""
    engine = create_async_engine(HCM_TEST_DB_URL, pool_pre_ping=True, echo=False)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        async with session.begin():
            yield session
            await session.rollback()
    await engine.dispose()


@pytest.fixture
def anyio_backend():
    return "asyncio"


# ── Parametrized scenario testing ──────────────────────────────────────────────
@pytest.mark.parametrize(
    "cdl_days, medical_days, visa_days, sentry_id, global_entry_id, threshold, expected_eligible, expected_reason_substring",
    [
        # Caso 01: Éxito con Sentry
        (45, 45, 45, "SENTRY123", None, 30, True, "vigente"),
        # Caso 02: Éxito con Global Entry
        (45, 45, 45, None, "GE9876", 30, True, "vigente"),
        # Caso 03: Fallo por Umbral Seguro (CDL vence en +15 días, umbral es 30)
        (15, 45, 45, "SENTRY123", None, 30, False, "Licencia Comercial (CDL/Federal) vence en 15 día(s)"),
        # Caso 04: Fallo por Falta de Identificador (Ambos nulos)
        (45, 45, 45, None, None, 30, False, "requiere credencial FAST/Sentry o Global Entry activa"),
        # Caso 05: Fallo por CDL expirado (hace 5 días)
        (-5, 45, 45, "SENTRY123", None, 30, False, "expirado hace 5 día(s)"),
        # Caso 06: Fallo por CDL no registrado (None)
        (None, 45, 45, "SENTRY123", None, 30, False, "Documento no registrado: Licencia Comercial"),
        # Caso 07: Fallo por Medical Expiry bajo el umbral (20 días, umbral 30)
        (45, 20, 45, "SENTRY123", None, 30, False, "Certificado Médico (SCT/DOT) vence en 20 día(s)"),
        # Caso 08: Fallo por Visa Expiry bajo el umbral (10 días, umbral 30)
        (45, 45, 10, "SENTRY123", None, 30, False, "Visa Láser / B1-B2 vence en 10 día(s)"),
    ]
)
def test_calculate_eligibility_scenarios(
    cdl_days, medical_days, visa_days, sentry_id, global_entry_id, threshold, expected_eligible, expected_reason_substring
):
    today = date.today()
    
    cdl_date = today + timedelta(days=cdl_days) if cdl_days is not None else None
    med_date = today + timedelta(days=medical_days) if medical_days is not None else None
    visa_date = today + timedelta(days=visa_days) if visa_days is not None else None

    # Collaborator mock model instance
    collaborator = Collaborator(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        internal_id="TEST-DRIVER-01",
        first_name="Carlos",
        last_name_paternal="Ramirez",
        last_name_maternal="Lopez",
        is_active=True,
        driver_license_expiry=cdl_date,
        medical_certificate_expiry=med_date,
        visa_expiry=visa_date,
        sentry_id=sentry_id,
        global_entry_id=global_entry_id,
    )
    
    response = _calculate_eligibility(collaborator, "CROSS_BORDER", threshold)
    
    assert response.eligible == expected_eligible
    assert expected_reason_substring.lower() in response.reason.lower()
    assert response.collaborator_id == collaborator.id
    assert response.full_name == "Carlos Ramirez Lopez"
    
    if not expected_eligible:
        # Check detail structure
        assert response.details is not None
        assert response.details.document is not None


# ── Multi-tenant isolation testing ─────────────────────────────────────────────
@pytest.mark.anyio
async def test_multi_tenant_isolation(db_session):
    """
    Validates that query results and lookups are strictly isolated by company_id (tenant_id).
    Inserting collaborators for Company A must not be visible/retrievable by Company B queries.
    """
    company_a = uuid.uuid4()
    company_b = uuid.uuid4()
    
    repo = SQLAlchemyCollaboratorRepository(db_session)
    
    # Collaborator in Company A
    c1 = DomainCollaborator(
        id=uuid.uuid4(),
        company_id=company_a,
        tenant_id=company_a,
        internal_id="EMP-A-100",
        full_name="Alice Company A",
        is_supervisor=False,
    )
    
    # Collaborator in Company B
    c2 = DomainCollaborator(
        id=uuid.uuid4(),
        company_id=company_b,
        tenant_id=company_b,
        internal_id="EMP-B-200",
        full_name="Bob Company B",
        is_supervisor=False,
    )
    
    # Persist both via repo
    await repo.create(c1)
    await repo.create(c2)
    
    # Verify company A list only contains company A collaborator
    list_a = await repo.list_all(company_a)
    assert len(list_a) == 1
    assert list_a[0].id == c1.id
    assert list_a[0].full_name == "Alice Company A"
    
    # Verify company B list only contains company B collaborator
    list_b = await repo.list_all(company_b)
    assert len(list_b) == 1
    assert list_b[0].id == c2.id
    assert list_b[0].full_name == "Bob Company B"
    
    # Verify lookup by internal_id is tenant-scoped
    c_found_a = await repo.get_by_internal_id("EMP-A-100", company_a)
    assert c_found_a is not None
    assert c_found_a.id == c1.id
    
    # Attempting to fetch C1 using Company B scope should fail (None)
    c_not_found = await repo.get_by_internal_id("EMP-A-100", company_b)
    assert c_not_found is None
