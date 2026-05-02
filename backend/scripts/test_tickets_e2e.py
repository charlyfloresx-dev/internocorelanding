import asyncio
import httpx
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

async def validate_tickets():
    async with httpx.AsyncClient() as client:
        # 1. Login
        print("[*] Iniciando Login...")
        login_payload = {"email": "charly@interno.com", "password": "charly123"}
        try:
            r_login = await client.post(f"{BASE_URL}/auth/login", json=login_payload)
            if r_login.status_code != 200:
                print(f"[-] Error en login: {r_login.text}")
                return
            
            login_data = r_login.json()["data"]
            sel_token = login_data["selection_token"]
            
            # Buscamos la empresa de Charly (Interno Enterprise)
            companies = login_data["companies"]
            target_company = next((c for c in companies if "Interno" in c["company_name"]), companies[0])
            company_id = target_company["company_id"]
            
            # 2. Select Company
            print(f"[*] Seleccionando empresa: {target_company['company_name']} (ID: {company_id})...")
            r_sel = await client.post(
                f"{BASE_URL}/auth/select-company", 
                json={"company_id": company_id},
                headers={"Authorization": f"Bearer {sel_token}", "X-Selection-Token": sel_token}
            )
            if r_sel.status_code != 200:
                print(f"[-] Error en select-company: {r_sel.text}")
                return
            
            access_token = r_sel.json()["data"]["access_token"]
            headers = {
                "Authorization": f"Bearer {access_token}",
                "X-Company-ID": company_id,
                "X-Admin-Master-Key": "GOD_MODE_ACTIVE"
            }
            
            # 3. Create Ticket
            print("[*] Creando ticket industrial...")
            ticket_payload = {
                "title": f"Test Industrial {int(time.time())}",
                "description": "Falla en sensor de temperatura - Estación 04. Revisión requerida.",
                "priority": "Alta",
                "ticket_type": "Soporte",
                "area": "Producción",
                "company_id": company_id
            }
            r_ticket = await client.post(f"{BASE_URL}/tickets/", json=ticket_payload, headers=headers)
            if r_ticket.status_code != 200:
                print(f"[-] Error al crear ticket: {r_ticket.text}")
                return
            
            ticket = r_ticket.json()["data"]
            print(f"[+] Ticket creado con éxito: {ticket['reference_code']} (ID: {ticket['id']})")
            
            # 4. List Tickets
            print("[*] Listando tickets para verificar persistencia...")
            r_list = await client.get(f"{BASE_URL}/tickets/", headers=headers)
            tickets_list = r_list.json()["data"]
            print(f"[+] Total tickets encontrados: {len(tickets_list)}")
            
            # 5. Check Outbox (Optional validation)
            # print("📬 Verificando eventos en Outbox (vía DB)...")
            
        except Exception as e:
            print(f"[-] Error inesperado: {e}")

if __name__ == "__main__":
    asyncio.run(validate_tickets())
