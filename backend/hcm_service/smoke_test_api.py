from jose import jwt
import uuid
import requests
from datetime import datetime, timedelta

# Config from docker-compose.yml / app code
SECRET_KEY = "DEV_SECRET_KEY_CAMBIAME_EN_PROD_12345"
ALGORITHM = "HS256"

def generate_dev_token():
    payload = {
        "sub": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "company_id": "ad6cc8a6-34f9-42df-8f29-28254e0ad242", # Logistics MX
        "role": "ADMIN",
        "modules": ["auth_core", "inventory_core"],
        "readonly": False,
        "status": "ACTIVE",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def run_smoke_test_api():
    token = generate_dev_token()
    headers = {"Authorization": f"Bearer {token}"}
    base_url = "http://localhost:8009/api/v1/staff"

    print("\n--- SMOKE TEST: ELEGIBLE COLLABORATOR (SMOKE-01) ---")
    r1 = requests.get(f"{base_url}/validate-scan/SMOKE-01?type=CROSS_BORDER", headers=headers)
    print(f"Status: {r1.status_code}")
    print(f"Response: {r1.json()}")

    print("\n--- SMOKE TEST: INELEGIBLE COLLABORATOR (SMOKE-02) ---")
    r2 = requests.get(f"{base_url}/validate-scan/SMOKE-02?type=CROSS_BORDER", headers=headers)
    print(f"Status: {r2.status_code}")
    print(f"Response: {r2.json()}")

if __name__ == "__main__":
    run_smoke_test_api()
