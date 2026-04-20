import requests
import json
import uuid
from decimal import Decimal

# URLs de los servicios en Docker
AUTH_URL = "http://localhost:8001/api/v1/auth"
INVENTORY_URL = "http://localhost:8004/api/v1/inventory/transfers/inter-company"

# Parámetros Demo
USER_EMAIL = "charly@interno.com"
USER_PASS = "charly123"

# Compañías Demo (Mapeos según base de datos)
# Logistica: Tijuana / Enterprise: Planta Centro
LOGISTICS_COMPANY_KEY = "Tijuana"
ENTERPRISE_COMPANY_KEY = "Enterprise" 

def get_jwt_for_company(company_keyword: str) -> dict:
    print(f"\n🔐 Solicitando JWT para Empresa destino (keyword: {company_keyword})...")
    # 1. Base Login
    r_login = requests.post(f"{AUTH_URL}/login", json={"email": USER_EMAIL, "password": USER_PASS})
    r_login.raise_for_status()
    data = r_login.json()["data"]
    
    sel_token = data["selection_token"]
    
    # 2. Encontrar compañía
    target = next((c for c in data["companies"] if company_keyword.lower() in c["company_name"].lower()), None)
    if not target:
        print(f"❌ No se encontró empresa con la palabra clave '{company_keyword}'")
        return None
        
    print(f"✅ Empresa emparejada: {target['company_name']} ({target['company_id']})")
    
    # 3. Select Company
    headers = {
        "Authorization": f"Bearer {sel_token}",
        "X-Selection-Token": sel_token
    }
    r_select = requests.post(f"{AUTH_URL}/select-company", json={"company_id": target["company_id"]}, headers=headers)
    r_select.raise_for_status()
    access_token = r_select.json()["data"]["access_token"]
    
    return {
        "company_id": target["company_id"],
        "token": access_token
    }

def run_e2e_flow():
    print("==================================================")
    print("🚀 TEST E2E: INTER-COMPANY TRANSFER (VÍA HTTP API)")
    print("==================================================")
    
    # --- 1. OBTENER TOKENS ---
    auth_a = get_jwt_for_company(LOGISTICS_COMPANY_KEY)
    auth_b = get_jwt_for_company(ENTERPRISE_COMPANY_KEY)
    
    if not auth_a or not auth_b:
        print("❌ Falló la autenticación inicial.")
        return
        
    print("\n[A] EMPRESA A (Emisor):", auth_a['company_id'])
    print("[B] EMPRESA B (Receptor):", auth_b['company_id'])

    # --- 2. EMPRESA A DESPACHA (Initiate) ---
    print("\n--- PASO 1: EMPRESA A DESPACHA (InitiateTransfer) ---")
    headers_a = {"Authorization": f"Bearer {auth_a['token']}", "Content-Type": "application/json"}
    
    # Nota: Estos UUIDs son los predefinidos en nuestro seed
    wh_main_a = str(uuid.uuid5(uuid.NAMESPACE_DNS, "interno.warehouse.WH-MAIN"))
    wh_main_b = str(uuid.uuid5(uuid.NAMESPACE_DNS, "interno.warehouse.ENTERPRISE-MAIN"))
    product_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, "interno.item.MAT-001"))
    uom_pz = str(uuid.uuid5(uuid.NAMESPACE_DNS, "interno.uom.PZA"))

    initiate_payload = {
        "destination_company_id": auth_b["company_id"],
        "destination_warehouse_id": wh_main_b,
        "origin_warehouse_id": wh_main_a,
        "product_id": product_id,
        "uom_id": uom_pz,
        "quantity": 10.0,
        "weight": 2.0,
        "origin_sku": "MAT-001",
        "destination_sku": "ENT-MAT-001",
        "destination_product_id": product_id,
        "transfer_price": 125.50, # Contrato Financiero Pactado
        "notes": "E2E Test vía Axios/Http",
        "external_reference": "E2E-HTTP-001"
    }
    
    try:
        r_init = requests.post(f"{INVENTORY_URL}/initiate", json=initiate_payload, headers=headers_a)
        r_init.raise_for_status()
        transfer_data = r_init.json()["data"]
        transfer_id = transfer_data["id"]
        
        print(f"✅ Documento Iniciado: {transfer_data['folio']} | ID: {transfer_id}")
        print(f"   Status: {transfer_data['status']}")
        print(f"   Sealed Transfer Price: ${transfer_data['unit_price_at_dispatch']}")
        print(f"   Revenue (Empresa A): ${transfer_data['transfer_revenue_a']}")
    except Exception as e:
        print(f"❌ Error al iniciar la transferencia ({r_init.status_code}): {r_init.text}")
        return

    # --- 3. EMPRESA B RECIBE (Complete) ---
    print("\n--- PASO 2: EMPRESA B RECIBE (CompleteTransfer) ---")
    headers_b = {"Authorization": f"Bearer {auth_b['token']}", "Content-Type": "application/json"}
    
    receive_payload = {
        "received_quantity": 10.0,
        "notes": "Recibido íntegro E2E Test"
    }

    try:
        r_recv = requests.post(f"{INVENTORY_URL}/{transfer_id}/receive", json=receive_payload, headers=headers_b)
        r_recv.raise_for_status()
        recv_data = r_recv.json()["data"]
        
        print(f"✅ Documento Recibido: {recv_data['folio']}")
        print(f"   Status: {recv_data['status']}")
        print(f"   Adquisición (Costo Empresa B): ${recv_data['acquisition_cost_b']}")
        
        expected_cost = Decimal("10.0") * Decimal("125.50")
        if Decimal(str(recv_data['acquisition_cost_b'])) == expected_cost:
            print(f"   [AUDIT] Integridad Matemática del Costo B comprobada (10 x 125.50 = {expected_cost}) 🟢")
        else:
            print(f"   [AUDIT] Falla de cálculo: {recv_data['acquisition_cost_b']} 🔴")
            
    except Exception as e:
        print(f"❌ Error al recibir la transferencia ({r_recv.status_code}): {r_recv.text}")
        return
        
    print("\n🔥 E2E COMPLETADO CON ÉXITO 🔥")

if __name__ == "__main__":
    run_e2e_flow()
