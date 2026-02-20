from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

# 1. Esquema Base (Campos comunes)
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    sku: str
    company_id: UUID
    is_active: bool = True

# 2. Esquema para Crear (Cuando llega del API)
class ProductCreate(ProductBase):
    pass

# 3. Esquema para Leer (Lo que regresa el API)
class ProductRead(ProductBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# 4. Esquema para Leer con Versiones (El que te faltaba)
class ProductReadWithVersions(ProductRead):
    # Aquí iría una lista de esquemas de versión, 
    # por ahora lo dejamos como lista genérica para que el import pase.
    versions: List[dict] = []