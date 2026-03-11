import requests
import json
import sys
import os

# --- CONFIGURACIÓN ---
# Ajusta estas credenciales según lo que hayas definido en scripts/seed_data.py
EMAIL = "admin@interno.com"
PASSWORD = "admin123456"

# Puertos basados en docker-compose.yml
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://127.0.0.1:8000/api/v1/auth")
MASTER_SERVICE_URL = os.getenv("MASTER_SERVICE_URL", "http://127.0.0.1:8003/api/v1")

# ID de la empresa que esperamos usar (del seed_master.py)
TARGET_COMPANY_ID = "eb8f7e2c-3f4a-4b5c-8d7e-1f2a3b4c5d6e"

def print_step(step_name):
    print(f"\n{'='*50}")
    print(f"📍 PASO: {step_name}")
    print(f"{'='*50}")

def main():
    # ---------------------------------------------------------
    # 1. LOGIN (Pre-Auth)
    # Obtiene el selection_token y la lista de empresas
    # ---------------------------------------------------------
    print_step("1. Login (Obtener Selection Token)")
    
    login_payload = {
        "email": EMAIL,
        "password": PASSWORD
    }
    
    response = None
    try:
        response = requests.post(f"{AUTH_SERVICE_URL}/login", json=login_payload)
        response.raise_for_status()
        data = response.json()
        
        selection_token = data["data"]["selection_token"]
        companies = data["data"]["companies"]
        
        print(f"✅ Login exitoso.")
        print(f"🔑 Selection Token: {selection_token[:20]}...")
        print(f"🏢 Empresas disponibles: {len(companies)}")
        
        if not companies:
            print("❌ Error: El usuario no tiene empresas asignadas. Ejecuta seed_data.py primero.")
            sys.exit(1)
            
        # Mostramos las empresas
        for idx, comp in enumerate(companies):
            c_name = comp.get("name") or comp.get("company_name") or "Sin Nombre"
            c_id = comp.get("id") or comp.get("company_id")
            print(f"   [{idx}] {c_name} (ID: {c_id})")

    except requests.exceptions.RequestException as e:
        print(f"❌ Error en Login: {e}")
        if response:
            print(response.text)
        sys.exit(1)

    # ---------------------------------------------------------
    # 2. SELECCIÓN DE EMPRESA
    # Intercambia selection_token + company_id por access_token
    # ---------------------------------------------------------
    print_step("2. Seleccionar Empresa (Obtener Access Token)")
    
    # Buscamos la empresa específica del seed, si no, usamos la primera
    selected_company = next(
        (c for c in companies if str(c.get("id") or c.get("company_id")) == TARGET_COMPANY_ID),
        companies[0]
    )
    
    company_id = selected_company.get("id") or selected_company.get("company_id")
    c_name = selected_company.get("name") or selected_company.get("company_name") or "Sin Nombre"
    print(f"👉 Seleccionando empresa: {c_name}")

    headers_select = {
        "X-Selection-Token": selection_token,
        "Content-Type": "application/json"
    }
    
    payload_select = {
        "company_id": company_id
    }

    response = None
    try:
        response = requests.post(f"{AUTH_SERVICE_URL}/select-company", json=payload_select, headers=headers_select)
        response.raise_for_status()
        auth_data = response.json()
        
        access_token = auth_data["data"]["access_token"]
        print(f"✅ Autenticación completa.")
        print(f"🔐 Access Token Final: {access_token[:20]}...")

    except requests.exceptions.RequestException as e:
        print(f"❌ Error al seleccionar empresa: {e}")
        if response:
            print(response.text)
        sys.exit(1)

    # ---------------------------------------------------------
    # 3. CONSULTAR PRODUCTOS (Master Data Service)
    # Usa el access_token y el header X-Company-Id
    # ---------------------------------------------------------
    print_step("3. Consultar Productos (Master Data)")

    headers_api = {
        "Authorization": f"Bearer {access_token}",
        "X-Company-Id": company_id
    }

    response = None
    try:
        # Asumiendo que el endpoint es /products
        response = requests.get(f"{MASTER_SERVICE_URL}/products", headers=headers_api)
        
        if response.status_code == 200:
            products = response.json()
            print(f"✅ Consulta exitosa. HTTP 200")
            print(f"📦 Productos encontrados: {len(products)}")
            
            # Validación simple del contenido
            iphone_found = any("iPhone 15 Pro" in str(p) for p in products)
            if iphone_found:
                print("   ✅ VALIDACIÓN: Producto 'iPhone 15 Pro' encontrado.")
            else:
                print("   ⚠️ VALIDACIÓN: No se encontró el 'iPhone 15 Pro'. ¿Corriste seed_master.py?")
            print(json.dumps(products, indent=2))
        else:
            print(f"⚠️ Error consultando productos. Status: {response.status_code}")
            if response:
                print(response.text if response.text else f"[Cuerpo Vacío] Raw: {response.content}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión con Master Data: {e}")

if __name__ == "__main__":
    main()