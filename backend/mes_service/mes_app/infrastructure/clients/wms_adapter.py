from typing import Dict, Any
from mes_app.domain.repositories.interfaces import IWMSClient
from mes_app.infrastructure.wms_client import WMSClient

class SQLAlchemyWMSClient(IWMSClient):
    def __init__(self):
        self._client = WMSClient()
        
    async def check_stock(self, sku: str, company_id: str) -> Dict[str, Any]:
        return await self._client.check_stock(sku, company_id)
