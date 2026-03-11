import uuid
from typing import Generic, TypeVar, Optional, List, Type, Any
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from common.context import request_context
# Asumimos que MultiTenantBase y BaseEntity están disponibles en common.models
# Si no, se deberían importar de donde estén definidos (ej. common.domain.entities)
# Para este ejemplo, usaremos un check dinámico de atributos.

T = TypeVar("T")

class BaseRepository(Generic[T]):
    """
    Repositorio Base con soporte para Multi-tenancy automático y Auditoría.
    Utiliza ContextVar para inyectar filtros de seguridad sin ensuciar la firma de los métodos.
    """

    def __init__(self, model: Type[T], db: AsyncSession):
        self.model = model
        self.db = db

    def _get_context(self) -> Optional[Any]:
        """Recupera el contexto del usuario actual desde el middleware."""
        # Se devuelve 'Any' para desacoplar de 'UserContext' y evitar importaciones circulares.
        # La estructura real del contexto se valida en el middleware.
        return request_context.get()

    def _get_base_query(self):
        """
        Genera la consulta base aplicando filtros de seguridad (Tenant) y lógicos (Soft Delete).
        """
        query = select(self.model)
        
        # 1. Filtro de Soft Delete (si aplica)
        if hasattr(self.model, "is_active"):
            query = query.where(self.model.is_active == True)

        # 2. Filtro de Multi-tenancy Automático
        context = self._get_context()
        if context and context.company_id and hasattr(self.model, "company_id"):
            # Aplicamos el filtro de compañía automáticamente
            query = query.where(self.model.company_id == context.company_id)
        
        return query

    async def get(self, id: uuid.UUID) -> Optional[T]:
        """Obtiene una entidad por ID, respetando el aislamiento de tenant."""
        query = self._get_base_query().where(self.model.id == id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def list(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Lista entidades del tenant actual."""
        query = self._get_base_query().offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, obj_in: Any) -> T:
        """
        Crea una nueva entidad inyectando company_id y created_by del contexto.
        """
        if hasattr(obj_in, "model_dump"):
            # Para modelos Pydantic, usamos `exclude_unset=True` para no enviar
            # campos no especificados que Pydantic inicializa a None.
            # Esto permite que los valores por defecto de la DB (ej. created_at) funcionen.
            obj_data = obj_in.model_dump(exclude_unset=True)
        else:
            # Si es un diccionario, filtramos explícitamente los valores None.
            obj_data = {k: v for k, v in obj_in.items() if v is not None}

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
        """Actualiza una entidad inyectando updated_by."""
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
        """Soft delete (si existe is_active) o Hard delete."""
        # Nota: Para implementar delete seguro, primero debemos obtener el objeto 
        # usando get() para asegurar que pertenece al tenant, y luego modificarlo.
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