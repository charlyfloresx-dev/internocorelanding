import asyncio
import httpx
import uuid
import sys

# Test de Integraci\u00f3n: WMS -> Inventory Service (SSOT Validated)
# Este script simula una Recepci\u00f3n de Mercanc\u00eda con IDs Sincronizados

async def test_integration():
    auth_url = "http://localhost:8001/api/v1/auth/login"
    wms_url = "http://localhost:8007/api/v1/inventory/documents/goods-receipt"
    inv_url = "http://localhost:8006/api/v1/inventory/transactions"

    # IDs FIJOS SEG\u00daN SEED SINCRONIZADO
    TARGET_COMPANY_ID = "00000000-0000-0000-0000-000000000001"
    TARGET_WAREHOUSE_ID = "00000000-0000-0000-0000-000000000001"
    TARGET_CONCEPT_ID = "00000000-0000-0000-0000-000000000001"
    TARGET_PRODUCT_ID = "00000000-0000-0000-0000-000000000001"
    TARGET_LOCATION_ID = "a7178d8e-4b14-477d-9e90-d40e904ac31e" # DOCK-01

    print("[*] Paso 1: Obteniendo Token de Acceso (Charly)...")
    login_data = {"email": "charly@internocore.app", "password": "Dell2024"}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            auth_res = await client.post(auth_url, json=login_data)
            if auth_res.status_code != 200:
                print(f"[!] Fall\u00f3 el login (Code {auth_res.status_code}): {auth_res.text}")
                return
            
            res_data = auth_res.json()
            selection_token = res_data["data"]["selection_token"]
            
            # Buscamos la empresa Planta Tijuana (0..01)
            company_id = None
            for comp in res_data["data"]["companies"]:
                if comp["company_id"] == TARGET_COMPANY_ID:
                    company_id = comp["company_id"]
                    break
            
            if not company_id:
                print(f"[!] No se encontr\u00f3 la empresa {TARGET_COMPANY_ID} en el login.")
                return

            print(f"[+] Handshake 1 completado. Company Sincronizada: {company_id}")

            # Paso 1.5: Seleccionar Empresa
            select_url = "http://localhost:8001/api/v1/auth/select-company"
            select_payload = {"company_id": company_id}
            select_headers = {"Authorization": f"Bearer {selection_token}"}
            
            select_res = await client.post(select_url, json=select_payload, headers=select_headers)
            if select_res.status_code != 200:
                print(f"[!] Fall\u00f3 la selecci\u00f3n de empresa: {select_res.text}")
                return
            
            token = select_res.json()["data"]["access_token"]
            print(f"[+] Handshake final completado. Access Token obtenido.")
            
            headers = {
                "Authorization": f"Bearer {token}",
                "X-Company-ID": str(company_id)
            }

            # Paso 2: Preparar Recepci\u00f3n de Mercanc\u00eda
            payload = {
                "folio": f"GR-{uuid.uuid4().hex[:6].upper()}",
                "warehouse_id": TARGET_WAREHOUSE_ID,
                "concept_id": TARGET_CONCEPT_ID,
                "company_id": str(company_id), 
                "items": [
                    {
                        "product_id": TARGET_PRODUCT_ID,
                        "quantity": 100.0,
                        "unit_cost": 25.50,
                        "location_id": TARGET_LOCATION_ID
                    }
                ]
            }

            print(f"[*] Paso 2: Enviando Goods Receipt al WMS (Folio: {payload['folio']})...")
            wms_res = await client.post(wms_url, json=payload, headers=headers)
            
            if wms_res.status_code != 200:
                print(f"[!] Error en WMS ({wms_res.status_code}): {wms_res.text}")
                # Intentar leer logs del servidor si es posible o mostrar respuesta
                return
            
            print(f"[+] WMS Confirmado: {wms_res.json()['message']}")
            
            # Paso 3: Verificar en Inventory Service
            print("[*] Paso 3: Verificando Kardex en Inventory Service...")
            inv_res = await client.get(f"{inv_url}?product_id={TARGET_PRODUCT_ID}", headers=headers)
            
            if inv_res.status_code == 200:
                transactions = inv_res.json()["data"]
                if len(transactions) > 0:
                    print(f"[\u2714] INTEGRACI\u00d3N EXITOSA: El Kardex tiene el registro.")
                    for tx in transactions:
                        print(f"    - Tx {tx['transaction_type']}: Cambio={tx['quantity_change']} Saldo={tx['new_balance']} Ref={tx['reference_id']}")
                        print(f"    - Metadata: {tx.get('comments')}")
                else:
                    print("[!] Alerta: El Kardex est\u00e1 vac\u00edo para este producto.")
            else:
                print(f"[!] No se pudo consultar el Kardex: {inv_res.status_code}")

        except Exception as e:
            print(f"[!] Error en el script de test: {e}")

if __name__ == "__main__":
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_integration())
