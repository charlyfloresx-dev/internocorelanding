import asyncio
import httpx
import json
import uuid

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
        
        # 3. Fetch Warehouses
        res_wh = await client.get("http://localhost:8000/api/v1/warehouses", headers=headers)
        if res_wh.status_code != 200:
            print("Failed to fetch warehouses:", res_wh.text)
            return
        
        warehouses = res_wh.json()["data"]
        warehouse_id = warehouses[0]["id"]
        
        # 4. Create Document with concept_id="ENT-PUR" as a string literal instead of UUID
        correlation_id = str(uuid.uuid4())
        client_request_id = str(uuid.uuid4())
        headers["X-Client-Request-ID"] = client_request_id
        
        doc_payload = {
            "correlation_id": correlation_id,
            "type": "IN",
            "concept_id": "ENT-PUR", 
            "warehouse_id": warehouse_id,
            "external_entity": None,
            "notes": "Testing string concept_id",
            "items": [
                {
                    "sku": "ECM-600",
                    "product_id": "b5e6df8e-a777-5834-bd0f-0181065a3bcd",
                    "quantity": 5.0,
                    "unit_price": 495.0,
                    "currency": "MXN",
                    "location": "SYS_RECEIVING",
                    "weight": 1.5
                }
            ]
        }
        
        print("Sending Create Document Request...")
        res_doc = await client.post("http://localhost:8000/api/v1/inventory/documents", json=doc_payload, headers=headers)
        print(f"Status Code: {res_doc.status_code}")
        try:
            print(json.dumps(res_doc.json(), indent=2))
        except Exception as e:
            print(f"JSON Error: {e}, Text: {res_doc.text}")

if __name__ == "__main__":
    asyncio.run(run_test())
