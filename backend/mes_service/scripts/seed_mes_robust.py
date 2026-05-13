import asyncio
import uuid
import logging
from datetime import datetime, timezone
from sqlalchemy import String, ForeignKey, DateTime, select, text, Numeric, Boolean
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, Mapped, mapped_column, DeclarativeBase
import os

# CONFIG
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5433/mes_db")
COMPANY_A_ID = uuid.UUID("9cd9986b-89da-48b7-8733-26a2a1225b01")
SYSTEM_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

class MultiTenantBase(Base):
    __abstract__ = True
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(index=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_by: Mapped[uuid.UUID] = mapped_column(nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    updated_by: Mapped[uuid.UUID] = mapped_column(nullable=True)
    version_id: Mapped[int] = mapped_column(default=1)

class DowntimeReason(MultiTenantBase):
    __tablename__ = "mes_downtime_reasons"
    code: Mapped[str] = mapped_column(String(20), index=True)
    name: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(50))

class LaborType(MultiTenantBase):
    __tablename__ = "mes_labor_types"
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(250), nullable=True)

DOWNTIME_CATEGORIES = {
    "Equipment": ["Banda dañada", "Cambio de Rollos", "Equipo Caído", "Falla Eléctrica", "Falta de Herramienta", "Guarda Quebrada", "Herramienta Defectuosa", "Material Atorado", "No Baja Cabezal", "No calienta", "No corta hilo", "Sellado Débil", "Setup", "Sistema de embobinado no funciona", "Sobre Sellado"],
    "Management": ["Sin Plan de Producción"],
    "Material": ["Atom Falta de SubEnsamble", "Falta de Insumos", "INDS Discrepancia de Inventario Almacén", "INW Discrepancia Inventario WIP", "Lasser Falta de SubEnsamble", "Lectra Falta de SubEnsamble", "Maquinado Falta de SubEnsamble", "Materia Prima Defectuosa", "Materiales no Solicitados a Tiempo", "Moldeo Falta de SubEnsamble", "Pedal/ Botón no funciona", "Prepar Falta de SubEnsamble", "WDL Falta de Surtido de Almacén"],
    "Method": ["Método Ineficiente", "Método Inexistente", "Prueba Piloto", "Validación de Equipo", "Validación de Materiales"],
    "Personal": ["Auditorías", "Ausencia", "Baños", "Cambio de Módulo", "Despeje/cambio de modelo/Cambio de orden", "Enfermería", "Entrenamiento", "Inventarios", "Juntas", "Recursos Humanos", "Término de Turno"],
    "Service": ["Aire Comprimido", "Corriente Eléctrica", "Intranet", "Programa de Computadora"]
}

LABOR_OPTIONS = ["Enfermería", "Recursos Humanos", "Auditorías", "Inventarios", "Entrenamiento", "Juntas", "Baños", "Cambio de Módulo", "Ausencia", "Término de Turno", "Falta de Personal", "Espera de Técnico Disponible", "Despeje/cambio de modelo/Cambio de orden"]

async def run_seed():
    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        try:
            logger.info("🌱 Starting Robust MES Seeding...")
            for cat, reasons in DOWNTIME_CATEGORIES.items():
                for r in reasons:
                    res = await session.execute(select(DowntimeReason).where(DowntimeReason.name == r, DowntimeReason.company_id == COMPANY_A_ID))
                    if not res.scalar_one_or_none():
                        code = f"{cat[:3].upper()}-{r[:10].replace(' ', '').upper()}"
                        session.add(DowntimeReason(code=code[:20], name=r, category=cat, company_id=COMPANY_A_ID, created_by=SYSTEM_USER_ID))
            
            for l in LABOR_OPTIONS:
                res = await session.execute(select(LaborType).where(LaborType.name == l, LaborType.company_id == COMPANY_A_ID))
                if not res.scalar_one_or_none():
                    session.add(LaborType(name=l, description=f"Actividad de {l}", company_id=COMPANY_A_ID, created_by=SYSTEM_USER_ID))
            
            await session.commit()
            logger.info("✅ Robust MES Seeding Completed.")
        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Error: {e}")
        finally:
            await session.close()

if __name__ == "__main__":
    asyncio.run(run_seed())
