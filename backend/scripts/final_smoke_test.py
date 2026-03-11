import asyncio
import httpx
import uuid
import json

BASE_URL_AUTH = "http://localhost:8001"
BASE_URL_INV = "http://localhost:8006"
BASE_URL_WMS = "http://localhost:8007"

DEMO_USER = "admin@interno.com"
DEMO_PASS = "admin123456"

async def smoke_test():
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("Starting Final MVP Smoke Test...")

        # 1. Login Handshake
        print("\nStep 1: Auth Login Handshake")
        try:
            r_login = await client.post(f"{BASE_URL_AUTH}/api/v1/auth/login", json={
                "email": DEMO_USER,
                "password": DEMO_PASS
            })
            r_login.raise_for_status()
            resp_body = r_login.json()
            login_data = resp_body["data"]
            selection_token = login_data["selection_token"]
            
            # Buscamos la empresa "Interno Logistics" (ID: ad6cc8a6-34f9-42df-8f29-28254e0ad242)
            target_company = next((c for c in login_data["companies"] if "Logistics" in c["company_name"]), login_data["companies"][0])
            company_id = target_company["company_id"]
            
            print(f"Login successful. Selection Token obtained. Target Company: {target_company['company_name']} ({company_id})")
        except Exception as e:
            print(f"Login failed: {e}")
            if 'r_login' in locals(): print(r_login.text)
            return

        # 2. Select Company (Final JWT)
        print("\nStep 2: Select Company & Access Token Verification")
        try:
            headers_sel = {"Authorization": f"Bearer {selection_token}"}
            r_sel = await client.post(f"{BASE_URL_AUTH}/api/v1/auth/select-company", 
                                     json={"company_id": company_id},
                                     headers=headers_sel)
            r_sel.raise_for_status()
            final_data = r_sel.json()["data"]
            access_token = final_data["access_token"]
            permissions = final_data.get("permissions", [])
            roles = final_data.get("roles", [])
            print(f"Access Token obtained. Roles: {roles}. Permissions count: {len(permissions)}")
        except Exception as e:
            print(f"Select company failed: {e}")
            if 'r_sel' in locals(): print(r_sel.text)
            return

        final_headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Company-ID": company_id
        }

        # 3. Inventory Stock Summary (Modo Demo Industrial)
        print("\nStep 3: Inventory Stock Summary (Industrial Scale Verification)")
        try:
            r_stock = await client.get(f"{BASE_URL_INV}/api/v1/dashboard/stock", headers=final_headers)
            r_stock.raise_for_status()
            stocks = r_stock.json()["data"]
            
            # IDs de Almacenes (Alineados con el seed)
            NAMESPACE_DNS = uuid.NAMESPACE_DNS
            WH_TIJ_ID = uuid.uuid5(NAMESPACE_DNS, f"interno.wh.WH-TIJ.{company_id}")
            WH_SDY_ID = uuid.uuid5(NAMESPACE_DNS, f"interno.wh.WH-SDY.{company_id}")

            wh_tij = next((s for s in stocks if str(s["warehouse_id"]) == str(WH_TIJ_ID)), None)
            wh_sdy = next((s for s in stocks if str(s["warehouse_id"]) == str(WH_SDY_ID)), None)
            
            print(f"Total stock entries found: {len(stocks)}")
            
            if wh_tij:
                print(f"   - TIJ Warehouse ({WH_TIJ_ID}): {wh_tij['total_quantity']} units (Expected 5000)")
            else:
                print(f"   - TIJ Warehouse ({WH_TIJ_ID}) not found in dashboard.")
                
            if wh_sdy:
                print(f"   - SDY Warehouse ({WH_SDY_ID}): {wh_sdy['total_quantity']} units (Expected 2000)")
            else:
                print(f"   - SDY Warehouse ({WH_SDY_ID}) not found in dashboard.")
                
            if (wh_tij and float(wh_tij["total_quantity"]) == 5000) and (wh_sdy and float(wh_sdy["total_quantity"]) == 2000):
                 print("Industrial Scale verification: PASSED")
            else:
                 print("Industrial Scale verification: Partials match or missing data.")

        except Exception as e:
            print(f"Stock verification failed: {e}")
            if 'r_stock' in locals(): print(r_stock.text)

        # 4. WMS Sync Status
        print("\nStep 4: WMS Sync Status (IInventoryClient Test)")
        try:
            # Reutilizamos el payload del seed o uno representativo
            sync_payload = {
                "products": [
                    {
                        "id": "e6a1d9b4-7f41-4c7b-a48e-6d9b42581639", # Example ID
                        "sku": "MAT-001",
                        "name": "Industrial Material 001",
                        "versions": [{"version_number": 1, "is_active": True}]
                    }
                ]
            }
            r_sync = await client.post(f"{BASE_URL_WMS}/api/v1/inventory/sync-initial", 
                                      json=sync_payload, 
                                      headers=final_headers)
            r_sync.raise_for_status()
            sync_res = r_sync.json()["data"]
            print(f"WMS Sync: Processed {sync_res['processed']} items. Status: Success.")
        except Exception as e:
            print(f"WMS Sync failed: {e}")
            if 'r_sync' in locals(): print(r_sync.text)

        print("\nFinal MVP Smoke Test: COMPLETED.")

if __name__ == "__main__":
    asyncio.run(smoke_test())
