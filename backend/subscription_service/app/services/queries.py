import uuid
from typing import List, Any
from app.domain.repositories.subscription_repository import ISubscriptionRepository
from app.core.enums import ModuleCode


class GetEntitlementsQuery:
    def __init__(self, repo: ISubscriptionRepository):
        self.repo = repo

    async def execute(self, company_id: uuid.UUID):
        entitlements = await self.repo.get_entitlements_by_company(company_id)
        modules = [e.module_code for e in entitlements if e.is_enabled]
        return {
            "modules": modules,
            "can_invite": True
        }


class GetModulePermissionsQuery:
    def __init__(self, repo: ISubscriptionRepository):
        self.repo = repo

    async def execute(self, company_id: uuid.UUID):
        entitlements = await self.repo.get_entitlements_by_company(company_id)

        return {
            "can_use_wms": any(e.module_code == ModuleCode.WMS_CORE and e.is_enabled for e in entitlements),
            "can_use_mes": any(e.module_code == ModuleCode.MES_CORE and e.is_enabled for e in entitlements),
            "can_use_tickets": any(e.module_code == ModuleCode.TICKETS_CORE and e.is_enabled for e in entitlements),
        }
