import uuid
from typing import Generic, TypeVar, Optional, List, Type, Any
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from common.models import BaseEntity
from common.context import request_context

T = TypeVar("T", bound=BaseEntity)

class BaseRepository(Generic[T]):
    """
    Repositorio Base Genérico.
    IMPLEMENTA:
    - Aislamiento Multi-tenant Automático (vía ContextVar).
    - Gestión de Soft Delete (is_active).
    - Consultas parametrizadas (SQLAlchemy 2.0).
    - Auditoría Automática (created_by, updated_by).
    """

    def __init__(self, model: Type[T], db: AsyncSession):
        self.model = model
        self.db = db

    def _get_context(self):
        """Recupera el contexto del usuario actual desde el middleware."""
        return request_context.get()

    def _apply_tenant_filter(self, query, bypass_tenant: bool = False):
        """
        Aplica el filtro de compañía automáticamente si existe contexto.
        Secure by Default: Solo se omite si bypass_tenant=True.
        """
        if bypass_tenant:
            return query
            
        context = self._get_context()
        if context and context.company_id and hasattr(self.model, "company_id"):
            # PERMITE ver tanto registros de la compañía como registros globales (NULL)
            from sqlalchemy import or_
            return query.where(
                or_(
                    self.model.company_id == context.company_id,
                    self.model.company_id == None
                )
            )
        return query

    async def get(self, id: uuid.UUID, bypass_tenant: bool = False) -> Optional[T]:
        """Obtiene un registro por ID asegurando el contexto de tenant (salvo bypass)."""
        query = select(self.model).where(self.model.id == id)
        if hasattr(self.model, "is_active"):
            query = query.where(self.model.is_active == True)
            
        query = self._apply_tenant_filter(query, bypass_tenant=bypass_tenant)
        
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_email(self, email: str, bypass_tenant: bool = False) -> Optional[T]:
        """Busca por email dentro del tenant (salvo bypass)."""
        if not hasattr(self.model, "email"):
            return None
            
        query = select(self.model).where(self.model.email == email)
        if hasattr(self.model, "is_active"):
            query = query.where(self.model.is_active == True)
            
        query = self._apply_tenant_filter(query, bypass_tenant=bypass_tenant)
        
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_name(self, name: str, bypass_tenant: bool = False) -> Optional[T]:
        """Busca por nombre (salvo bypass)."""
        if not hasattr(self.model, "name"):
            return None
            
        query = select(self.model).where(self.model.name == name)
        if hasattr(self.model, "is_active"):
            query = query.where(self.model.is_active == True)
            
        query = self._apply_tenant_filter(query, bypass_tenant=bypass_tenant)
        
        result = await self.db.execute(query)
        return result.scalars().first()

    async def list(self, skip: int = 0, limit: int = 100, bypass_tenant: bool = False) -> List[T]:
        """Lista registros activos aplicando el tenant filter automático (salvo bypass)."""
        query = select(self.model)
        if hasattr(self.model, "is_active"):
            query = query.where(self.model.is_active == True)
            
        query = self._apply_tenant_filter(query, bypass_tenant=bypass_tenant)
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, obj_in: Any) -> T:
        """Crea un nuevo registro inyectando company_id y created_by del contexto."""
        obj_data = obj_in.model_dump() if hasattr(obj_in, "model_dump") else obj_in
        
        db_obj = self.model(**obj_data)
        
        context = self._get_context()
        if context:
            # Inyección de Tenant
            if hasattr(db_obj, "company_id") and context.company_id:
                db_obj.company_id = context.company_id
            
            # Inyección de Auditoría
            if hasattr(db_obj, "created_by") and context.user_id:
                db_obj.created_by = context.user_id
            
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(self, db_obj: T, obj_in: Any) -> T:
        """Actualiza un registro existente inyectando updated_by."""
        obj_data = obj_in.model_dump(exclude_unset=True) if hasattr(obj_in, "model_dump") else obj_in
        
        for field in obj_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, obj_data[field])
        
        context = self._get_context()
        if context and hasattr(db_obj, "updated_by") and context.user_id:
            db_obj.updated_by = context.user_id

        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete(self, id: uuid.UUID) -> bool:
        """Soft Delete (si existe is_active) o Hard Delete."""
        # Primero obtenemos el objeto para asegurar que pertenece al tenant (vía get())
        db_obj = await self.get(id)
        if not db_obj:
            return False
            
        if hasattr(db_obj, "is_active"):
            db_obj.is_active = False
            self.db.add(db_obj)
        else:
            await self.db.delete(db_obj)
            
        await self.db.flush()
        return True
