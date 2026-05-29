from common.infrastructure.models.base import Base
from hcm_app.models.collaborator import Collaborator
from hcm_app.models.tenant_settings import HrTenantConfig
from hcm_app.models.department import Department
from hcm_app.models.break_group import BreakGroup, BreakSlot
from common.models.external_contact import ExternalContact

__all__ = ["Base", "Collaborator", "HrTenantConfig", "Department",
           "BreakGroup", "BreakSlot", "ExternalContact"]
