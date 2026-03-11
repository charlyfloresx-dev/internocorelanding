import requests
import json

BASE_URL = "http://localhost:8001/api/v1/auth"

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

    # 2. Test RFID Token (Operator)
    res2 = test_login(
        {"identity_token": "RFID123456"},
        "RFID Login (Operator)"
    )

    # 3. Test Invalid Token
    res3 = test_login(
        {"identity_token": "INVALID_TOKEN"},
        "Invalid RFID Token"
    )

    # 4. Test Missing Credentials
    res4 = test_login(
        {},
        "Missing Credentials"
    )

    if res1 and res2:
        print("\n✅ PRUEBAS DE LOGIN DUAL EXITOSAS.")
    else:
        print("\n❌ ALGUNAS PRUEBAS FALLARON.")

if __name__ == "__main__":
    run_tests()
