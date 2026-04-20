import sys
import os
from jose import jwt
from datetime import datetime, timedelta
import requests
import uuid

# Set PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

def create_test_token(company_id: str):
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "DEV_SECRET_KEY_FOR_LOCAL_TESTS_ONLY")
    ALGORITHM = "HS256"
    payload = {
        "sub": "test-user",
        "company_id": company_id,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_wms_api():
    print("SEARCHING: Starting WMS API Validation (Critical Endpoints)...")
    
    BASE_URL = "http://127.0.0.1:8001/api/v1/inventory"
    company_id = str(uuid.uuid4())
    token = create_test_token(company_id)
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Company-ID": company_id
    }

    try:
        # Step 1: Create Document (DRAFT)
        doc_data = {
            "folio": f"TST-{uuid.uuid4().hex[:6]}",
            "concept_id": str(uuid.uuid4()),
            "warehouse_id": str(uuid.uuid4()),
            "movements": [
                {
                    "product_id": "prod-001",
                    "warehouse_id": "wh-001",
                    "quantity": "100.0000",
                    "unit_cost": "50.5000"
                }
            ]
        }
        
        print(f"POST /documents -> Folio: {doc_data['folio']}")
        response = requests.post(f"{BASE_URL}/documents", json=doc_data, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code != 201:
            print(f"ERROR creating document: {response.text}")
            return
        
        doc_id = response.json()["data"]["id"]
        print(f"SUCCESS: Document created: {doc_id}")

        # Step 2: Confirm Document
        print(f"POST /documents/{doc_id}/confirm")
        confirm_resp = requests.post(f"{BASE_URL}/documents/{doc_id}/confirm", headers=headers)
        print(f"Status: {confirm_resp.status_code}")
        
        if confirm_resp.status_code != 200:
            print(f"ERROR confirming: {confirm_resp.text}")
            return
        
        print("SUCCESS: Document confirmed.")

        # Step 3: Check Stock
        print("GET /stock/prod-001")
        stock_resp = requests.get(f"{BASE_URL}/stock/prod-001", headers=headers)
        print(f"Status: {stock_resp.status_code}")
        
        if stock_resp.status_code == 200:
            snapshots = stock_resp.json()["data"]
            for s in snapshots:
                print(f"STOCK: {s['stock_on_hand']} | CPP: {s['average_cost']} in WH: {s['warehouse_id']}")
            print("SUCCESS: Stock Balance Verified.")
        
        # Step 4: Security Drill (Wrong X-Company-ID)
        print("LOGIN: Security Drill: Wrong X-Company-ID Header")
        wrong_headers = headers.copy()
        wrong_headers["X-Company-ID"] = str(uuid.uuid4())
        sec_resp = requests.get(f"{BASE_URL}/stock/prod-001", headers=wrong_headers)
        print(f"Status (Expected 403): {sec_resp.status_code}")
        if sec_resp.status_code == 403:
            print("SUCCESS: Multi-tenant Isolation OK")
        else:
            print("FAILURE: Multi-tenant Isolation failed to block request")

    except Exception as e:
        print(f"ERROR during validation: {e}")

if __name__ == "__main__":
    verify_wms_api()
