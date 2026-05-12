import requests
import json

BASE_URL = "http://localhost:8000/api/v1/auth"
CREDENTIALS = {"email": "charly@interno.com", "password": "charly123"}

def test_qr_flow():
    print("\n[START] TESTING QR DELEGATION FLOW")
    print("="*70)

    # --- PASO 1: LOGIN ---
    print("PASO 1: Login...")
    try:
        r_login = requests.post(f"{BASE_URL}/login", json=CREDENTIALS)
        r_login.raise_for_status()
        login_data = r_login.json()["data"]
        sel_token = login_data["selection_token"]
        target_company = login_data["companies"][0]
        print(f"OK: Login successful.")
    except Exception as e:
        print(f"ERR: Step 1 failed: {e}")
        return

    # --- PASO 2: SELECT COMPANY ---
    print(f"PASO 2: Selecting company: {target_company['company_name']}...")
    headers = {"Authorization": f"Bearer {sel_token}"}
    payload = {"company_id": target_company["company_id"]}
    try:
        r_select = requests.post(f"{BASE_URL}/select-company", json=payload, headers=headers)
        r_select.raise_for_status()
        access_token = r_select.json()["data"]["access_token"]
        print(f"OK: Company selected.")
    except Exception as e:
        print(f"ERR: Step 2 failed: {e}")
        return

    # --- PASO 3: DELEGATE SELECTION (QR) ---
    print("PASO 3: Requesting QR Delegation...")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Company-Id": target_company["company_id"]
    }
    try:
        r_delegate = requests.get(f"{BASE_URL}/delegate-selection", headers=headers)
        r_delegate.raise_for_status()
        resp_json = r_delegate.json()
        print("\n[API RESPONSE]:")
        print(json.dumps(resp_json, indent=4, ensure_ascii=False))
        
        # Check if qr_b64 exists and what's inside (optional, but we want the JSON data)
        data = resp_json["data"]
        print("\n[VERIFICATION]:")
        print(f"   - baseUrl: {data.get('base_url') or data.get('baseUrl')}")
        
    except Exception as e:
        print(f"ERR: Step 3 failed: {e}")
        if 'r_delegate' in locals(): print(r_delegate.text)

if __name__ == "__main__":
    test_qr_flow()
