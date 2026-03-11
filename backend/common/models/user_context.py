import uuid
from pydantic import BaseModel
from typing import Optional

class UserContext(BaseModel):
    user_id: Optional[str] = None
    company_id: Optional[uuid.UUID] = None
    group_id: Optional[uuid.UUID] = None
    trace_id: Optional[str] = None
    token: Optional[str] = None