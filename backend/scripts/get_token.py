import requests
import json
import uuid

BASE_URL = "http://localhost:8001/api/v1/auth"
EMAIL = "admin@interno.com"
PASSWORD = "admin123456"
COMPANY_ID = "eb8f7e2c-3f4a-4b5c-8d7e-1f2a3b4c5d6e"

def get_token():
    print(f"[*] Authenticando a {EMAIL}...")
    
    # 1. Login (Handshake)
    login_data = {"email": EMAIL, "password": PASSWORD}
    r_login = requests.post(f"{BASE_URL}/login", json=login_data)
    
    if r_login.status_code != 200:
        print(f"❌ Login fallido ({r_login.status_code}): {r_login.text}")
        return None
    
    data = r_login.json().get("data", {})
    handshake_token = data.get("handshakeToken")
    print(f"✅ Handshake exitoso. Token: {handshake_token[:10]}...")
    
    # 2. Selección de Empresa
    print(f"[*] Seleccionando empresa {COMPANY_ID}...")
    select_data = {"handshakeToken": handshake_token, "tenant_id": COMPANY_ID}
    r_sel = requests.post(f"{BASE_URL}/select-company", json=select_data)
    
    if r_sel.status_code != 200:
        print(f"❌ Selección fallida ({r_sel.status_code}): {r_sel.text}")
        return None
    
    final_token = r_sel.json().get("data", {}).get("access_token")
    print(f"✅ Token FINAL obtenido: {final_token[:20]}...")
    
    with open("verify_token.txt", "w") as f:
        f.write(final_token)
    
    return final_token

if __name__ == "__main__":
    get_token()
