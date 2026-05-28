import uuid
from pydantic import BaseModel, ConfigDict


class ScanPatternRead(BaseModel):
    """Lightweight DTO received from master_data_service scan-patterns endpoint."""
    id: uuid.UUID
    item_code: str
    pattern_name: str
    regex: str
    error_message: str
    priority: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
