import asyncio
import httpx
import uuid
import sys

# Script de prueba unitaria de integridad referencial
async def test_referential_integrity():
    # Asumimos que inventory_service estará en el puerto 8006 tal como dictaminamos
    inventory_url = "http://localhost:8006/api/v1/inventory/transactions"
    
    product_id_fake = str(uuid.uuid4())
    uom_id_fake = str(uuid.uuid4())
    warehouse_id_fake = str(uuid.uuid4())

    payload = {
        "product_id": product_id_fake,
        "uom_id": uom_id_fake,
        "warehouse_id": warehouse_id_fake,
        "transaction_type": "IN",
        "quantity_change": 100.5
    }

    print(f"[*] Evaluando validación Cross-Service contra el Master Data...")
    print(f"[*] Intentando asentar un movimiento con product_id inexistente: {product_id_fake}")

    try:
        async with httpx.AsyncClient() as client:
            # Mandamos un request a nuestro nuevo Inventory Service
            response = await client.post(inventory_url, json=payload)
    except Exception as e:
        print(f"[ERROR DE RED] No se pudo conectar al inventory_service en {inventory_url}: {e}")
        return

    # Verificar si el Endpoint se encuentra levantado (404/Method Not Allowed si la ruta es mala)
    if response.status_code == 404 and "detail" not in response.json():
        print("[!] Endpoint no encontrado. ¿Está levantado el servicio?")
        return
        
    # Verificar la respuesta de la lógica de negocio   
    print(f"[*] Status code retornado: {response.status_code}")
    
    resp_data = response.json()
    print(f"[*] Response payload: {resp_data}")

    # En este test esperamos que si descomentamos la validación cross-service,
    # explote con un 400 Bad Request
    if response.status_code in [400, 404]:
         print("[✔] COMPROBADO: El sistema previene inserciones de Kardex para productos inventados.")
    else:
         print("[✗] FALLO: El sistema permitió el registro o actuó de forma inesperada sin validar el MDS.")

if __name__ == "__main__":
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_referential_integrity())
