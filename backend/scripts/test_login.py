import httpx
import json

BASE_URL_AUTH = "http://localhost:8000"
BASE_URL_WMS = "http://localhost:8002"

def print_json(title, data):
    print(f"\n--- {title} ---")
    print(json.dumps(data, indent=2))

async def run_flow():
    async with httpx.AsyncClient() as client:
        # 1. LOGIN
        print("🔐 Iniciando Login...")
        login_data = {
            "username": "admin@interno.com",
            "password": "admin_password" # Ajusta a tus credenciales de demo
        }
        r_login = await client.post(f"{BASE_URL_AUTH}/api/v1/auth/login", json=login_data)
        
        if r_login.status_code != 200:
            print(f"Error en Login: {r_login.text}")
            return

        login_response = r_login.json()
        print_json("RESPONSE: LOGIN", login_response)
        
        token = login_response["access_token"]
        # El login retorna CompanyAccessDto según tus requerimientos
        companies = login_response["companies"] 
        headers = {"Authorization": f"Bearer {token}"}

        if not companies:
            print("El usuario no tiene empresas asignadas.")
            return

        # 2. SELECCIONAR EMPRESA (Simulamos que el usuario elige la primera)
        selected_company_id = companies[0]["id"]
        headers["X-Company-ID"] = selected_company_id
        print(f"\n🏢 Empresa seleccionada: {companies[0]['name']} (ID: {selected_company_id})")

        # 3. CREAR PRODUCTO EN WMS (Prueba de escritura)
        print("\n📦 Creando producto de prueba...")
        product_data = {
            "code": "PROD-001",
            "name": "Producto Interno Core",
            "description": "Prueba de integración ADN common",
            "weight": 1.5
        }
        r_prod = await client.post(f"{BASE_URL_WMS}/api/v1/products/", json=product_data, headers=headers)
        print_json("RESPONSE: PRODUCT CREATE (WMS)", r_prod.json())

        # 4. LISTAR PRODUCTOS (Prueba de lectura)
        print("\n📑 Obteniendo lista de productos...")
        r_list = await client.get(f"{BASE_URL_WMS}/api/v1/products/", headers=headers)
        print_json("RESPONSE: PRODUCT LIST (WMS)", r_list.json())

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_flow())