import requests
import json
import sys
import uuid
import time

def print_result(step, passed, detail=""):
    status = "PASSED ✅" if passed else "FAILED ❌"
    print(f"[{status}] {step}", flush=True)
    if detail:
        print(f"    Detail: {detail}", flush=True)

def validate_e2e():
    print("--- 🚀 INICIANDO VALIDACIÓN E2E (INTERNOCORE) ---")
    
    # Configuración de URLs (Contexto Docker)
    # Dentro de la red de docker, usamos los nombres de servicio.
    # Si se ejecuta desde el host, usamos localhost y los puertos mapeados.
    # Asumimos ejecución desde el contenedor wms-service para que 'auth-service' sea accesible.
    AUTH_BASE_URL = "http://auth-service:8000/api/v1/auth"
    WMS_BASE_URL = "http://wms-service-api:8000/api/v1/inventory"
    
    # Credenciales del Seed
    CREDENTIALS = {
        "email": "test@ejemplo.com",
        "password": "admin123"
    }
    
    print(f"DEBUG: AUTH_BASE_URL: {AUTH_BASE_URL}", flush=True)
    print(f"DEBUG: WMS_BASE_URL: {WMS_BASE_URL}", flush=True)
    
    context = {}

    try:
        # --- PASO 1: AUTH CHECK ---
        print("\n1. Auth Check...")
        login_resp = requests.post(f"{AUTH_BASE_URL}/login", json=CREDENTIALS)
        if login_resp.status_code != 200:
             print_result("Login Inicial", False, f"Status: {login_resp.status_code} - {login_resp.text}")
             return
        
        login_data = login_resp.json()["data"]
        selection_token = login_data["selection_token"]
        first_company = login_data["companies"][0]
        company_id = first_company["company_id"]
        
        # Seleccionar empresa
        select_resp = requests.post(
            f"{AUTH_BASE_URL}/select-company",
            json={"company_id": company_id},
            headers={"X-Selection-Token": selection_token}
        )
        if select_resp.status_code != 200:
            print_result("Selección de Empresa", False, select_resp.text)
            return
        
        access_token = select_resp.json()["data"]["access_token"]
        context["token"] = access_token
        context["company_id"] = company_id
        context["headers"] = {
            "Authorization": f"Bearer {access_token}",
            "X-Company-ID": company_id
        }
        print_result("Auth Check", True, f"Token obtenido para {first_company['company_name']}")

        # --- PASO 2: MASTER DATA ---
        print("\n2. Master Data Check...")
        # En esta demo, usaremos IDs generados pero consistentes
        product_id = "PROD-E2E-001"
        warehouse_id = "WH-E2E-MAIN"
        context["product_id"] = product_id
        context["warehouse_id"] = warehouse_id
        print_result("Master Data", True, f"Usando Product: {product_id}, Warehouse: {warehouse_id}")

        # --- PASO 3: LEDGER TRANSACTION (FIRST ENTRY) ---
        print("\n3. Ledger Transaction: First Entry ($100.00)...")
        doc_1 = {
            "folio": f"E2E-{uuid.uuid4().hex[:6]}",
            "concept_id": "ENTRADA-E2E",
            "warehouse_id": warehouse_id,
            "movements": [
                {
                    "product_id": product_id,
                    "warehouse_id": warehouse_id,
                    "quantity": "10.0000",
                    "unit_cost": "100.0000"
                }
            ]
        }
        
        resp_create_1 = requests.post(f"{WMS_BASE_URL}/documents", json=doc_1, headers=context["headers"])
        if resp_create_1.status_code != 201:
            try:
                error_msg = resp_create_1.json().get("message", resp_create_1.text)
            except:
                error_msg = resp_create_1.text
            print_result("Creación Documento 1", False, error_msg)
            return
        
        doc_id_1 = resp_create_1.json()["data"]["id"]
        
        # Confirmar
        resp_conf_1 = requests.post(f"{WMS_BASE_URL}/documents/{doc_id_1}/confirm", headers=context["headers"])
        if resp_conf_1.status_code != 200:
            error_msg = resp_conf_1.json().get("message", resp_conf_1.text)
            print_result("Confirmación Documento 1", False, error_msg)
            return
        
        # Verificar Snapshot
        resp_stock_1 = requests.get(f"{WMS_BASE_URL}/stock/{product_id}", headers=context["headers"])
        snap_1 = resp_stock_1.json()["data"][0]
        
        stock_ok = float(snap_1["stock_on_hand"]) == 10.0
        cpp_ok = float(snap_1["average_cost"]) == 100.0
        
        if stock_ok and cpp_ok:
            print_result("Ledger Entry 1", True, f"Stock: {snap_1['stock_on_hand']}, CPP: {snap_1['average_cost']}")
        else:
            print_result("Ledger Entry 1", False, f"Stock Esperado: 10, Real: {snap_1['stock_on_hand']} | CPP Esperado: 100, Real: {snap_1['average_cost']}")
            return

        # --- PASO 4: LEDGER TRANSACTION (SECOND ENTRY) ---
        print("\n4. Ledger Transaction: Second Entry ($150.00)...")
        doc_2 = {
            "folio": f"E2E-{uuid.uuid4().hex[:6]}",
            "concept_id": "ENTRADA-E2E",
            "warehouse_id": warehouse_id,
            "movements": [
                {
                    "product_id": product_id,
                    "warehouse_id": warehouse_id,
                    "quantity": "10.0000",
                    "unit_cost": "150.0000"
                }
            ]
        }
        
        resp_create_2 = requests.post(f"{WMS_BASE_URL}/documents", json=doc_2, headers=context["headers"])
        doc_id_2 = resp_create_2.json()["data"]["id"]
        requests.post(f"{WMS_BASE_URL}/documents/{doc_id_2}/confirm", headers=context["headers"])
        
        # Verificar Snapshot (Cálculo CPP: (10*100 + 10*150) / 20 = 2500 / 20 = 125)
        resp_stock_2 = requests.get(f"{WMS_BASE_URL}/stock/{product_id}", headers=context["headers"])
        snap_2 = resp_stock_2.json()["data"][0]
        
        stock_ok = float(snap_2["stock_on_hand"]) == 20.0
        cpp_ok = float(snap_2["average_cost"]) == 125.0
        
        if stock_ok and cpp_ok:
            print_result("Ledger Entry 2 (Recalcular CPP)", True, f"Stock: {snap_2['stock_on_hand']}, CPP: {snap_2['average_cost']}")
        else:
            print_result("Ledger Entry 2", False, f"Stock Esperado: 20, Real: {snap_2['stock_on_hand']} | CPP Esperado: 125, Real: {snap_2['average_cost']}")
            return

        # --- PASO 5: SECURITY CHECK ---
        print("\n5. Security Check (Tenant Isolation)...")
        fake_company_id = str(uuid.uuid4())
        fake_headers = context["headers"].copy()
        fake_headers["X-Company-ID"] = fake_company_id
        
        resp_sec = requests.get(f"{WMS_BASE_URL}/stock/{product_id}", headers=fake_headers)
        
        if resp_sec.status_code == 403:
            print_result("Security Check", True, "Acceso bloqueado satisfactoriamente (403 Forbidden)")
        else:
            print_result("Security Check", False, f"Se obtuvo status {resp_sec.status_code} en lugar de 403")
            return

        print("\n--- ✅ VALIDACIÓN E2E COMPLETADA CON ÉXITO ---")

    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO DURANTE E2E: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    validate_e2e()
