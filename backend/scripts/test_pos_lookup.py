import asyncio
import httpx
import json

AUTH_URL = "http://localhost:8000/api/v1/auth/login"
SELECT_URL = "http://localhost:8000/api/v1/auth/select-company"
LOOKUP_URL = "http://localhost:8000/api/v1/master/products/lookup/ECM-600" # Notice the endpoint might be /api/v1/master-data/products or /api/v1/master/products

async def run_test():
    async with httpx.AsyncClient() as client:
        # 1. Login
        print("Logging in...")
        res = await client.post(AUTH_URL, json={"email": "charly@interno.com", "password": "charly123"})
        if res.status_code != 200:
            print("Login failed:", res.text)
            return
        
        data = res.json()["data"]
        sel_token = data["selection_token"]
        target_company = next(c for c in data["companies"] if "Enterprise" in c["company_name"])
        company_id = target_company["company_id"]
        
        # 2. Select Company
        print("Selecting company...")
        headers = {"Authorization": f"Bearer {sel_token}", "X-Selection-Token": sel_token}
        res2 = await client.post(SELECT_URL, json={"company_id": company_id}, headers=headers)
        if res2.status_code != 200:
            print("Select failed:", res2.text)
            return
        
        token = res2.json()["data"]["access_token"]
        
        # 3. Lookup Product
        print("Looking up product ECM-600...")
        headers = {"Authorization": f"Bearer {token}", "X-Company-ID": company_id}
        # First try master-data
        res3 = await client.get("http://localhost:8000/api/v1/master-data/products/lookup/ECM-600", headers=headers)
        if res3.status_code == 404:
            res3 = await client.get("http://localhost:8000/api/v1/master/products/lookup/ECM-600", headers=headers)
        
        if res3.status_code == 200:
            print("SUCCESS! Data:")
            print(json.dumps(res3.json()["data"], indent=2))
        else:
            print("Failed to lookup:", res3.status_code, res3.text)

if __name__ == "__main__":
    asyncio.run(run_test())
