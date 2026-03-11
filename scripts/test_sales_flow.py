"""
InternoCore E2E Sales Flow Test
================================
Tests the full sales flow: Auth T1/T2 -> WMS Create Order -> WMS Dispatch -> Inventory Verification.

Credentials: admin@interno.com / admin123456
Company: Interno Logistics (ad6cc8a6-34f9-42df-8f29-28254e0ad242)
"""
import requests
import json
import uuid
from pprint import pprint

AUTH_URL = "http://localhost:8001/api/v1"
WMS_URL = "http://localhost:8007/api/v1"
INV_URL = "http://localhost:8006/api/v1"

# --- Constantes del Seed ---
CO_LOGISTICS_ID = "ad6cc8a6-34f9-42df-8f29-28254e0ad242"


def authenticate():
    """Realiza el handshake T1/T2 y retorna headers autenticados."""
    # --- T1: Login -> selection_token ---
    print("=" * 60)
    print("PASO 1: Login (Handshake T1)")
    print("=" * 60)
    resp = requests.post(
        f"{AUTH_URL}/auth/login",
        json={"email": "admin@interno.com", "password": "admin123456"}
    )
    if resp.status_code != 200:
        print(f"FAIL: Login fallido ({resp.status_code}):", resp.text)
        return None
    
    login_data = resp.json()["data"]
    selection_token = login_data["selection_token"]
    
    print(f"DONE: Login exitoso. Empresas disponibles:")
    for c in login_data["companies"]:
        marker = " [TARGET]" if c["company_id"] == CO_LOGISTICS_ID else ""
        print(f"   * {c['company_name']} ({c['company_id']}){marker}")
    
    # --- T2: Select Company -> access_token ---
    print(f"\n{'=' * 60}")
    print(f"PASO 2: Select Company (Handshake T2) -> Interno Logistics")
    print("=" * 60)
    resp = requests.post(
        f"{AUTH_URL}/auth/select-company",
        json={"company_id": CO_LOGISTICS_ID},
        headers={
            "Authorization": f"Bearer {selection_token}",
            "X-Selection-Token": selection_token
        }
    )
    if resp.status_code != 200:
        print(f"FAIL: Select-Company fallido ({resp.status_code}):", resp.text)
        return None
    
    data = resp.json()["data"]
    access_token = data["access_token"]
    roles = data.get("roles", [])
    print(f"DONE: Token de acceso obtenido. Roles: {roles}")

    # DEBUG: Inspeccionar Claims del JWT
    try:
        import base64
        import json
        payload_b64 = access_token.split(".")[1]
        payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
        claims = json.loads(base64.urlsafe_b64decode(payload_b64).decode())
        print(f"DEBUG: JWT Modules Claim: {claims.get('modules', 'MISSING')}")
        print(f"DEBUG: JWT Full Claims: {claims}")
    except Exception as e:
        print(f"DEBUG: Error decodificando JWT: {e}")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Company-ID": CO_LOGISTICS_ID,
        "X-Trace-Id": str(uuid.uuid4())
    }
    return headers


def get_seed_uuids():
    """Calcula los UUIDs deterministas del seed."""
    item_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, "interno.item.MAT-001"))
    warehouse_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.wh.WH-TIJ.{CO_LOGISTICS_ID}"))
    uom_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, "interno.uom.PZA"))
    return item_id, warehouse_id, uom_id


def step_query_price_stock(headers, item_id, warehouse_id):
    """Paso 3: Consultar precio y stock."""
    print(f"\n{'=' * 60}")
    print("PASO 3: Consulta de Precio y Stock (GET /sales/price-stock)")
    print("=" * 60)
    resp = requests.get(
        f"{WMS_URL}/sales/price-stock",
        params={"product_id": item_id, "warehouse_id": warehouse_id},
        headers=headers
    )
    if resp.status_code == 200:
        data = resp.json()["data"]
        print("DONE: Respuesta:")
        pprint(data)
        return data
    else:
        print(f"WARN: Price-Stock no disponible ({resp.status_code}): {resp.text}")
        return None


def step_create_sales_order(headers, item_id, warehouse_id, uom_id, quantity=5.0):
    """Paso 4: Crear Orden de Venta."""
    print(f"\n{'=' * 60}")
    print(f"PASO 4: Crear Orden de Venta ({quantity} unidades)")
    print("=" * 60)
    folio = f"SO-{str(uuid.uuid4())[:8].upper()}"
    order_payload = {
        "folio": folio,
        "product_id": item_id,
        "warehouse_id": warehouse_id,
        "uom_id": uom_id,
        "quantity": quantity,
        "observations": "Orden de Prueba E2E - Sales Flow"
    }
    print(f"   Folio: {folio}")
    
    try:
        resp = requests.post(
            f"{WMS_URL}/sales-orders/",
            json=order_payload,
            headers=headers,
        )
        if resp.status_code == 200:
            order = resp.json()["data"]
            print(f"DONE: Orden creada: ID={order['id']} | Status={order['status']}")
            return order
        else:
            print(f"FAIL: Error creando orden ({resp.status_code}): {resp.text}")
            return None
    except Exception as e:
        print(f"FAIL: Error de conexion: {e}")
        return None


def step_dispatch_order(headers, order_id, warehouse_id):
    """Paso 5: Despachar la Orden."""
    print(f"\n{'=' * 60}")
    print(f"PASO 5: Despacho de Orden (POST /sales/dispatch)")
    print("=" * 60)
    dispatch_payload = {
        "sales_order_id": order_id,
        "warehouse_id": warehouse_id,
    }
    resp = requests.post(
        f"{WMS_URL}/sales/dispatch",
        json=dispatch_payload,
        headers=headers,
    )
    if resp.status_code == 200:
        result = resp.json()["data"]
        print(f"DONE: Orden despachada: Status={result['status']}")
        return result
    else:
        print(f"FAIL: Despacho fallido ({resp.status_code}): {resp.text}")
        return None


def step_verify_inventory(headers, item_id, warehouse_id):
    """Paso 6: Verificar transacciones de inventario."""
    print(f"\n{'=' * 60}")
    print("PASO 6: Verificacion de Inventario (Kardex)")
    print("=" * 60)
    resp = requests.get(
        f"{INV_URL}/inventory/transactions",
        params={"product_id": item_id, "warehouse_id": warehouse_id, "limit": 5},
        headers=headers,
    )
    if resp.status_code == 200:
        data = resp.json()
        txns = data.get("data", [])
        print(f"DONE: Ultimas {len(txns)} transacciones:")
        for t in txns:
            print(f"   [{t.get('transaction_type', '?')}] qty={t.get('quantity_change', '?')} | balance={t.get('new_balance', '?')}")
        return txns
    else:
        print(f"WARN: No se pudieron obtener transacciones ({resp.status_code}): {resp.text}")
        return None


def main():
    print("RUN: InternoCore E2E Sales Flow Test")
    print("=" * 60)
    
    # 1-2: Autenticacion
    headers = authenticate()
    if not headers:
        print("\nABORT: Fallo en autenticacion.")
        return
    
    # Calcular UUIDs del seed
    item_id, warehouse_id, uom_id = get_seed_uuids()
    print(f"\nINFO: IDs del Seed:")
    print(f"   Product (MAT-001): {item_id}")
    print(f"   Warehouse (WH-TIJ): {warehouse_id}")
    
    # 3: Consultar precio/stock inicial
    initial_data = step_query_price_stock(headers, item_id, warehouse_id)
    
    # 4: Crear Orden de Venta
    order = step_create_sales_order(headers, item_id, warehouse_id, uom_id, quantity=5.0)
    if not order:
        print("\nABORT: Fallo en creacion de orden.")
        return
    
    # 5: Despachar
    dispatch = step_dispatch_order(headers, order["id"], warehouse_id)
    if not dispatch:
        print("\nABORT: Fallo en despacho.")
        return
    
    # 6: Verificar transacciones en inventario
    step_verify_inventory(headers, item_id, warehouse_id)
    
    # 7: Verificar stock post-despacho
    print(f"\n{'=' * 60}")
    print("PASO 7: Verificacion Final de Stock")
    print("=" * 60)
    final_data = step_query_price_stock(headers, item_id, warehouse_id)
    
    if initial_data and final_data:
        initial_stock = initial_data.get("stock_on_hand", "N/A")
        final_stock = final_data.get("stock_on_hand", "N/A")
        print(f"\nRESUMEN: Stock Inicial={initial_stock} -> Stock Final={final_stock}")
    
    print(f"\n{'=' * 60}")
    print("FIN: E2E Sales Flow Test Finalizado")
    print("=" * 60)


if __name__ == "__main__":
    main()
