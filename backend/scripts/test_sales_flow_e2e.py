import asyncio
import uuid
import httpx
import json

# Configuration
AUTH_URL = "http://localhost:8001/api/v1/auth/login"
WMS_URL = "http://localhost:8007/api/v1/sales"
INV_URL = "http://localhost:8006/api/v1/inventory"

async def test_sales_flow():
    print("[*] Starting Sales Flow E2E Test")
    
    # 1. Login to get token and company context
    # Note: Using credentials from seed
    async with httpx.AsyncClient() as client:
        print("[*] Logging in...")
        login_res = await client.post(AUTH_URL, json={"email": "admin@interno.com", "password": "admin123456"})
        if login_res.status_code != 200:
             print(f"[!] Login failed: {login_res.text}")
             return
        
        login_data = login_res.json()["data"]
        sel_token = login_data["selection_token"]
        target_company = next((c for c in login_data["companies"] if "Logistic" in c["company_name"] or "Logistics" in c["company_name"] or "Tijuana" in c["company_name"]), login_data["companies"][0])
        company_id = target_company["company_id"]
        
        print(f"[*] Selecting Company: {target_company['company_name']} ({company_id})...")
        select_headers = {"Authorization": f"Bearer {sel_token}", "X-Selection-Token": sel_token}
        select_res = await client.post("http://localhost:8001/api/v1/auth/select-company", json={"company_id": company_id}, headers=select_headers)
        if select_res.status_code != 200:
             print(f"[!] Select Company failed: {select_res.text}")
             return
        
        token = select_res.json()["data"]["access_token"]
        
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Company-ID": company_id
        }
        print(f"[*] Authenticated. Company ID: {company_id}")

        # 2. Get Product and Warehouse from Seed (Logistic Demo)
        # We assume SKU-100 and WH-TIJ exist from seed_demo_logistic
        # For the test, we'll try to find any product and warehouse
        print("[*] Fetching available variants...")
        # Since we don't have a direct products endpoint here, let's use fixed IDs if known, 
        # or mock the IDs for internal service-to-service testing if localhost is not up.
        
        product_id = "00000000-0000-0000-0000-000000000101" # SKU-100 from seed
        warehouse_id = "00000000-0000-0000-0000-000000000201" # WH-TIJ from seed
        uom_id = "00000000-0000-0000-0000-000000000001"

        # 3. Step B: Query Price and Stock
        print(f"[*] Querying Price and Stock for Product {product_id}...")
        res = await client.get(f"{WMS_URL}/price-stock?product_id={product_id}&warehouse_id={warehouse_id}", headers=headers)
        print(f"[*] Query Result: {json.dumps(res.json(), indent=2)}")
        
        initial_stock = res.json().get("stock_on_hand", 0)
        initial_reserved = res.json().get("stock_reserved", 0)

        # 4. Step C: Create Sales Order (Triggers Reserve)
        print("[*] Creating Sales Order (10 units)...")
        order_payload = {
            "folio": f"TEST-SO-{uuid.uuid4().hex[:6]}",
            "product_id": product_id,
            "warehouse_id": warehouse_id,
            "uom_id": uom_id,
            "quantity": 10,
            "observations": "E2E Test Order"
        }
        res_order = await client.post("http://localhost:8007/api/v1/sales-orders/", json=order_payload, headers=headers)
        if res_order.status_code != 200:
            print(f"[!] Order creation failed: {res_order.text}")
            return
        
        order_id = res_order.json()["id"]
        print(f"[*] Order Created: {order_id} (Status: {res_order.json()['status']})")

        # 5. Verify Reservation
        print("[*] Verifying reservation in Inventory Service...")
        res_stock = await client.get(f"{WMS_URL}/price-stock?product_id={product_id}&warehouse_id={warehouse_id}", headers=headers)
        new_reserved = res_stock.json().get("stock_reserved", 0)
        print(f"[*] New Reserved Stock: {new_reserved} (Expected: {initial_reserved + 10})")

        # 6. Step D: Dispatch (Triggers Out and Fulfills Reserve)
        print(f"[*] Dispatching Order {order_id}...")
        dispatch_payload = {
            "sales_order_id": order_id,
            "warehouse_id": warehouse_id
        }
        res_dispatch = await client.post(f"{WMS_URL}/dispatch", json=dispatch_payload, headers=headers)
        if res_dispatch.status_code != 200:
            print(f"[!] Dispatch failed: {res_dispatch.text}")
            return
        
        print(f"[*] Dispatch Successful. Order Status: {res_dispatch.json()['status']}")

        # 7. Final Verification
        print("[*] Final Stock Check...")
        res_final = await client.get(f"{WMS_URL}/price-stock?product_id={product_id}&warehouse_id={warehouse_id}", headers=headers)
        final_stock = res_final.json().get("stock_on_hand", 0)
        final_reserved = res_final.json().get("stock_reserved", 0)
        
        print(f"[*] Final Stock: {final_stock} (Expected: {initial_stock - 10})")
        print(f"[*] Final Reserved: {final_reserved} (Expected: {initial_reserved})")
        
        if final_stock == initial_stock - 10 and final_reserved == initial_reserved:
            print("✅ E2E Sales Flow Successful!")
        else:
            print("❌ E2E Sales Flow Failed Data Integrity.")

if __name__ == "__main__":
    asyncio.run(test_sales_flow())
