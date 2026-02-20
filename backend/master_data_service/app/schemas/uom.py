import uuid
from pydantic import BaseModel, ConfigDict

class UOMBase(BaseModel):
    code: str
    name: str
    plural: str | None = None
    translation_key: str | None = None

class UOMCreate(UOMBase):
    pass

class UOMUpdate(UOMBase):
    # Permitir actualizaciones parciales
    code: str | None = None
    name: str | None = None

class UOMRead(UOMBase):
    id: uuid.UUID
    company_id: uuid.UUID | None = None
    model_config = ConfigDict(from_attributes=True)