import uuid
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from common.models import MultiTenantBase

class ScrapEntry(MultiTenantBase):
    __tablename__ = "mes_scrap_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    production_run_id = Column(UUID(as_uuid=True), ForeignKey("mes_production_runs.id"), nullable=False)
    reason_code = Column(String(50), nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    operator_id = Column(String(50), nullable=True) # Optional operator reference

    def __repr__(self):
        return f"<ScrapEntry(run={self.production_run_id}, qty={self.quantity}, reason='{self.reason_code}')>"
