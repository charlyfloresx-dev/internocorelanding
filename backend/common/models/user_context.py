from pydantic import BaseModel, UUID4
from typing import Optional

class UserContext(BaseModel):
    user_id: str
    company_id: UUID4