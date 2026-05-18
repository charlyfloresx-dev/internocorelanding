import uuid as _uuid
import logging as _logging

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from common.config import settings

_rls_log = _logging.getLogger("security.rls")

# Unified Database Engine with industrial pooling settings
engine = create_async_engine(settings.ASYNC_DATABASE_URL, pool_pre_ping=True, pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    echo=False)

# Unified Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def get_db():
    """Generic dependency for database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

from sqlalchemy import event
from sqlalchemy.orm import with_loader_criteria, Session, ORMExecuteState
from common.context import request_context
from common.infrastructure.models.base import MultiTenantBase

# --- PROTECCIÓN DE LECTURA (Selects, Joins, Subqueries) ---
@event.listens_for(Session, "do_orm_execute")
def _add_global_tenant_filter(execute_state: ORMExecuteState):
    """
    Interceptor Global: Inyecta automatically 'where company_id = X' 
    en cada consulta ORM que involucre entidades MultiTenant.
    """
    ctx = request_context.get()
    
    if ctx and ctx.company_id and not execute_state.execution_options.get("ignore_tenant_filter", False):
        company_id_val = ctx.company_id
        execute_state.statement = execute_state.statement.options(
            with_loader_criteria(
                MultiTenantBase,
                lambda cls: cls.company_id == company_id_val,
                include_aliases=True,
                track_closure_variables=False
            )
        )

# --- PROTECCIÓN DE ESCRITURA (Inserts) ---
@event.listens_for(Session, "before_flush")
def _force_tenant_on_create(session, flush_context, instances):
    """
    Interceptor de Escritura: Garantiza que el company_id asignado sea 
    siempre el del contexto seguro, ignorando cualquier input del cliente.
    """
    ctx = request_context.get()
    
    if ctx and ctx.company_id:
        # Revisamos los objetos nuevos en la sesión
        for obj in session.new:
            if isinstance(obj, MultiTenantBase):
                # Hard-reset del company_id al valor del token/contexto
                obj.company_id = ctx.company_id

# --- INFRAESTRUCTURA RLS (Fase 5) ---
@event.listens_for(engine.sync_engine, "checkout")
def set_tenant_on_checkout(dbapi_connection, connection_record, connection_proxy):
    """
    Establece el company_id en la variable de sesión de Postgres al tomar 
    una conexión del pool. Es vital limpiar la variable si no hay contexto
    para evitar el leakage en conexiones recicladas.
    """
    ctx = request_context.get()
    cursor = dbapi_connection.cursor()
    try:
        if ctx and ctx.company_id:
            # Validar UUID estrictamente antes de interpolarlo — previene inyección SQL
            tenant_str = str(_uuid.UUID(str(ctx.company_id)))
            cursor.execute(f"SET LOCAL app.current_tenant = '{tenant_str}';")
        else:
            # Reseteo de seguridad: evita que una conexión reciclada herede el tenant anterior
            cursor.execute("RESET app.current_tenant;")
    except Exception as e:
        # RLS falló — invalidar la conexión para que NO vuelva al pool contaminada
        _rls_log.critical(
            "[RLS_FAILURE] Tenant isolation set failed — invalidating connection. error=%s", e
        )
        connection_record.invalidate()
        raise  # 500 explícito es preferible a un data leak silencioso
    finally:
        cursor.close()
