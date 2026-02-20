import requests
import json
import os

# URLs de los Microservicios
AUTH_BASE = "http://localhost:8000/api/v1/auth"
WMS_BASE = "http://localhost:8002/api/v1"

# Credenciales Demo
EMAIL = "admin@interno.com"
PASSWORD = "admin123456"

# ID de producto usado en el seed del WMS para probar el endpoint de stock
DEMO_PRODUCT_ID = "550e8400-e29b-41d4-a716-446655440002"

def fetch_all_data():
    # Inicializamos la estructura para evitar errores si algo falla
    consolidated_data = {
        "auth": {}, 
        "wms": {
            "warehouses": [], 
            "inventory": []
        }
    }

    try:
        # --- PASO 1: LOGIN ---
        print("🔐 Paso 1: Autenticando en Interno Core...")
        login_payload = {"email": EMAIL, "password": PASSWORD}
        login_res = requests.post(f"{AUTH_BASE}/login", json=login_payload)
        
        if login_res.status_code != 200:
            print(f"❌ Error en Login: {login_res.text}")
            return

        response_json = login_res.json()
        data_block = response_json.get("data", {})
        selection_token = data_block.get("selection_token")
        companies = data_block.get("companies", [])

        if not companies:
            print("⚠️ No se encontraron empresas vinculadas a este usuario.")
            return

        # Obtenemos la primera empresa disponible
        first_company = companies[0]
        target_company_id = first_company.get("company_id")
        
        print(f"✅ Login exitoso. Empresa: {target_company_id}")

        # --- PASO 2: SELECCIÓN DE EMPRESA ---
        print(f"🏢 Paso 2: Obteniendo token de acceso final...")
        select_payload = {"company_id": str(target_company_id)}
        select_headers = {"X-Selection-Token": selection_token}
        
        select_res = requests.post(
            f"{AUTH_BASE}/select-company",
            json=select_payload,
            headers=select_headers
        )
        select_res.raise_for_status()
        
        auth_final_data = select_res.json().get("data", {})
        final_token = auth_final_data.get("access_token")
        consolidated_data["auth"] = auth_final_data

        if not final_token:
            print("❌ Error: No se recibió el access_token final.")
            return

        # --- PASO 3: CONSULTA WMS ---
        # Limpieza estricta del token para evitar el 401
        clean_token = final_token.strip()
        wms_headers = {
            "Authorization": f"Bearer {clean_token}",
            "X-Company-ID": str(target_company_id),
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        print(f"🚀 Consultando WMS con token: {clean_token[:15]}...")

        # Consultar Almacenes
        print("📦 Consultando Almacenes (/warehouses)...")
        wh_res = requests.get(f"{WMS_BASE}/warehouses", headers=wms_headers)
        
        if wh_res.status_code == 200:
            consolidated_data["wms"]["warehouses"] = wh_res.json().get("data", [])
            print(f"✅ Almacenes obtenidos: {len(consolidated_data['wms']['warehouses'])}")
        else:
            print(f"⚠️ Error {wh_res.status_code} en Almacenes: {wh_res.text}")

        # Consultar Stock
        print(f"📊 Consultando Stock del producto demo...")
        stock_url = f"{WMS_BASE}/stock/{DEMO_PRODUCT_ID}"
        stock_res = requests.get(stock_url, headers=wms_headers)
        
        if stock_res.status_code == 200:
            consolidated_data["wms"]["inventory"] = stock_res.json().get("data", [])
            print("✅ Datos de stock obtenidos.")
        else:
            print(f"⚠️ Error {stock_res.status_code} en Stock: {stock_res.text}")

        # --- GUARDAR RESULTADOS ---
        with open("api_context_dump.json", "w", encoding="utf-8") as f:
            json.dump(consolidated_data, f, indent=4, ensure_ascii=False)
        
        print(f"\n✨ Proceso completado exitosamente.")
        print(f"📂 Archivo generado: {os.path.abspath('api_context_dump.json')}")

    except Exception as e:
        print(f"💥 Error inesperado: {str(e)}")

if __name__ == "__main__":
    fetch_all_data()