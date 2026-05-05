import asyncio
from common.testing.auth_client import InternoAuthClient
import logging
logging.basicConfig(level=logging.INFO)

async def main():
    headers = await InternoAuthClient.get_authenticated_headers(
        email="charly@internocore.com", 
        password="password123",
        auth_url="http://localhost:8001/api/v1/auth"
    )
    print("\n[Auth Headers Obtenidos]:")
    print(headers)

asyncio.run(main())
