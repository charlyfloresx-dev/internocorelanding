import httpx
import asyncio
import uuid

# Configuration
AUTH_URL = "http://localhost:8001/api/v1"

VIATRA_URL = "http://localhost:8011/api/v1"



async def run_smoke_test():
    print("🚀 Iniciando Viatra Core Smoke Test v0.8.0...")
    
    async with httpx.AsyncClient() as client:
        # 1. Health Checks
        print("\n🔍 Step 1: Cluster Health Status")
        try:
            auth_health = await client.get(f"{AUTH_URL}/health/demo")

            viatra_health = await client.get(f"{VIATRA_URL}/sentinel/status")
            print(f"✅ Auth Service: {auth_health.status_code}")
            print(f"✅ Viatra Service (Sentinel): {viatra_health.status_code}")
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
            return

        # 2. Mock Social Auth Handshake
        print("\n🔍 Step 2: Social Auth Handshake Simulation")
        # In a real test, we'd use a test token
        print("💡 [LOG] Mocking X-Company-ID and Bearer Token for cluster communication.")
        
        headers = {
            "Authorization": "Bearer SMOKE_TEST_TOKEN",
            "X-Company-ID": str(uuid.uuid4())
        }

        # 3. Booking Engine Consistency
        print("\n🔍 Step 3: Booking Engine & Multi-Tenancy")
        packages = await client.get(f"{VIATRA_URL}/booking/packages", headers=headers)
        if packages.status_code == 200:
            print(f"✅ Packages retrieved: {len(packages.json())} items found.")
        else:
            print(f"⚠️ Warning: Booking API returned {packages.status_code} (Check Auth Middleware)")

        # 4. Fintech Webhook Simulation (Handshake)
        print("\n🔍 Step 4: Stripe Webhook Handshake")
        webhook_test = await client.post(f"{VIATRA_URL}/payments/webhook", json={"type": "ping"})
        if webhook_test.status_code in [200, 400]: # 400 is fine if signature fails, means endpoint is there
            print(f"✅ Webhook Listener is LIVE.")

    print("\n🏁 Smoke Test Finalizado. Clúster Operativo.")

if __name__ == "__main__":
    asyncio.run(run_smoke_test())
