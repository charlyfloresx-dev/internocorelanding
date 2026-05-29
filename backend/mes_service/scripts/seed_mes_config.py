"""
InternoCore — MES Configuration Seed (Phase 156-A)
===================================================
Siembra la configuración física de planta para las 3 empresas del grupo:
  ENTERPRISE_ID   → Manufactura Industrial MX  (Planta Tijuana)
  LOGISTICS_MX_ID → Logística MX               (Centro Distribución MX)
  LOGISTICS_US_ID → Logistics US               (San Diego Distribution Center)

Por empresa:
  • 1 Facility
  • 3 ProductionAreas  (Líneas de Ensamble / Calidad / Almacén WIP)
  • 4 Resources         (CELDA-58D, CELDA-59A, TURRET-01, PRENSA-01)
  • 3 Shifts            (MAT 06-14 / VES 14-22 / NOC 22-06)
  • 2 ShiftBreaks/turno (Descanso 30min + Comida 30min)
  • 5 StandardTimes     (ECM-600, TRB-700, BRK-800, FLI-900, SUS-100)

Idempotente: inserta solo si no existe el id determinístico.
IDs generados con uuid5(NAMESPACE_DNS, "mes156.<tipo>.<company_id>.<key>").
"""
import asyncio
import os
import sys
import uuid
import logging
from datetime import time
from decimal import Decimal

# ── Path resolution (works both inside Docker /app and locally) ────────────────
_script_dir = os.path.dirname(os.path.abspath(__file__))
_service_root = os.path.abspath(os.path.join(_script_dir, ".."))
_backend_root = os.path.abspath(os.path.join(_service_root, ".."))
for _p in [_service_root, _backend_root, "/app"]:
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from mes_app.models.facility import Facility
from mes_app.models.production_area import ProductionArea
from mes_app.models.resource import Resource
from mes_app.models.shift import Shift
from mes_app.models.shift_break import ShiftBreak
from mes_app.models.standard_time import StandardTime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("mes-config-seed")

# ── Connection ─────────────────────────────────────────────────────────────────
_DB_URL = os.getenv(
    "CORE_DATABASE_URL",
    "postgresql+asyncpg://user:internocore_db_pass_2026@localhost:5433/mes_db",
)

# ── SSOT IDs — aligned with unified_industrial_seed.py ────────────────────────
GROUP_ID        = uuid.UUID("eb8f7e2c-3f4a-4b5c-8d7e-1f2a3b4c5d6e")
ENTERPRISE_ID   = uuid.UUID("9cd9986b-89da-48b7-8733-26a2a1225b01")
LOGISTICS_MX_ID = uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242")
LOGISTICS_US_ID = uuid.UUID("777cc8a6-34f9-42df-8f29-28254e0ad277")
SYSTEM_USER_ID  = uuid.UUID("00000000-0000-0000-0000-000000000001")

_NS = uuid.NAMESPACE_DNS


def _uid(*parts: object) -> uuid.UUID:
    """Deterministic UUID from mes156 namespace + arbitrary key parts."""
    return uuid.uuid5(_NS, "mes156." + ".".join(str(p) for p in parts))


# ── Per-company configuration ──────────────────────────────────────────────────
COMPANIES = [
    {
        "id": ENTERPRISE_ID,
        "facility": {
            "code": "PLT-TIJ",
            "name": "Planta Tijuana",
            "location": "Tijuana, BC, México",
        },
        "areas": [
            {"name": "Líneas de Ensamble", "desc": "Producción en piso — celdas y máquinas"},
            {"name": "Área de Calidad", "desc": "Inspección, pruebas y control de calidad"},
            {"name": "Almacén WIP", "desc": "Work-in-Progress — material en proceso"},
        ],
        "resources": [
            {"code": "CELDA-58D",  "name": "Celda de Ensamble 58D",       "type": "CELL",    "cap": 240},
            {"code": "CELDA-59A",  "name": "Celda de Ensamble 59A",       "type": "CELL",    "cap": 240},
            {"code": "TURRET-01",  "name": "Torno CNC TURRET-01",         "type": "MACHINE", "cap": 180},
            {"code": "PRENSA-01",  "name": "Prensa Hidráulica PRENSA-01", "type": "MACHINE", "cap": 120},
        ],
    },
    {
        "id": LOGISTICS_MX_ID,
        "facility": {
            "code": "PLT-MXC",
            "name": "Centro de Distribución MX",
            "location": "Monterrey, NL, México",
        },
        "areas": [
            {"name": "Líneas de Picking", "desc": "Preparación de pedidos"},
            {"name": "Área de Recepción", "desc": "Recepción y validación de mercancía"},
            {"name": "Almacén Principal", "desc": "Almacenamiento general"},
        ],
        "resources": [
            {"code": "PICK-L01",   "name": "Línea de Picking L01",        "type": "LINE",    "cap": 300},
            {"code": "PICK-L02",   "name": "Línea de Picking L02",        "type": "LINE",    "cap": 300},
            {"code": "RECEP-01",   "name": "Estación de Recepción 01",    "type": "CELL",    "cap": 150},
            {"code": "RECEP-02",   "name": "Estación de Recepción 02",    "type": "CELL",    "cap": 150},
        ],
    },
    {
        "id": LOGISTICS_US_ID,
        "facility": {
            "code": "PLT-SDG",
            "name": "San Diego Distribution Center",
            "location": "San Diego, CA, USA",
        },
        "areas": [
            {"name": "Assembly Lines", "desc": "Production floor — cells and machines"},
            {"name": "Quality Control", "desc": "Inspection and testing"},
            {"name": "WIP Storage", "desc": "Work-in-Progress material"},
        ],
        "resources": [
            {"code": "CELL-A01",   "name": "Assembly Cell A01",           "type": "CELL",    "cap": 240},
            {"code": "CELL-A02",   "name": "Assembly Cell A02",           "type": "CELL",    "cap": 240},
            {"code": "CNC-01",     "name": "CNC Lathe CNC-01",            "type": "MACHINE", "cap": 180},
            {"code": "PRESS-01",   "name": "Hydraulic Press PRESS-01",    "type": "MACHINE", "cap": 120},
        ],
    },
]

# Shifts are the same structure for every company
SHIFT_TEMPLATES = [
    {
        "code": "MAT",
        "name": "Turno Matutino",
        "start": time(6, 0),
        "end": time(14, 0),
        "overnight": False,
        "breaks": [
            {"code": "DSC1", "label": "Primer Descanso", "type": "BREAK",
             "start": time(9, 0), "end": time(9, 30), "mins": 30},
            {"code": "COM1", "label": "Comida",          "type": "MEAL",
             "start": time(11, 0), "end": time(11, 30), "mins": 30},
        ],
    },
    {
        "code": "VES",
        "name": "Turno Vespertino",
        "start": time(14, 0),
        "end": time(22, 0),
        "overnight": False,
        "breaks": [
            {"code": "DSC2", "label": "Primer Descanso", "type": "BREAK",
             "start": time(17, 0), "end": time(17, 30), "mins": 30},
            {"code": "COM2", "label": "Comida",          "type": "MEAL",
             "start": time(19, 0), "end": time(19, 30), "mins": 30},
        ],
    },
    {
        "code": "NOC",
        "name": "Turno Nocturno",
        "start": time(22, 0),
        "end": time(6, 0),
        "overnight": True,
        "breaks": [
            {"code": "DSC3", "label": "Primer Descanso", "type": "BREAK",
             "start": time(1, 0), "end": time(1, 30), "mins": 30},
            {"code": "COM3", "label": "Comida",          "type": "MEAL",
             "start": time(3, 0), "end": time(3, 30), "mins": 30},
        ],
    },
]

# Standard times — same item_codes across all companies (aligned with PRODUCT_CATALOG)
STANDARD_TIME_TEMPLATES = [
    {"sku": "ECM-600", "op": "Ensamble Módulo ECM",            "hours": Decimal("0.0028"), "cycle": 10},
    {"sku": "TRB-700", "op": "Ensamble Turbocompresor",        "hours": Decimal("0.0139"), "cycle": 50},
    {"sku": "BRK-800", "op": "Torneado Disco de Freno",        "hours": Decimal("0.0056"), "cycle": 20},
    {"sku": "FLI-900", "op": "Limpieza Inyector Combustible",  "hours": Decimal("0.0028"), "cycle": 10},
    {"sku": "SUS-100", "op": "Ajuste Amortiguador",            "hours": Decimal("0.0083"), "cycle": 30},
]


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_or_create(session: AsyncSession, model_class, obj_id: uuid.UUID, **kwargs):
    existing = await session.get(model_class, obj_id)
    if existing:
        return existing, False
    obj = model_class(id=obj_id, **kwargs)
    session.add(obj)
    return obj, True


def _base(company_id: uuid.UUID) -> dict:
    return {
        "company_id": company_id,
        "tenant_id": company_id,
        "group_id": GROUP_ID,
        "created_by": SYSTEM_USER_ID,
    }


# ── Seed functions ────────────────────────────────────────────────────────────

async def _seed_company(session: AsyncSession, cfg: dict) -> dict[str, int]:
    company_id: uuid.UUID = cfg["id"]
    counts = {"facility": 0, "area": 0, "resource": 0, "shift": 0, "break": 0, "stdtime": 0}

    # ── Facility ──────────────────────────────────────────────────────────────
    fac_cfg = cfg["facility"]
    fac_id = _uid("facility", company_id, fac_cfg["code"])
    fac, created = await _get_or_create(
        session, Facility, fac_id,
        code=fac_cfg["code"],
        name=fac_cfg["name"],
        location_description=fac_cfg["location"],
        **_base(company_id),
    )
    if created:
        counts["facility"] += 1
        log.info("  [+] Facility %s (%s)", fac_cfg["code"], company_id)

    # ── ProductionAreas ───────────────────────────────────────────────────────
    area_map: dict[str, uuid.UUID] = {}
    for area_cfg in cfg["areas"]:
        area_id = _uid("area", company_id, area_cfg["name"])
        area_map[area_cfg["name"]] = area_id
        _, created = await _get_or_create(
            session, ProductionArea, area_id,
            name=area_cfg["name"],
            description=area_cfg["desc"],
            facility_id=fac_id,
            **_base(company_id),
        )
        if created:
            counts["area"] += 1

    # First area hosts the production resources
    resources_area_id = list(area_map.values())[0]

    # ── Resources ─────────────────────────────────────────────────────────────
    for res_cfg in cfg["resources"]:
        res_id = _uid("resource", company_id, res_cfg["code"])
        _, created = await _get_or_create(
            session, Resource, res_id,
            code=res_cfg["code"],
            name=res_cfg["name"],
            resource_type=res_cfg["type"],
            capacity=Decimal(str(res_cfg["cap"])),
            production_area_id=resources_area_id,
            active=True,
            **_base(company_id),
        )
        if created:
            counts["resource"] += 1

    # ── Shifts + ShiftBreaks ──────────────────────────────────────────────────
    for shift_tmpl in SHIFT_TEMPLATES:
        shift_id = _uid("shift", company_id, shift_tmpl["code"])
        shift, created = await _get_or_create(
            session, Shift, shift_id,
            code=shift_tmpl["code"],
            name=shift_tmpl["name"],
            start_time=shift_tmpl["start"],
            end_time=shift_tmpl["end"],
            is_overnight=shift_tmpl["overnight"],
            break_minutes=60,
            resource_id=None,
            is_active=True,
            **_base(company_id),
        )
        if created:
            counts["shift"] += 1

        for brk in shift_tmpl["breaks"]:
            brk_id = _uid("break", shift_id, brk["code"])
            _, created = await _get_or_create(
                session, ShiftBreak, brk_id,
                shift_id=shift_id,
                code=brk["code"],
                label=brk["label"],
                break_type=brk["type"],
                start_time=brk["start"],
                end_time=brk["end"],
                duration_minutes=brk["mins"],
                **_base(company_id),
            )
            if created:
                counts["break"] += 1

    # ── StandardTimes ─────────────────────────────────────────────────────────
    for st in STANDARD_TIME_TEMPLATES:
        st_id = _uid("stdtime", company_id, st["sku"])
        _, created = await _get_or_create(
            session, StandardTime, st_id,
            item_code=st["sku"],
            operation_name=st["op"],
            set_time_hours=st["hours"],
            cycle_time_seconds=st["cycle"],
            **_base(company_id),
        )
        if created:
            counts["stdtime"] += 1

    return counts


async def seed_mes_config(db_url: str | None = None) -> None:
    """Seed MES configuration for all companies.

    Args:
        db_url: Override database URL (used in tests to pass the test DB URL directly).
                Falls back to CORE_DATABASE_URL env var → hardcoded mes_db default.
    """
    log.info("=" * 60)
    log.info("  MES Configuration Seed — Phase 156-A")
    log.info("=" * 60)

    url = db_url or _DB_URL
    engine = create_async_engine(url, pool_pre_ping=True, echo=False)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with factory() as session:
            async with session.begin():
                totals = {"facility": 0, "area": 0, "resource": 0,
                          "shift": 0, "break": 0, "stdtime": 0}
                for cfg in COMPANIES:
                    log.info("[company] %s", cfg["id"])
                    counts = await _seed_company(session, cfg)
                    for k, v in counts.items():
                        totals[k] += v

        log.info("-" * 60)
        log.info(
            "Done: %d facilities, %d areas, %d resources, "
            "%d shifts, %d breaks, %d standard_times",
            totals["facility"], totals["area"], totals["resource"],
            totals["shift"], totals["break"], totals["stdtime"],
        )
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_mes_config())
