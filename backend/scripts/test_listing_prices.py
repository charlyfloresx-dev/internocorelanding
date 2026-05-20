import asyncio
import httpx
import json

AUTH_URL = "http://localhost:8000/api/v1/auth/login"
SELECT_URL = "http://localhost:8000/api/v1/auth/select-company"

async def run_test():
    async with httpx.AsyncClient(follow_redirects=True) as client:
        # 1. Login
        res = await client.post(AUTH_URL, json={"email": "charly@interno.com", "password": "charly123"})
        if res.status_code != 200:
            print("Login failed:", res.text)
            return
        
        data = res.json()["data"]
        sel_token = data["selection_token"]
        target_company = next(c for c in data["companies"] if "Enterprise" in c["company_name"])
        company_id = target_company["company_id"]
        
        # 2. Select Company
        headers = {"Authorization": f"Bearer {sel_token}", "X-Selection-Token": sel_token}
        res2 = await client.post(SELECT_URL, json={"company_id": company_id}, headers=headers)
        if res2.status_code != 200:
            print("Select failed:", res2.text)
            return
        
        token = res2.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}", "X-Company-ID": company_id}
        
        # 3. List Products
        print("Fetching products list...")
        res3 = await client.get("http://localhost:8000/api/v1/products", headers=headers)
        print(f"Status Code: {res3.status_code}")
        if res3.status_code == 200:
            products = res3.json()["data"]
            for p in products:
                print(f"SKU: {p.get('sku')} | Name: {p.get('name')} | Last Price: {p.get('last_price')} | Currency: {p.get('currency')}")

if __name__ == "__main__":
    asyncio.run(run_test())
