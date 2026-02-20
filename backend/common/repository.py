import uuid
from typing import Generic, TypeVar, Optional, List, Type, Any
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from common.models.base_models import BaseEntity, MultiTenantBase

T = TypeVar("T", bound=BaseEntity)

class BaseRepository(Generic[T]):
    """
    Repositorio Base Genérico.
    IMPLEMENTA:
    - Aislamiento Multi-tenant (company_id).
    - Gestión de Soft Delete (is_active).
    - Consultas parametrizadas (SQLAlchemy 2.0).
    """

    def __init__(self, model: Type[T], db: AsyncSession, company_id: Optional[uuid.UUID] = None):
        self.model = model
        self.db = db
        self.company_id = company_id
        self.is_multitenant = issubclass(model, MultiTenantBase)

    def _apply_tenant_filter(self, query):
        """Aplica el filtro de compañía si el modelo es MultiTenant."""
        if self.is_multitenant and self.company_id:
            return query.filter(self.model.company_id == self.company_id)
        return query

    async def get(self, id: uuid.UUID) -> Optional[T]:
        """Obtiene un registro por ID asegurando el contexto de tenant."""
        query = select(self.model).where(self.model.id == id, self.model.is_active == True)
        query = self._apply_tenant_filter(query)
        
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_email(self, email: str) -> Optional[T]:
        """Busca por email dentro del tenant (si el modelo tiene el campo email)."""
        if not hasattr(self.model, "email"):
            return None
            
        query = select(self.model).where(self.model.email == email, self.model.is_active == True)
        query = self._apply_tenant_filter(query)
        
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_name(self, name: str) -> Optional[T]:
        """Busca por nombre (si el modelo tiene el campo name)."""
        if not hasattr(self.model, "name"):
            return None
            
        query = select(self.model).where(self.model.name == name, self.model.is_active == True)
        query = self._apply_tenant_filter(query)
        
        result = await self.db.execute(query)
        return result.scalars().first()

    async def list(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Lista registros activos aplicando el tenant filter."""
        query = select(self.model).where(self.model.is_active == True)
        query = self._apply_tenant_filter(query)
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, obj_in: Any) -> T:
        """Crea un nuevo registro inyectando el company_id automáticamente."""
        obj_data = obj_in.model_dump() if hasattr(obj_in, "model_dump") else obj_in
        
        db_obj = self.model(**obj_data)
        
        # Inyección forzada de tenant context
        if self.is_multitenant and self.company_id:
            db_obj.company_id = self.company_id
            
        self.db.add(db_obj)
        await self.db.flush()
        return db_obj

    async def update(self, db_obj: T, obj_in: Any) -> T:
        """Actualiza un registro existente."""
        obj_data = obj_in.model_dump(exclude_unset=True) if hasattr(obj_in, "model_dump") else obj_in
        
        for field in obj_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, obj_data[field])
        
        self.db.add(db_obj)
        await self.db.flush()
        return db_obj

    async def delete(self, id: uuid.UUID) -> bool:
        """Soft Delete: Marca el registro como inactivo."""
        query = update(self.model).where(self.model.id == id)
        query = self._apply_tenant_filter(query)
        query = query.values(is_active=False)
        
        result = await self.db.execute(query)
        await self.db.flush()
        return result.rowcount > 0
