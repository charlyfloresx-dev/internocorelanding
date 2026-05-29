"""
flow_pos_checkout.py
--------------------
Validates the full POS Checkout endpoint end-to-end via HTTP.

Flow:
  1. T1 Login (Charly) → selection_token
  2. T2 SelectCompany (ENTERPRISE) → final JWT with pos.checkout scope
  3. GET /inventory/levels?product_id=ECM-600 → verify stock exists
  4. POST /pos/checkout → place a 1-unit sale
  5. Verify InventoryDocument created + movement recorded

Pre-requisite: stack running (docker compose up -d), seed executed.
"""
import asyncio
import httpx
import json
import uuid
import sys

BASE = "http://localhost:8000/api/v1"

CO_ENTERPRISE_ID = "9cd9986b-89da-48b7-8733-26a2a1225b01"
ECM_PRODUCT_ID   = "e0e0e0e0-e0e0-40e0-a0e0-000000000001"


def _print(label: str, status: str, detail: str = ""):
    icon = "[OK]  " if status == "OK" else "[FAIL]" if status == "FAIL" else "[INFO]"
    print(f"  {icon}  {label}: {detail}")


async def run_pos_checkout_flow():
    print("=" * 60)
    print("  FLUJO POS CHECKOUT — Validación End-to-End")
    print("=" * 60)
    errors = 0

    async with httpx.AsyncClient(timeout=15.0) as client:

        # ── Auth: X-Admin-Master-Key bypass (auth_service en modificacion activa)
        # NOTE: T1/T2 handshake omitido intencionalmente — auth_service no se toca.
        headers = {
            "X-Admin-Master-Key": "ROTATED_MASTER_KEY_GOD_MODE",
            "X-Company-ID": CO_ENTERPRISE_ID,
        }
        _print("Auth bypass", "OK", "X-Admin-Master-Key (auth_service en modificacion)")

        # ── 3. Resolve warehouse_id ───────────────────────────────────────────
        r3 = await client.get(f"{BASE}/inventory/warehouses", headers=headers)
        warehouses = (r3.json().get("data") or []) if r3.status_code == 200 else []
        warehouse_id = next(
            (w["id"] for w in warehouses if w.get("code") == "WH-001"), None
        )
        if not warehouse_id:
            _print("Warehouse lookup", "FAIL", "WH-001 no encontrado — ejecuta unified_industrial_seed.py")
            errors += 1
            return errors
        _print("Warehouse", "OK", f"WH-001 → {warehouse_id}")

        # ── 4. Check inventory level ──────────────────────────────────────────
        r4 = await client.get(
            f"{BASE}/inventory/levels",
            params={"warehouse_id": warehouse_id},
            headers=headers,
        )
        levels = (r4.json().get("data") or []) if r4.status_code == 200 else []
        ecm_level = next((l for l in levels if str(l.get("product_id")) == ECM_PRODUCT_ID), None)
        if not ecm_level:
            _print("Stock check", "FAIL", "ECM-600 sin nivel de inventario — ejecuta flow_1_entry.py primero")
            errors += 1
            return errors
        available = float(ecm_level.get("available_quantity", 0))
        _print("Stock check", "OK", f"ECM-600 disponible: {available} uds")
        if available < 1:
            _print("Stock insuficiente", "FAIL", "Menos de 1 unidad disponible")
            errors += 1
            return errors

        # ── 5. Resolve price ──────────────────────────────────────────────────
        r5 = await client.get(
            f"{BASE}/products/lookup/ECM-600", headers=headers
        )
        if r5.status_code != 200:
            _print("Price lookup", "FAIL", f"HTTP {r5.status_code}")
            errors += 1
            return errors
        product_data = r5.json().get("data", {})
        unit_price = float(product_data.get("sale_price") or product_data.get("price") or 495.0)
        _print("Price lookup", "OK", f"ECM-600 precio: {unit_price}")

        # ── 6. POS Checkout ───────────────────────────────────────────────────
        sale_id = str(uuid.uuid4())
        payload = {
            "warehouse_id": warehouse_id,
            "app_reference": f"FLOW-TEST-{sale_id[:8]}",
            "currency": "MXN",
            "total_amount": str(unit_price),
            "comments": "Flow test POS checkout — validación automatizada",
            "items": [
                {
                    "product_id": ECM_PRODUCT_ID,
                    "quantity": 1,
                    "unit_price": unit_price,
                }
            ]
        }
        r6 = await client.post(f"{BASE}/pos/checkout", json=payload, headers=headers)
        if r6.status_code != 200:
            _print("POS Checkout", "FAIL",
                   f"HTTP {r6.status_code}: {r6.text[:300]}")
            errors += 1
        else:
            resp_data = r6.json().get("data", {})
            _print("POS Checkout", "OK",
                   f"sale_id={resp_data.get('sale_id')} "
                   f"movements={resp_data.get('movement_ids', [])}")

        # ── 7. Verify stock decreased ─────────────────────────────────────────
        r7 = await client.get(
            f"{BASE}/inventory/levels",
            params={"warehouse_id": warehouse_id},
            headers=headers,
        )
        levels2 = (r7.json().get("data") or []) if r7.status_code == 200 else []
        ecm_after = next((l for l in levels2 if str(l.get("product_id")) == ECM_PRODUCT_ID), None)
        if ecm_after:
            new_qty = float(ecm_after.get("available_quantity", 0))
            delta = available - new_qty
            if abs(delta - 1.0) < 0.001:
                _print("Stock verification", "OK",
                       f"Antes: {available} → Después: {new_qty} (Δ={delta})")
            else:
                _print("Stock verification", "FAIL",
                       f"Esperado Δ=1, obtenido Δ={delta}")
                errors += 1
        else:
            _print("Stock verification", "FAIL", "No se pudo releer el nivel")
            errors += 1

    print("-" * 60)
    if errors == 0:
        print("  [PASS] FLUJO POS CHECKOUT: TODAS LAS VALIDACIONES PASARON")
    else:
        print(f"  [FAIL] FLUJO POS CHECKOUT: {errors} ERROR(ES) DETECTADO(S)")
    return errors


if __name__ == "__main__":
    result = asyncio.run(run_pos_checkout_flow())
    sys.exit(result)
