import httpx
import asyncio
import uuid
import json
from datetime import datetime

import os

# Detect if running inside Docker
IN_DOCKER = os.path.exists('/.dockerenv')

if IN_DOCKER:
    AUTH_URL = "http://auth-service-api:8000/api/v1"
    INV_URL = "http://localhost:8000/api/v1"
    MD_URL = "http://master-data-service-api:8000/api/v1"
else:
    AUTH_URL = "http://localhost:8001/api/v1"
    INV_URL = "http://localhost:8006/api/v1"
    MD_URL = "http://localhost:8003/api/v1"

# Shorthand for compatibility with rest of the script if needed
AUTH_URL = AUTH_URL
INVENTORY_URL = INV_URL
MASTER_URL = MD_URL

USER_EMAIL = "charly@interno.com"
USER_PWD = "charly123"

# IDs from seed
CORP_ENT_ID = "9cd9986b-89da-48b7-8733-26a2a1225b01"
LOGISTICS_ID = "ad6cc8a6-34f9-42df-8f29-28254e0ad242"
PRODUCT_SKU = "MAT-001"
UOM_PZ_CODE = "PZ"

async def test_ict_mirror():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Login
        print(f"Logging in as {USER_EMAIL}...")
        login_res = await client.post(f"{AUTH_URL}/auth/login", json={
            "email": USER_EMAIL,
            "password": USER_PWD
        })
        if login_res.status_code != 200:
            print(f"Login failed: {login_res.text}")
            return
        
        # El login devuelve handshake (lista de empresas)
        handshake = login_res.json()
        print(f"Handshake successful. Received {len(handshake['data']['companies'])} companies.")

        # 2. Select Company A (InternoCorp Enterprise)
        print(f"Selecting company A: {CORP_ENT_ID}")
        sel_res = await client.post(f"{AUTH_URL}/auth/select-company", json={
            "company_id": CORP_ENT_ID
        }, headers={"Authorization": f"Bearer {handshake['data']['selection_token']}"})
        
        if sel_res.status_code != 200:
            print(f"Select company A failed: {sel_res.text}")
            return
        
        token_a = sel_res.json()['data']['access_token']
        headers_a = {
            "Authorization": f"Bearer {token_a}",
            "X-Company-ID": CORP_ENT_ID
        }

        # 3. Get Resources in A (Warehouse, Product, UOM)
        # Getting Warehouse
        wh_res_a = await client.get(f"{MD_URL}/warehouses/", headers=headers_a)
        warehouses_a = wh_res_a.json()['data']
        origin_wh = next((w for w in warehouses_a if w['code'] == 'WH-TIJ'), warehouses_a[0])
        print(f"Origin WH: {origin_wh['name']} ({origin_wh['id']})")

        # Getting Product MAT-001
        prod_res_a = await client.get(f"{MD_URL}/products/", headers=headers_a)
        products_a = prod_res_a.json()['data']
        product_a = next((p for p in products_a if p['sku'] == PRODUCT_SKU), None)
        if not product_a:
            print(f"Product {PRODUCT_SKU} not found in A")
            return
        print(f"Product A: {product_a['name']} ({product_a['id']})")

        # Getting UOM PZ
        uom_res_a = await client.get(f"{MD_URL}/ums/", headers=headers_a)
        uoms_a = uom_res_a.json()['data']
        uom_a = next((u for u in uoms_a if u['code'] == UOM_PZ_CODE), uoms_a[0])
        print(f"UOM A: {uom_a['name']} ({uom_a['id']})")

        # 4. Ensure Stock in A (Quick Adjustment)
        # Fetching concepts for A
        concepts_res_a = await client.get(f"{MD_URL}/concepts/", headers=headers_a)
        concepts_a = concepts_res_a.json()['data']
        concept_a = next((c for c in concepts_a if c['code'] == 'ENT-ADJ'), concepts_a[0])
        print(f"Using Concept: {concept_a['name']} ({concept_a['id']})")

        print("Ensuring stock in A...")
        adj_res = await client.post(f"{INV_URL}/inventory/transactions", json={
            "warehouse_id": origin_wh['id'],
            "product_id": product_a['id'],
            "uom_id": uom_a['id'],
            "quantity_change": 100.0,
            "weight": 200.0,  # 2kg per item approx
            "transaction_type": "IN",
            "concept_id": concept_a['id'],
            "comments": "Test ICT Mirror Initial Stock"
        }, headers=headers_a)
        
        if adj_res.status_code not in [200, 201]:
            print(f"FAILED: Stock adjustment. Code: {adj_res.status_code}")
            print(f"Response: {adj_res.text[:200]}")
            return
        print(f"SUCCESS: Stock adjustment recorded.")

        # 5. Select Company B (Interno Logistics) to get its Warehouse
        print(f"Action: Selecting company B: {LOGISTICS_ID}")
        sel_res_b = await client.post(f"{AUTH_URL}/auth/select-company", json={
            "company_id": LOGISTICS_ID
        }, headers={"Authorization": f"Bearer {handshake['data']['selection_token']}"})
        
        token_b = sel_res_b.json()['data']['access_token']
        headers_b = {
            "Authorization": f"Bearer {token_b}",
            "X-Company-ID": LOGISTICS_ID
        }

        wh_res_b = await client.get(f"{MD_URL}/warehouses/", headers=headers_b)
        warehouses_b = wh_res_b.json()['data']
        dest_wh = next((w for w in warehouses_b if w['code'] == 'WH-SDY'), warehouses_b[0])
        print(f"Destination WH: {dest_wh['name']} ({dest_wh['id']})")

        # 6. INITIATE TRANSFER (Mirror Logic Trigger)
        print("\n🚀 Initiating Inter-Company Transfer (Mirror Logic Challenge)...")
        ict_body = {
            "destination_company_id": LOGISTICS_ID,
            "destination_warehouse_id": dest_wh['id'],
            "origin_warehouse_id": origin_wh['id'],
            "product_id": product_a['id'],
            "uom_id": uom_a['id'],
            "quantity": 25,
            "notes": "Mirror Logic Validation Test",
            "transfer_price": 45.50
        }
        
        ict_res = await client.post(f"{INV_URL}/transfers/inter-company/initiate", json=ict_body, headers=headers_a)
        if ict_res.status_code != 201:
            print(f"ICT Initiation failed: {ict_res.text}")
            return
        
        ict_data = ict_res.json()['data']
        print(f"✅ ICT Initiated. Folio: {ict_data['folio']}")
        print(f"   Mirror Document ID: {ict_data.get('mirror_document_id')}")

        # 7. VALIDATE MIRROR DOCUMENT in Company B
        print("\n🔍 Validating Mirror Document in Company B (Interno Logistics)...")
        # List Documents in Company B
        # Endpoint: GET /inventory/documents/
        docs_res_b = await client.get(f"{INV_URL}/inventory/", headers=headers_b)
        docs_b = docs_res_b.json()['data']
        
        # Find document with matching mirror_document_id or related folio
        mirror_doc = next((d for d in docs_b if d['id'] == ict_data.get('mirror_document_id')), None)
        
        if mirror_doc:
            print(f"⭐ SUCCESS! Mirror Document found in Company B!")
            print(f"   Folio: {mirror_doc['folio']}")
            print(f"   Status: {mirror_doc['status']}")
            print(f"   Origin: {mirror_doc.get('origin_name')}")
        else:
            print("❌ FAILURE: Mirror Document NOT found in Company B.")
            # Print last 5 docs for debugging
            print("Last 5 docs in B:")
            for d in docs_b[:5]:
                print(f" - {d['folio']} ({d['id']}) | Status: {d['status']}")

if __name__ == "__main__":
    asyncio.run(test_ict_mirror())
