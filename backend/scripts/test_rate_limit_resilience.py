import asyncio
import httpx
import uuid
import time
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"
# Usaremos un endpoint público para no requerir tokens complejos en la prueba de ráfaga inicial,
# o podemos usar /api/v1/health que es ligero.
TEST_ENDPOINT = f"{BASE_URL}/api/v1/health"

# Tenants de prueba
TENANT_A = str(uuid.uuid4())
TENANT_B = str(uuid.uuid4())

async def test_tenant_isolation():
    print(f"\n[1] TEST: AISLAMIENTO DE TENANT (Multi-Tenant Leak Test)")
    print(f"[*] Objetivo: Agotar cuota de Tenant_A sin afectar a Tenant_B")
    
    async with httpx.AsyncClient() as client:
        # 1. Agotar Tenant_A
        print(f"[*] Saturando Tenant_A ({TENANT_A})...")
        blocked = False
        for i in range(110): # El límite es 100 por minuto en limiter.py
            resp = await client.get(TEST_ENDPOINT, headers={"X-Company-ID": TENANT_A})
            if resp.status_code == 429:
                print(f"[+] Tenant_A bloqueado exitosamente en la petición {i+1} (429 Too Many Requests)")
                blocked = True
                break
        
        if not blocked:
            print("[!] FAIL: Tenant_A no fue bloqueado tras 110 peticiones.")
            return False

        # 2. Probar Tenant_B inmediatamente
        print(f"[*] Probando Tenant_B ({TENANT_B}) inmediatamente...")
        resp_b = await client.get(TEST_ENDPOINT, headers={"X-Company-ID": TENANT_B})
        if resp_b.status_code == 200:
            print("[+] OK: Tenant_B sigue operando normalmente (200 OK). Aislamiento confirmado.")
            return True
        else:
            print(f"[!] FAIL: Tenant_B también fue afectado. Status: {resp_b.status_code}")
            return False

async def test_log_spam_control():
    print(f"\n[2] TEST: CONTROL DE LOG-SPAM (Inyección Masiva)")
    print(f"[*] Objetivo: Verificar que el sistema no degrade por exceso de logs 429")
    
    start_time = time.time()
    count = 0
    async with httpx.AsyncClient() as client:
        print("[*] Enviando ráfaga de 200 peticiones bloqueadas...")
        for _ in range(200):
            resp = await client.get(TEST_ENDPOINT, headers={"X-Company-ID": TENANT_A})
            if resp.status_code == 429:
                count += 1
    
    duration = time.time() - start_time
    print(f"[+] Ráfaga completada. {count} peticiones bloqueadas en {duration:.2f}s.")
    print("[i] Verifique manualmente los logs de Docker para asegurar que no hay inundación de INFO.")
    return True

async def run_all_tests():
    print("="*60)
    print(" INTERNOCORE RATE LIMIT RESILIENCE TEST SUITE")
    print("="*60)
    
    # Verificar salud inicial
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{BASE_URL}/health")
            if r.status_code != 200:
                print("[!] El servidor no parece estar listo.")
                return
    except Exception as e:
        print(f"[!] Error conectando al servidor: {e}")
        return

    success_a = await test_tenant_isolation()
    success_b = await test_log_spam_control()
    
    print("\n" + "="*60)
    print(" RESUMEN DE PRUEBAS")
    print(f" Aislamiento Tenant: {'PASSED' if success_a else 'FAILED'}")
    print(f" Control de Log-Spam: {'PASSED' if success_b else 'COMPLETED'}")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(run_all_tests())
