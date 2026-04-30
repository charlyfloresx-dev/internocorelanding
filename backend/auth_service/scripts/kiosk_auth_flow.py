
import requests
import json
import jwt

BASE_URL = "http://localhost:8001/api/v1/auth"

def test_rfid_flow(rfid_tag: str):
    """Simula el escaneo de una tarjeta RFID en el Kiosco."""
    print(f"\n[RFID FLOW] Escaneando Tag: {rfid_tag}")
    print("-" * 60)
    
    payload = {"rfid_tag": rfid_tag}
    try:
        response = requests.post(f"{BASE_URL}/collaborator/login", json=payload)
        response.raise_for_status()
        data = response.json().get("data")
        
        # Manejo de Descubrimiento (Si el RFID está en múltiples empresas)
        if data.get("selection_token"):
            print("Discovery: Multi-company detected.")
            company = data["companies"][0]
            print(f"   Auto-selecting: {company['company_name']}")
            
            headers = {"Authorization": f"Bearer {data['selection_token']}"}
            r_sel = requests.post(f"{BASE_URL}/select-company", json={"company_id": company["company_id"]}, headers=headers)
            r_sel.raise_for_status()
            token = r_sel.json()["data"]["access_token"]
        else:
            token = data["access_token"]
            
        print_token_info(token, "RFID OK")
    except Exception as e:
        print(f"ERR [RFID]: {e}")
        if 'response' in locals(): print(response.text)

def test_pin_flow(internal_id: str, pin: str):
    """Simula el escaneo de un código de barras + ingreso de PIN."""
    print(f"\n[PIN FLOW] Identidad: {internal_id} | PIN: {pin}")
    print("-" * 60)
    
    payload = {
        "internal_id": internal_id,
        "pin_code": pin
    }
    try:
        response = requests.post(f"{BASE_URL}/collaborator/login", json=payload)
        response.raise_for_status()
        data = response.json().get("data")
        
        if data.get("selection_token"):
            print("Discovery: Multi-company detected.")
            company = data["companies"][0]
            print(f"   Auto-selecting: {company['company_name']}")
            headers = {"Authorization": f"Bearer {data['selection_token']}"}
            r_sel = requests.post(f"{BASE_URL}/select-company", json={"company_id": company["company_id"]}, headers=headers)
            r_sel.raise_for_status()
            token = r_sel.json()["data"]["access_token"]
        else:
            token = data["access_token"]
            
        print_token_info(token, "ID+PIN OK")
    except Exception as e:
        print(f"ERR [PIN]: {e}")
        if 'response' in locals(): print(response.text)

def print_token_info(token, status_label):
    decoded = jwt.decode(token, options={"verify_signature": False})
    print(f"[OK] {status_label}")
    print(f"   Name:        {decoded.get('full_name')}")
    print(f"   Internal ID: {decoded.get('internal_id')}")
    print(f"   Company ID:  {decoded.get('cid')}")
    print(f"   Supervisor:  {decoded.get('is_supervisor')}")
    print(f"   WarehouseID: {decoded.get('wid')}")
    print(f"   Perms:       {decoded.get('permissions')}")

if __name__ == "__main__":
    print("\n" + "="*70)
    print("      INTERNO CORE - INDUSTRIAL AUTHENTICATION TEST SUITE")
    print("="*70)
    
    # 1. Prueba de RFID (Ej. Luis Torres - Logistics)
    test_rfid_flow("2327559684")
    
    # 2. Prueba de ID + PIN (Ej. Carlos Ramirez - Industrial Admin)
    test_pin_flow("003709A", "1234")
