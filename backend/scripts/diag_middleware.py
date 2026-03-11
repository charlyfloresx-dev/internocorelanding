import httpx
import json
import asyncio

async def diag():
    url = "http://localhost:8001/api/v1/auth/login"
    async with httpx.AsyncClient() as client:
        # 1. Login
        r = await client.post(url, json={"email": "admin@interno.com", "password": "admin123456"})
        data = r.json()["data"]
        token = data["selection_token"]
        company_id = data["companies"][0]["company_id"]
        
        print(f"Token type selection: {token[:20]}...")
        
        # 2. Select Company
        url_sel = "http://localhost:8001/api/v1/auth/select-company"
        headers = {"Authorization": f"Bearer {token}"}
        r_sel = await client.post(url_sel, json={"company_id": company_id}, headers=headers)
        
        print(f"Status: {r_sel.status_code}")
        print(f"Body: {r_sel.text}")

if __name__ == "__main__":
    asyncio.run(diag())
