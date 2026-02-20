import requests
import json
import uuid
import sys
import time

def print_step(name):
    print(f"\n--- STEP: {name} ---", flush=True)

def print_result(passed, message=""):
    status = "✅ PASSED" if passed else "❌ FAILED"
    print(f"[{status}] {message}", flush=True)
    if not passed:
        sys.exit(1)

def validate_e2e_wms():
    print("🚀 INICIANDO VALIDACIÓN INTEGRAL WMS (FLORENCE E2E) 🚀", flush=True)
    
    # Internal Docker URLs
    AUTH_URL = "http://auth-service-api:8000/api/v1/auth"
    WMS_URL = "http://wms-service-api:8000/api/v1/inventory"
    
    # 1. HANDSHAKE DE IDENTIDAD
    print_step("Handshake de Identidad")
    
    login_payload = {"email": "test@ejemplo.com", "password": "admin123"}
    resp = requests.post(f"{AUTH_URL}/login", json=login_payload)
    print_result(resp.status_code == 200, "Login inicial exitoso")
    
    auth_data = resp.json()["data"]
    selection_token = auth_data["selection_token"]
    company = auth_data["companies"][0]
    company_id = company["company_id"]
    
    # Select Company
    resp = requests.post(
        f"{AUTH_URL}/select-company",
        json={"company_id": company_id},
        headers={"X-Selection-Token": selection_token}
    )
    print_result(resp.status_code == 200, "Selección de empresa y obtención de JWT")
    
    access_token = resp.json()["data"]["access_token"]
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Company-ID": company_id
    }

    # 2. MASTER DATA (Warehouse Creation)
    print_step("Configuración de Datos Maestros")
    wh_payload = {
        "code": f"WH-{uuid.uuid4().hex[:4]}",
        "name": "Almacén Principal E2E",
        "active": True
    }
    resp = requests.post(f"{WMS_URL}/warehouses", json=wh_payload, headers=headers)
    print_result(resp.status_code == 201, f"Warehouse {wh_payload['code']} creado via API")
    warehouse_id = resp.json()["data"]["id"]
    product_id = "PRODUCT-CPP-TEST-001"

    # 3. OPERACIÓN DE INVENTARIO (FLUJO CPP)
    print_step("Operación de Inventario (Flujo CPP)")
    
    # Transacción 1: 100u @ $10.00
    print("Enviando Transacción 1: 100u @ $10.00...", flush=True)
    doc_1 = {
        "folio": f"IN-{uuid.uuid4().hex[:6]}",
        "concept_id": "concept-in-01",
        "warehouse_id": warehouse_id,
        "movements": [
            {
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "quantity": 100.0,
                "unit_cost": 10.0
            }
        ]
    }
    resp = requests.post(f"{WMS_URL}/documents", json=doc_1, headers=headers)
    doc_id_1 = resp.json()["data"]["id"]
    requests.post(f"{WMS_URL}/documents/{doc_id_1}/confirm", headers=headers)
    print("Transacción 1 Confirmada.", flush=True)

    # Transacción 2: 50u @ $25.00
    print("Enviando Transacción 2: 50u @ $25.00...", flush=True)
    doc_2 = {
        "folio": f"IN-{uuid.uuid4().hex[:6]}",
        "concept_id": "concept-in-01",
        "warehouse_id": warehouse_id,
        "movements": [
            {
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "quantity": 50.0,
                "unit_cost": 25.0
            }
        ]
    }
    resp = requests.post(f"{WMS_URL}/documents", json=doc_2, headers=headers)
    doc_id_2 = resp.json()["data"]["id"]
    requests.post(f"{WMS_URL}/documents/{doc_id_2}/confirm", headers=headers)
    print("Transacción 2 Confirmada.", flush=True)

    # Verificación de Stock y CPP
    print_step("Cálculo de Resultados (Ledger Reactivo)")
    resp = requests.get(f"{WMS_URL}/stock/{product_id}", headers=headers)
    stock_data = resp.json()["data"][0]
    
    stock_real = float(stock_data["stock_on_hand"])
    cpp_real = float(stock_data["average_cost"])
    
    print(f"RESULTADO: Stock={stock_real}, CPP={cpp_real}", flush=True)
    
    stock_ok = stock_real == 150.0
    # CPP esperado: (100*10 + 50*25) / 150 = 2250 / 150 = 15.0
    cpp_ok = abs(cpp_real - 15.0) < 0.001
    
    print_result(stock_ok and cpp_ok, "Cálculo de Stock y CPP Recalculado correctamente")

    # 4. PRUEBA DE 'BÚNKER' (SEGURIDAD)
    print_step("Prueba de 'Búnker' (Seguridad Multi-Tenancy)")
    
    wrong_headers = headers.copy()
    wrong_headers["X-Company-ID"] = str(uuid.uuid4())
    
    print(f"Intentando acceso con X-Company-ID falso: {wrong_headers['X-Company-ID']}", flush=True)
    resp = requests.get(f"{WMS_URL}/stock/{product_id}", headers=wrong_headers)
    
    print_result(resp.status_code == 403, "Acceso bloqueado satisfactoriamente (403 Forbidden)")

    print("\n" + "="*40, flush=True)
    print("🌟 REPORT: ALL GREEN 🌟", flush=True)
    print("InternoCore WMS está listo para Producción.", flush=True)
    print("="*40, flush=True)

if __name__ == "__main__":
    validate_e2e_wms()
