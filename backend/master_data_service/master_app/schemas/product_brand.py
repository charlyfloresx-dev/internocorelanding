import uuid
from pydantic import BaseModel, ConfigDict

class BrandBase(BaseModel):
    name: str
    code: str
    translation_key: str | None = None

class BrandCreate(BrandBase):
    pass

class BrandUpdate(BrandBase):
    pass

class BrandRead(BrandBase):
    id: uuid.UUID
    company_id: uuid.UUID | None = None
    model_config = ConfigDict(from_attributes=True)
