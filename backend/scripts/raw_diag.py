import httpx
import asyncio

BASE_URL_AUTH = "http://localhost:8001"
DEMO_USER = "admin@interno.com"
DEMO_PASS = "admin123456"

async def run():
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{BASE_URL_AUTH}/api/v1/auth/login", json={
            "email": DEMO_USER,
            "password": DEMO_PASS
        })
        data = r.json()["data"]
        tok = data["selection_token"]
        cid = data["companies"][0]["company_id"]
        print(f"Selection Token: {tok}")
        print(f"Company ID: {cid}")
        
        r2 = await c.post(f"{BASE_URL_AUTH}/api/v1/auth/select-company", 
                         json={"company_id": cid}, 
                         headers={"Authorization": f"Bearer {tok}"})
        print(f"Status: {r2.status_code}")
        print(f"Body: {r2.text}")

if __name__ == "__main__":
    asyncio.run(run())
