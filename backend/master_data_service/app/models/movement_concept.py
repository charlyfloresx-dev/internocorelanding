import enum
from sqlalchemy import String, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column
from common.models import MultiTenantBase

from common.models import BaseMovementConcept

class MovementConcept(BaseMovementConcept):
    __tablename__ = "movement_concepts"

    requires_external_entity: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_target_warehouse: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<MovementConcept(name='{self.name}', type='{self.type}')>"
