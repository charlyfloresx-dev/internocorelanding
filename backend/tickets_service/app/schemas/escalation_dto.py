from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Optional

class EscalationRuleRead(BaseModel):
    id: UUID
    area: str
    level: int
    role_name: str
    sla_minutes: int
    notification_channel: str
    company_id: UUID

    model_config = ConfigDict(from_attributes=True)
