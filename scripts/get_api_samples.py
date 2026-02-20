import requests
import json
import sys

AUTH_URL = "http://127.0.0.1:8001/api/v1/auth"
WMS_URL = "http://127.0.0.1:8002/api/v1"

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"   ✅ Archivo guardado: {filename}")

def run_integration():
    print("\n🚀 INTERNO CORE - PRUEBA DE INTEGRACIÓN")
    print("="*60)

    # 1. LOGIN
    print("🔐 Paso 1: Autenticando...")
    try:
        r_login = requests.post(f"{AUTH_URL}/login", json={"email": "admin@interno.com", "password": "admin123456"})
        r_login.raise_for_status()
        login_data = r_login.json().get("data", {})
    except Exception as e:
        print(f"❌ Error Login: {e}")
        return

    t1_token = login_data.get("access_token")
    companies = login_data.get("companies", [])

    # 2. SELECCIÓN DE EMPRESA
    c_id = companies[0].get("company_id") or companies[0].get("id")
    print(f"🏢 Paso 2: Seleccionando empresa {c_id}...")

    select_headers = {
        "Authorization": f"Bearer {t1_token}",
        "X-Selection-Token": t1_token,
        "Content-Type": "application/json"
    }
    
    r_select = requests.post(f"{AUTH_URL}/select-company", json={"company_id": str(c_id)}, headers=select_headers)
    
    if r_select.status_code != 200:
        print(f"❌ Error en Selección: {r_select.text}")
        return

    print("✅ Selección exitosa.")
    save_json("sample_selection_response.json", r_select.json())

if __name__ == "__main__":
    run_integration()