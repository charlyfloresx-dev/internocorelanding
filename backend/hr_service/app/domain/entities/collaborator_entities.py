from dataclasses import dataclass
from typing import Optional
from uuid import UUID

@dataclass
class Collaborator:
    id: UUID
    company_id: UUID
    internal_id: str
    full_name: str
    rfid_tag: Optional[str] = None
    pin_code: Optional[str] = None
    home_warehouse_id: Optional[UUID] = None
    is_supervisor: bool = False
    tenant_id: Optional[UUID] = None
    photo_path: Optional[str] = None
