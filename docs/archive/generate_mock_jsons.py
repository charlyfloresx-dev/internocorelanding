import requests
import json
import os

BASE_URL = "http://localhost:8000"

def save_json(name, data):
    with open(f"mock_{name}.json", "w") as f:
        json.dump(data, f, indent=4)
    print(f"✅ Archivo mock_{name}.json generado.")

def test_flows():
    print("🚀 Iniciando pruebas de flujo para Frontend...")

    # FLUJO 1: Registro Dual (Admin + Nueva Empresa)
    register_payload = {
        "user": {
            "full_name": "Carlos Admin",
            "email": "admin@nuevaempresa.com",
            "password": "password123"
        },
        "company": {
            "name": "NexoCorp",
            "country": "México",
            "industry": "Tecnología"
        }
    }
    # Nota: El endpoint debe coincidir con tu router de FastAPI
    r1 = requests.post(f"{BASE_URL}/auth/register-company", json=register_payload)
    if r1.status_code == 201:
        save_json("register_success", r1.json())
    else:
        print(f"🚨 Error en registro: {r1.status_code} - {r1.text}")

    # FLUJO 2: Login con Selección de Múltiples Empresas (Caso B)
    # Simulamos un usuario que ya pertenece a 2 empresas
    login_payload = {"email": "user@multicompany.com", "password": "password123"}
    r2 = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
    if r2.status_code == 200:
        save_json("login_multi_tenant", r2.json())
    else:
        print(f"🚨 Error en login: {r2.status_code} - {r2.text}")


    # FLUJO 3: Selección de Empresa (Generación de JWT Final)
    handshake_token = None
    if r2.status_code == 200:
        handshake_token = r2.json().get("handshakeToken")
        
    if handshake_token:
        # NOTE: 'uuid-empresa-1' should be replaced with an actual UUID from 'login_multi_tenant' response
        # For now, this will likely fail if a valid UUID is not hardcoded or retrieved dynamically
        select_payload = {"tenant_id": "uuid-empresa-1", "token": handshake_token}
        r3 = requests.post(f"{BASE_URL}/auth/select-company", json=select_payload)
        if r3.status_code == 200:
            save_json("jwt_final_session", r3.json())
        else:
            print(f"🚨 Error en selección de empresa: {r3.status_code} - {r3.text}")
    else:
        print("🚨 No se obtuvo handshakeToken, omitiendo selección de empresa.")


if __name__ == "__main__":
    test_flows()
