import uuid
from typing import Generic, TypeVar, Optional, List, Type, Any
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from common.models import BaseEntity
from common.context import request_context

T = TypeVar("T", bound=BaseEntity)

class BaseRepository(Generic[T]):
    """
    Generic Base Repository.
    IMPLEMENTS:
    - Automatic Multi-tenant Isolation (via ContextVar).
    - Soft Delete Management (is_active).
    - Parameterized queries (SQLAlchemy 2.0).
    - Automatic Auditing (created_by, updated_by).
    """

    def __init__(self, model: Type[T], db: AsyncSession):
        self.model = model
        self.db = db

    def _get_context(self):
        """Retrieves the current user context from the middleware."""
        return request_context.get()

    def _apply_tenant_filter(self, query, bypass_tenant: bool = False):
        """
        Applies company filter automatically if context exists.
        Secure by Default: Only omitted if bypass_tenant=True.
        """
        if bypass_tenant:
            return query
            
        context = self._get_context()
        if context and context.company_id and hasattr(self.model, "company_id"):
            # ALLOW viewing both company records and global records (NULL)
            from sqlalchemy import or_
            return query.where(
                or_(
                    self.model.company_id == context.company_id,
                    self.model.company_id == None
                )
            )
        return query

    async def get(self, id: uuid.UUID, bypass_tenant: bool = False) -> Optional[T]:
        """Gets a record by ID ensuring tenant context (unless bypass)."""
        query = select(self.model).where(self.model.id == id)
        if hasattr(self.model, "is_active"):
            query = query.where(self.model.is_active == True)
            
        query = self._apply_tenant_filter(query, bypass_tenant=bypass_tenant)
        
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_email(self, email: str, bypass_tenant: bool = False) -> Optional[T]:
        """Searches by email within the tenant (unless bypass)."""
        if not hasattr(self.model, "email"):
            return None
            
        query = select(self.model).where(self.model.email == email)
        if hasattr(self.model, "is_active"):
            query = query.where(self.model.is_active == True)
            
        query = self._apply_tenant_filter(query, bypass_tenant=bypass_tenant)
        
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_name(self, name: str, bypass_tenant: bool = False) -> Optional[T]:
        """Searches by name (unless bypass)."""
        if not hasattr(self.model, "name"):
            return None
            
        query = select(self.model).where(self.model.name == name)
        if hasattr(self.model, "is_active"):
            query = query.where(self.model.is_active == True)
            
        query = self._apply_tenant_filter(query, bypass_tenant=bypass_tenant)
        
        result = await self.db.execute(query)
        return result.scalars().first()

    async def list(self, skip: int = 0, limit: int = 100, bypass_tenant: bool = False) -> List[T]:
        """Lists active records applying automatic tenant filter (unless bypass)."""
        query = select(self.model)
        if hasattr(self.model, "is_active"):
            query = query.where(self.model.is_active == True)
            
        query = self._apply_tenant_filter(query, bypass_tenant=bypass_tenant)
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, obj_in: Any) -> T:
        """Creates a new record injecting company_id and created_by from context."""
        obj_data = obj_in.model_dump() if hasattr(obj_in, "model_dump") else obj_in
        
        db_obj = self.model(**obj_data)
        
        context = self._get_context()
        if context:
            # Tenant Injection
            if hasattr(db_obj, "company_id") and context.company_id:
                db_obj.company_id = context.company_id
                
            # Audit Injection
            if hasattr(db_obj, "created_by") and context.user_id:
                db_obj.created_by = context.user_id
                
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(self, db_obj: T, obj_in: Any) -> T:
        """Updates an existing record injecting updated_by."""
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
        """Soft Delete (if is_active exists) or Hard Delete."""
        # First get the object to ensure it belongs to the tenant (via get())
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
