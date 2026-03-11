from app.domain.interfaces.master_data_client import IMasterDataClient
from app.infrastructure.clients.master_data import MasterDataClient

async def get_master_data_client() -> IMasterDataClient:
    return MasterDataClient()
