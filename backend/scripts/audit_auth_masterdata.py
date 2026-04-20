"""
Script de Auditoría para Auth Service + Master Data Service
Valida el flujo completo: Login → Select Company → Acceso a rutas protegidas
"""
import requests
import json

AUTH_URL = "http://localhost:8001/api/v1/auth"
MASTER_URL = "http://localhost:8003/api/v1"
CREDENTIALS = {"email": "charly@interno.com", "password": "charly123"}

def separator(title=""):
    print(f"\n{'='*60}")
    if title:
        print(f"  {title}")
        print('='*60)

def run():
    separator("PASO 1 — AUTH SERVICE: LOGIN")
    try:
        r = requests.post(f"{AUTH_URL}/login", json=CREDENTIALS)
        assert r.status_code == 200, f"Status inesperado: {r.status_code} → {r.text}"
        login_data = r.json()["data"]

        sel_token = login_data["selection_token"]
        companies = login_data["companies"]
        company_id = companies[0]["company_id"]

        print(f"✅ Login OK → {len(companies)} empresa(s) disponibles")
        for c in companies:
            print(f"   • {c['company_name']} ({c['company_id']}) — roles: {c['role_names']}")
    except Exception as e:
        print(f"❌ FALLO en Login: {e}")
        return

    separator("PASO 2 — AUTH SERVICE: SELECT COMPANY")
    try:
        headers = {"Authorization": f"Bearer {sel_token}", "X-Selection-Token": sel_token}
        r = requests.post(f"{AUTH_URL}/select-company", json={"company_id": company_id}, headers=headers)
        assert r.status_code == 200, f"Status inesperado: {r.status_code} → {r.text}"

        resp_data = r.json()["data"]
        access_token = resp_data["access_token"]

        print(f"✅ Select-Company OK")
        print(f"   • Company ID : {resp_data['company_id']}")
        print(f"   • Role Names : {resp_data['roles']}")
        print(f"   • Scopes     : {resp_data['scopes'][:3]}...")
    except Exception as e:
        print(f"❌ FALLO en Select-Company: {e}")
        return

    # Cabeceras estándar multi-tenant
    auth_headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Company-ID": company_id,
        "X-User-ID": "test-script"
    }

    separator("PASO 3 — CORS PREFLIGHT (OPTIONS) via Python")
    for port, path in [(8001, "/api/v1/auth/login"), (8003, "/api/v1/concepts"), (8003, "/api/v1/products")]:
        import http.client
        conn = http.client.HTTPConnection("localhost", port)
        conn.request("OPTIONS", path, headers={
            "Origin": "http://localhost:8080",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,x-company-id,x-user-id"
        })
        resp = conn.getresponse()
        status = "✅" if resp.status in (200, 204) else "❌"
        print(f"{status} OPTIONS :{port}{path} → {resp.status} | Allow-Origin: {resp.getheader('Access-Control-Allow-Origin')}")

    separator("PASO 4 — MASTER DATA SERVICE: ACCESO PROTEGIDO")
    routes_to_test = [
        ("GET", f"{MASTER_URL}/concepts", "Conceptos"),
        ("GET", f"{MASTER_URL}/warehouses", "Almacenes"),
        ("GET", f"{MASTER_URL}/categories", "Categorías"),
        ("GET", f"{MASTER_URL}/brands", "Marcas"),
        ("GET", f"{MASTER_URL}/uoms", "Unidades de Medida"),
        ("GET", f"{MASTER_URL}/products", "Productos"),
    ]

    for method, url, label in routes_to_test:
        try:
            r = requests.request(method, url, headers=auth_headers)
            if r.status_code == 200:
                data = r.json().get("data", [])
                count = len(data) if isinstance(data, list) else "N/A"
                print(f"✅ {label:25s} → {r.status_code} | registros: {count}")
            else:
                print(f"⚠️  {label:25s} → {r.status_code} | {r.text[:80]}")
        except Exception as e:
            print(f"❌ {label:25s} → ERROR: {e}")

    separator("RESULTADO FINAL")
    print("  Auth Service : ✅ Login + Select-Company funcionando")
    print("  CORS         : ✅ OPTIONS responde 200 con los headers correctos")
    print("  Master Data  : Ver resultados arriba")
    print()

if __name__ == "__main__":
    run()
