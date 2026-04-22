import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000/api/v1"
EMAIL = "charly@interno.com"
PASSWORD = "charly123"

async def test_catalogs():
    print("==================================================")
    print("PROBANDO ENDPOINTS DE CATALOGOS (MASTER DATA)")
    print("==================================================")

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # 1. Login
        print("\n[1] Autenticando...")
        resp = await client.post("/auth/login", json={"email": EMAIL, "password": PASSWORD})
        if resp.status_code != 200:
            print(f"Error Login: {resp.text}")
            return
        
        login_data = resp.json()["data"]
        selection_token = login_data["selection_token"]
        
        # 2. Seleccionar empresa 'Interno Enterprise'
        enterprise = next((c for c in login_data["companies"] if "Enterprise" in c["company_name"]), None)
        if not enterprise:
            print("Error: No se encontro Interno Enterprise")
            return
            
        print(f"[2] Seleccionando empresa: {enterprise['company_name']}")
        headers = {"X-Selection-Token": selection_token}
        resp = await client.post("/auth/select-company", json={"company_id": enterprise["company_id"]}, headers=headers)
        if resp.status_code != 200:
            print(f"Error Select Company: {resp.text}")
            return
            
        access_token = resp.json()["data"]["access_token"]
        
        # Preparar headers para llamadas al catalogo
        auth_headers = {"Authorization": f"Bearer {access_token}"}
        
        # 3. Probar Endpoints de Catalogo
        endpoints_to_test = [
            ("Productos", "/products/"),
            ("Almacenes", "/warehouses/"),
            ("Unidades de Medida (UOM)", "/uoms/"),
            ("Conceptos de Movimiento", "/concepts/"),
            ("Ubicaciones", "/locations/")
        ]
        
        for name, url in endpoints_to_test:
            print(f"\n[{name}] GET {url}")
            res = await client.get(url, headers=auth_headers)
            if res.status_code == 200:
                data = res.json().get("data", [])
                if isinstance(data, dict) and "items" in data:
                    data = data["items"]
                print(f"   OK - Se encontraron {len(data)} registros.")
                if data:
                    # Mostrar el primero como muestra
                    sample = data[0]
                    # Print un par de campos relevantes si existen
                    display = {}
                    for k in ["name", "code", "sku", "id", "folio"]:
                        if k in sample: display[k] = sample[k]
                    print(f"   Muestra: {display}")
            else:
                print(f"   ERROR {res.status_code}: {res.text}")

if __name__ == "__main__":
    asyncio.run(test_catalogs())
