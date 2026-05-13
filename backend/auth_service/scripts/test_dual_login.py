import requests
import json

import os
BASE_URL = os.getenv("API_URL", "http://localhost:8000/api/v1/auth")

def test_login(payload, label):
    print(f"\n--- Probando: {label} ---")
    try:
        r = requests.post(f"{BASE_URL}/login", json=payload)
        print(f"Status: {r.status_code}")
        data = r.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return r.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def run_tests():
    # 1. Test Email/Password (Charly)
    res1 = test_login(
        {"email": "charly@interno.com", "password": "charly123"},
        "Email/Password Login (Charly)"
    )

    if res1:
        print("\n[OK] PRUEBAS DE LOGIN WEB EXITOSAS.")
    else:
        print("\n[FAIL] ALGUNAS PRUEBAS FALLARON.")

if __name__ == "__main__":
    run_tests()
