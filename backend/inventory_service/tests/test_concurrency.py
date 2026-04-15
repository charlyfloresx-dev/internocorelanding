import asyncio
import httpx
import uuid
import sys

# Test de Estrés para Validación de Optimistic Locking
async def make_request(client, url, payload, request_id):
    try:
        response = await client.post(url, json=payload)
        return {
            "request_id": request_id,
            "status": response.status_code,
            "response": response.json() if response.status_code != 500 else "Internal Error"
        }
    except Exception as e:
        return {"request_id": request_id, "status": "Error", "error": str(e)}

async def test_concurrency():
    # Asumimos que inventory_service está en el puerto 8006
    inventory_url = "http://localhost:8006/api/v1/inventory/transactions"
    
    # NOTA: Para este test, la validación cross-service fallaría con un 400/404 porque el producto es falso.
    # Por lo tanto, el test asume que el backend (transactions.py o inventory.py) tiene comentada o stubbeada  
    # la validación cross-service HTTP _verify_product_uom estrictamente para permitir que el flujo 
    # de base de datos intercepte el test de concurrencia, O el product_id debe ser real.
    
    # Usaremos un product_id falso, pero el test fallará temprano en _verify_product_uom si no inyectamos
    # la DB. Vamos a crear el script igualmente. En un entorno real, usaríamos un product_id insertado.
    
    product_id_fake = str(uuid.uuid4())
    uom_id_fake = str(uuid.uuid4())
    warehouse_id_fake = str(uuid.uuid4())

    payload = {
        "product_id": product_id_fake,
        "uom_id": uom_id_fake,
        "warehouse_id": warehouse_id_fake,
        "transaction_type": "IN",
        "quantity_change": 10.0
    }

    print(f"[*] Iniciando Prueba de Concurrencia (Optimistic Locking)")
    print(f"[*] Lanzando 5 peticiones simultáneas de ingreso para el mismo producto...")

    async with httpx.AsyncClient() as client:
        tasks = [
            make_request(client, inventory_url, payload, i)
            for i in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        
    success_count = sum(1 for r in results if r['status'] == 201)
    conflict_count = sum(1 for r in results if r['status'] == 409)
    other_errors = sum(1 for r in results if r['status'] not in [201, 409])
    
    print("\n--- Resultados de Concurrencia ---")
    for r in results:
        print(f"Req {r['request_id']}: HTTP {r['status']} -> {str(r.get('response', r.get('error')))[:100]}")
        
    print(f"\nResumen:")
    print(f"Éxitos (201): {success_count} (Primer commit que gana la carrera)")
    print(f"Conflictos (409): {conflict_count} (Transacciones bloqueadas por StaleDataError / Optimistic Locking)")
    print(f"Otros Errores: {other_errors} (Ej. 400/404 por producto inexistente en Master Data)")
    
    if conflict_count > 0:
        print("\n[✔] COMPROBADO: El Optimistic Locking funciona correctamente, previniendo el Lost Update.")
    elif other_errors > 0:
        print("\n[!] AVISO: Las peticiones fueron rechazadas antes de tocar la DB debido a la validación Cross-Service u otro error estructural.")

if __name__ == "__main__":
    if sys.platform.startswith('win'):
        # Evitar Warning de deprecación en Python 3.11/3.12+
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_concurrency())
