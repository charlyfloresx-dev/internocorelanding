import uuid
from pydantic import BaseModel, ConfigDict

class CategoryBase(BaseModel):
    name: str
    code: str
    translation_key: str | None = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(CategoryBase):
    pass

class CategoryRead(CategoryBase):
    id: uuid.UUID
    company_id: uuid.UUID | None = None
    model_config = ConfigDict(from_attributes=True)