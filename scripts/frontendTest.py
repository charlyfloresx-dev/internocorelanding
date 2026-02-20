import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def save_mock(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"✅ Archivo generado: {filename}")

def run():
    print("--- Generando Mocks basados en Swagger ---")
    
    # 1. Registro de Usuario
    user_data = {
        "email": "admin@nexo.com",
        "password": "password123",
        "full_name": "Admin Nexo"
    }
    print("Probando: Create User...")
    r_user = requests.post(f"{BASE_URL}/users/", json=user_data)
    if r_user.status_code in [200, 201]:
        save_mock("mock_user_created.json", r_user.json())

    # 2. Registro de Empresa
    company_data = {
        "name": "NexoSuite Demo",
        "industry": "Software"
    }
    print("Probando: Create Company...")
    # Nota: Aquí podrías necesitar pasar el token del usuario si el endpoint es protegido
    r_comp = requests.post(f"{BASE_URL}/companies/", json=company_data)
    if r_comp.status_code in [200, 201]:
        save_mock("mock_company_created.json", r_comp.json())

    # 3. Login (Handshake)
    print("Probando: Login...")
    login_data = {"email": "admin@nexo.com", "password": "password123"}
    r_login = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if r_login.status_code == 200:
        save_mock("mock_login_handshake.json", r_login.json())
        
        # 4. Selección de Empresa (JWT Final)
        handshake_token = r_login.json().get("data", {}).get("handshakeToken")
        # Usamos el ID de la empresa creada o uno genérico para el mock
        tenant_id = r_comp.json().get("data", {}).get("id") if r_comp.status_code < 300 else "uuid-test"
        
        print("Probando: Select Company...")
        select_data = {"handshakeToken": handshake_token, "tenant_id": tenant_id}
        r_sel = requests.post(f"{BASE_URL}/auth/select-company", json=select_data)
        if r_sel.status_code == 200:
            save_mock("mock_auth_final.json", r_sel.json())

if __name__ == "__main__":
    run()