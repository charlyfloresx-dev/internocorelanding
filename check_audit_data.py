import asyncio
import httpx
from common.testing.auth_client import InternoAuthClient

async def check_audit():
    auth_url = "http://localhost:8000/api/v1/auth"
    inventory_url = "http://localhost:8000/api/v1/inventory"
    client = InternoAuthClient(auth_url)
    
    if await client.login("charly@interno.com", "charly123"):
        await client.select_company()
        headers = client.get_headers()
        async with httpx.AsyncClient() as http:
            r = await http.get("http://localhost:8000/api/v1/audit/?limit=10", headers=headers)
            print(f"Status: {r.status_code}")
            if r.status_code == 200:
                data = r.json().get("data", [])
                print(f"Audit Logs found: {len(data)}")
                for log in data:
                    print(f" - [{log['timestamp']}] {log['action']} on {log['table_name']} (ID: {log['record_id']})")
            else:
                print(f"Error: {r.text}")

if __name__ == '__main__':
    asyncio.run(check_audit())
