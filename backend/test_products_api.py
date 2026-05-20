import httpx
import asyncio

async def test_api():
    async with httpx.AsyncClient() as client:
        # 1. Login
        login_payload = {
            "email": "charly@interno.com",
            "password": "charly123"
        }
        res = await client.post("http://auth-service:8001/api/v1/auth/login", json=login_payload)
        print("Login status:", res.status_code)
        if res.status_code != 200:
            print("Login failed:", res.text)
            return
        
        token_data = res.json()
        token = token_data.get("data", {}).get("access_token") or token_data.get("access_token")
        if not token:
            print("No access token in response:", token_data)
            return
            
        print("Obtained token successfully")
        
        # 2. Get Products
        headers = {
            "Authorization": f"Bearer {token}",
            "x-company-id": "9cd9986b-89da-48b7-8733-26a2a1225b01"
        }
        
        print("\n--- GET /api/v1/products ---")
        res_prod = await client.get("http://master-data-service:8003/api/v1/products", headers=headers)
        print("Status Code:", res_prod.status_code)
        if res_prod.status_code == 200:
            prod_data = res_prod.json()
            products = prod_data.get("data", [])
            print(f"Loaded {len(products)} products successfully!")
            if products:
                print("First product sample:", {
                    "id": products[0].get("id"),
                    "name": products[0].get("name"),
                    "sku": products[0].get("sku"),
                    "last_price": products[0].get("last_price")
                })
        else:
            print("Error details:", res_prod.text)

        print("\n--- GET /api/v1/products?q=GAR ---")
        res_q = await client.get("http://master-data-service:8003/api/v1/products?q=GAR", headers=headers)
        print("Status Code:", res_q.status_code)
        if res_q.status_code == 200:
            q_data = res_q.json()
            products_q = q_data.get("data", [])
            print("Search Results count:", len(products_q))
            for p in products_q:
                print(f"Match: SKU={p.get('sku')} | Name={p.get('name')} | Price={p.get('last_price')}")
        else:
            print("Error details:", res_q.text)

if __name__ == "__main__":
    asyncio.run(test_api())
