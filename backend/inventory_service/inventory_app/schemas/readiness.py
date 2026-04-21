from typing import List
from pydantic import BaseModel, ConfigDict
import uuid

class InventoryReadinessStep(BaseModel):
    task: str
    is_completed: bool
    action_link: str
    importance: str  # "Critical", "High", "Low"

class InventoryReadinessDto(BaseModel):
    company_id: uuid.UUID
    is_ready: bool
    steps: List[InventoryReadinessStep]

    model_config = ConfigDict(from_attributes=True)
