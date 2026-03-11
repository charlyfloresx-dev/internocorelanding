import asyncio
import httpx
import uuid
import random
from datetime import datetime
import sys

# --- CONFIGURATION ---
BASE_URL = "http://localhost:8000/api/v1/mes"
# Use existing data from seed if available, or unique IDs for test
COMPANY_ID = "046c49b0-9d6c-4f1c-bbd6-c9452ed37f79" # Replace with actual if needed
RESOURCE_RESULT_ID = "a1b2c3d4-e5f6-a1b2-c3d4-e5f6a1b2c3d4" # Placeholder
USERS = [str(uuid.uuid4()) for _ in range(3)]
SKUS = ["PROD-A", "PROD-B", "BOX-Z"]

async def simulate():
    headers = {
        "X-Company-Id": COMPANY_ID,
        "Authorization": "Bearer SIMULATED_TOKEN" # Middleware current simplified check
    }
    
    async with httpx.AsyncClient(headers=headers, timeout=10.0) as client:
        print(f"🚀 Iniciando Simulador MES - InternoCore Matrix")
        
        # 1. Labor Registration
        print("👤 Registrando Operadores en Línea...")
        for user in USERS:
            try:
                await client.post(f"{BASE_URL}/labor/clock-in", json={
                    "resourceResultId": RESOURCE_RESULT_ID,
                    "userId": user,
                    "employeeNumber": random.randint(1000, 9999)
                })
            except Exception as e:
                print(f"Warning: Failed to clock-in user {user}: {e}")

        # 2. Production Scans (5 cycles)
        for i in range(5):
            sku = random.choice(SKUS)
            print(f"📦 [{i+1}/5] Escaneando SKU: {sku}...")
            await client.post(f"{BASE_URL}/scan", json={
                "resourceResultId": RESOURCE_RESULT_ID,
                "scanInput": sku,
                "localTxnId": str(uuid.uuid4())
            })
            await asyncio.sleep(5)

        # 3. Andon Failure (Mechanical)
        print("🚨 ALERTA: Falla Mecánica Detectada (Andon RED)")
        dt_res = await client.post(f"{BASE_URL}/downtime/open", json={
            "resourceResultId": RESOURCE_RESULT_ID,
            "description": "Sobrecalentamiento de motor principal",
            "reasonId": str(uuid.uuid4()) # Placeholder
        })
        downtime_id = dt_res.json()["data"]["id"]
        
        # Dashboard Check
        oee_check = await client.get(f"{BASE_URL}/dashboard/oee/{RESOURCE_RESULT_ID}")
        print(f"📊 Dashboard Status: {oee_check.json()['data']['andonStatus']}")

        print("⏳ Esperando respuesta técnica (20s)...")
        await asyncio.sleep(20)

        # 4. Technical Response
        print("🛠️ Técnico en Sitio (Andon YELLOW)")
        await client.patch(f"{BASE_URL}/downtime/{downtime_id}/respond")
        
        oee_check = await client.get(f"{BASE_URL}/dashboard/oee/{RESOURCE_RESULT_ID}")
        print(f"📊 Dashboard Status: {oee_check.json()['data']['andonStatus']}")

        await asyncio.sleep(5)
        
        # 5. Technical Close
        print("✅ Falla Corregida - Retomando Producción")
        await client.patch(f"{BASE_URL}/downtime/{downtime_id}/close", json={
            "actionTaken": "Cambio de sensor de temperatura"
        })

        # Final Scan
        print("📦 Escaneo Final post-reparación...")
        await client.post(f"{BASE_URL}/scan", json={
            "resourceResultId": RESOURCE_RESULT_ID,
            "scanInput": "PROD-A",
            "localTxnId": str(uuid.uuid4())
        })

        print("🏁 Simulación Completada. Dashboard listo para validación.")

if __name__ == "__main__":
    asyncio.run(simulate())
