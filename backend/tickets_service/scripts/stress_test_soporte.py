import asyncio
import httpx
import uuid
import time
import sys
import os

# Ajuste de path para encontrar 'common'
sys.path.append(os.path.join(os.getcwd(), "backend"))

from common.testing.auth_client import InternoAuthClient

TICKETS_URL = "http://localhost:8004/api/v1/tickets"
AUTH_URL = "http://localhost:8001/api/v1/auth"

async def stress_test_soporte():
    print("--- INICIANDO STRESS TEST: SOPORTE AI & ESCALACIÓN (Common Auth Client) ---")
    
    # 1. Auth Flow usando el nuevo Helper
    auth_client = InternoAuthClient(AUTH_URL)
    if not await auth_client.login("charly@interno.com", "charly123"):
        print("[-] Fallo el login")
        return
    
    # Seleccionamos la empresa (ENTERPRISE_ID)
    company_id = "9cd9986b-89da-48b7-8733-26a2a1225b01"
    if not await auth_client.select_company(company_id):
        print("[-] Fallo la seleccion de empresa")
        return
    
    headers = auth_client.get_headers()
    print("[+] Autenticación exitosa.")

    async with httpx.AsyncClient() as client:
        # 2. Crear Ticket de Soporte
        print("[*] Creando ticket de SOPORTE...")
        ticket_data = {
            "title": f"Stress Test AI {int(time.time())}",
            "description": "La impresora Zebra en Piso 2 no reconoce etiquetas. Posible falla de sensor térmico.",
            "priority": "Alta",
            "ticket_type": "Soporte",
            "area": "Soporte",
            "company_id": company_id
        }
        r_create = await client.post(f"{TICKETS_URL}/", headers=headers, json=ticket_data)
        if r_create.status_code != 200:
            print(f"[-] Error al crear ticket: {r_create.text}")
            return
        
        ticket = r_create.json()["data"]
        ticket_id = ticket["id"]
        print(f"[+] Ticket creado: {ticket['reference_code']} (ID: {ticket_id})")

        # 3. Verificar Comentario AI (Phase 8 Preview)
        print("[*] Esperando procesamiento AI (5s)...")
        await asyncio.sleep(5)
        
        r_comments = await client.get(f"{TICKETS_URL}/{ticket_id}/comments", headers=headers)
        r_json = r_comments.json()
        comments = r_json.get("data") or []
        
        ai_comment = next((c for c in comments if "Interno AI Assistant" in c["content"]), None)
        if ai_comment:
            print("\n[VIRTUAL ASSISTANT RESPONSE]:")
            print("-" * 50)
            print(ai_comment['content'])
            print("-" * 50)
        else:
            print("[-] NO se detectó comentario AI. ¿Está activada la lógica en el servicio?")

        print("\n--- TEST COMPLETADO ---")

if __name__ == "__main__":
    asyncio.run(stress_test_soporte())
