# -*- coding: utf-8 -*-
"""
test_density_guard_aws.py -- Cloud Smoke Test: Laissez-Faire Density Guard (AWS App Runner)
================================================================================
Protocolo:
  A) Se asume que el backend en AWS ya tiene la base de datos sincronizada (sync_seeds.py).
  B) Obtiene endpoints via HTTP GET.
  C) Envia 500 unidades a BIN-STRESS-01 -> espera 200/202 (Laissez-Faire)
"""
import sys
import io
import asyncio
import uuid
import requests
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# --- AWS Configuration ---
BACKEND_URL  = "https://jtq5mfp8pj.us-east-2.awsapprunner.com"
AUTH_URL     = f"{BACKEND_URL}/api/v1/auth"
INV_URL      = f"{BACKEND_URL}/api/v1"

USER_EMAIL = "charly@interno.com"
USER_PW    = "charly123"
COMPANY_ID = "ad6cc8a6-34f9-42df-8f29-28254e0ad242"
LOCATION   = "BIN-STRESS-01"


def get_auth_token():
    print(f"[*] Autenticando {USER_EMAIL} en AWS...")
    r = requests.post(f"{AUTH_URL}/login", json={"email": USER_EMAIL, "password": USER_PW})
    if r.status_code != 200:
        print(f"Error login: {r.text}")
        sys.exit(1)
        
    selection_token = r.json().get("data", {}).get("selection_token")
    r2 = requests.post(
        f"{AUTH_URL}/select-company",
        json={"company_id": COMPANY_ID},
        headers={"X-Selection-Token": selection_token}
    )
    return r2.json().get("data", {}).get("access_token")

def get_warehouse_and_concept(token):
    headers = {"Authorization": f"Bearer {token}", "X-Company-ID": COMPANY_ID}
    
    # 1. Fetch Warehouses
    r_wh = requests.get(f"{INV_URL}/inventory/warehouses", headers=headers)
    wh_data = r_wh.json().get("data", [])
    if not wh_data:
        print("[ERROR] No se encontraron warehouses en AWS.")
        sys.exit(1)
    wh_id = wh_data[0]["id"]
    
    # 2. Fetch Concepts
    r_conc = requests.get(f"{INV_URL}/inventory/concepts", headers=headers)
    conc_data = r_conc.json().get("data", [])
    entry_concepts = [c for c in conc_data if c["type"] == "ENTRY"]
    if not entry_concepts:
        print("[ERROR] No se encontraron conceptos de entrada en AWS.")
        sys.exit(1)
    concept_id = entry_concepts[0]["id"]
    
    # MAT-STRESS-01 Product UUID
    product_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"item.{COMPANY_ID}.MAT-STRESS-01")
    
    return wh_id, concept_id, str(product_id)


def run_aws_stress_test():
    print("\n" + "=" * 60)
    print("  AWS DENSITY GUARD SMOKE TEST -- Laissez-Faire (Phase 64)")
    print("  Target:", BACKEND_URL)
    print("=" * 60)

    token = get_auth_token()
    wh_id, concept_id, product_id = get_warehouse_and_concept(token)
    
    headers = {"Authorization": f"Bearer {token}", "X-Company-ID": COMPANY_ID}
    correlation_id = str(uuid.uuid4())
    
    payload = {
        "warehouse_id": str(wh_id),
        "type": "IN",
        "concept_id": str(concept_id),
        "correlation_id": correlation_id,
        "items": [
            {
                "product_id": str(product_id),
                "sku": "MAT-STRESS-01",
                "quantity": 500,
                "uom_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "interno.uom.PZA")),
                "location": LOCATION,
                "unit_price": 10.0,
                "weight": 500.0,
            }
        ]
    }

    print(f"\n[*] FIRE IN THE HOLE: Inyectando 500 uds -> {LOCATION}...")
    start = time.time()
    r = requests.post(f"{INV_URL}/inventory/documents", json=payload, headers=headers)
    end = time.time()

    if r.status_code in [200, 201, 202]:
        print(f"[OK] Response {r.status_code} from AWS en {((end-start)*1000):.1f}ms")
        print("\n[INSTRUCCION] Ahora, observa el DensityAlertPanel en el Frontend (CloudFront).")
        print("El sistema hara polling en <= 30 segs y debera capturar el CapacityViolationEvent.")
    else:
        print(f"[FAIL] Error {r.status_code}: {r.text}")

    print("=" * 60 + "\n")

if __name__ == "__main__":
    run_aws_stress_test()
