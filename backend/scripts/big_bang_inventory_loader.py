"""
InternoCore Phase 100: Big Bang Inventory Loader
Inyecta 1M de registros Kardex en modo industrial.

Uso: python backend/scripts/big_bang_inventory_loader.py
Requiere: .env en la raíz con CORE_INTERNAL_API_KEY
          backend/.env con TEST_COMPANY_ID, TEST_PRODUCT_ID, TEST_WAREHOUSE_ID
"""
import asyncio
import httpx
import uuid
import time
import random
from datetime import datetime

import os
from dotenv import dotenv_values

# Cargar configuración: merge de .env raíz + backend/.env
_config = {**dotenv_values(".env"), **dotenv_values("backend/.env")}

# CONFIGURACIÓN DINÁMICA
BASE_URL = _config.get("CORE_API_EXTERNAL_URL", "http://localhost:8000") + "/api/v1/inventory"
INTERNAL_SECRET = _config.get("CORE_INTERNAL_API_KEY")
COMPANY_ID = _config.get("TEST_COMPANY_ID")
PRODUCT_ID = _config.get("TEST_PRODUCT_ID")
WAREHOUSE_ID = _config.get("TEST_WAREHOUSE_ID")

# Pre-flight check
_missing = [k for k, v in {"INTERNAL_SECRET": INTERNAL_SECRET, "COMPANY_ID": COMPANY_ID,
            "PRODUCT_ID": PRODUCT_ID, "WAREHOUSE_ID": WAREHOUSE_ID}.items() if not v]
if _missing:
    raise SystemExit(f"ABORT: Missing config: {', '.join(_missing)}. Check .env files.")

TOTAL_RECORDS = 1_000_000
BATCH_SIZE = 1_000  # Conservador: 1k por batch (probado y seguro)
CONCURRENCY = 3     # Máximo 3 batches en paralelo para no saturar uvicorn

async def inject_batch(client: httpx.AsyncClient, batch_num: int):
    movements = []
    current_balance = float(batch_num * 500)
    
    for i in range(BATCH_SIZE):
        t_type = random.choice(["IN", "OUT", "ADJUSTMENT", "TRANSFER"])
        qty = float(random.randint(1, 50))
        
        prev_b = current_balance
        if t_type == "OUT":
            qty_change = -qty
        else:
            qty_change = qty
        current_balance += qty_change
        
        movements.append({
            "product_id": PRODUCT_ID,
            "warehouse_id": WAREHOUSE_ID,
            "transaction_type": t_type,
            "quantity_change": qty_change,
            "previous_balance": prev_b,
            "new_balance": current_balance,
            "comments": f"Phase100 B{batch_num} S{i}"
        })

    headers = {
        "X-Internal-Secret": INTERNAL_SECRET,
        "X-Company-ID": COMPANY_ID,
    }

    start_time = time.time()
    try:
        response = await client.post(
            f"{BASE_URL}/bulk-load",
            json={"movements": movements},
            headers=headers,
            timeout=120.0  # 2 min timeout por batch
        )
        elapsed = time.time() - start_time
        
        if response.status_code in (200, 201):
            print(f"[+] Batch {batch_num}/{TOTAL_RECORDS // BATCH_SIZE}: {BATCH_SIZE} records in {elapsed:.1f}s")
            return True
        else:
            print(f"[!] Batch {batch_num} FAILED: HTTP {response.status_code} - {response.text[:200]}")
            return False
    except Exception as e:
        print(f"[!] Batch {batch_num} EXCEPTION: {type(e).__name__}: {str(e)[:200]}")
        return False

async def preflight_check(client: httpx.AsyncClient):
    """Verifica que el monolito esté vivo antes de lanzar la carga."""
    print("[*] Pre-flight: Verificando salud del monolito...")
    try:
        r = await client.get("http://localhost:8000/health", timeout=10)
        if r.status_code == 200:
            print("[✓] Monolito HEALTHY")
            return True
    except Exception as e:
        print(f"[✗] Monolito NO responde: {type(e).__name__}")
    return False

async def main():
    total_batches = TOTAL_RECORDS // BATCH_SIZE
    
    print("=" * 60)
    print(" INTERNOCORE PHASE 100: THE BIG BANG (1M RECORDS)")
    print("=" * 60)
    print(f"[*] Objetivo: {TOTAL_RECORDS:,} registros Kardex")
    print(f"[*] Batch Size: {BATCH_SIZE:,} | Batches: {total_batches}")
    print(f"[*] Concurrencia: {CONCURRENCY}")
    print(f"[*] Bypass Secret: {'ACTIVE' if INTERNAL_SECRET else 'MISSING'}")
    print(f"[*] Company: {COMPANY_ID}")
    
    async with httpx.AsyncClient() as client:
        # Pre-flight
        if not await preflight_check(client):
            raise SystemExit("ABORT: Monolith is not healthy. Run hard-reset first.")
        
        # Inyección semi-paralela controlada
        total_start = time.time()
        semaphore = asyncio.Semaphore(CONCURRENCY)
        
        async def sem_inject(b):
            async with semaphore:
                return await inject_batch(client, b)

        tasks = [sem_inject(i + 1) for i in range(total_batches)]
        results = await asyncio.gather(*tasks)
        
    total_end = time.time()
    success_count = sum(1 for r in results if r)
    
    print("\n" + "=" * 60)
    print(f" RESUMEN DEL BIG BANG")
    print(f" Batches Exitosos: {success_count}/{total_batches}")
    print(f" Registros Totales: {success_count * BATCH_SIZE:,}")
    print(f" Tiempo Total: {total_end - total_start:.1f}s")
    if total_end > total_start:
        print(f" Velocidad: {(success_count * BATCH_SIZE) / (total_end - total_start):,.0f} rec/s")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
