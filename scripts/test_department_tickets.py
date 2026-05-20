"""
InternoCore Polymorphic Department Ticket Assignment and Visibility Test
========================================================================
Validates Phase 118 requirements:
1. Create a ticket with an assigned department.
2. Triage ticket with REASSIGN action to a department and verify individual assignments are cleared.
3. List tickets using department-based visibility filters.
"""
import requests
import uuid
import json
from pprint import pprint

AUTH_URL = "http://localhost:8001/api/v1"
TICKETS_URL = "http://localhost:8008/api/v1/tickets"


def authenticate():
    """Performs handshake T1/T2 and returns authenticated headers + company_id."""
    print("=" * 60)
    print("PASO 1: Auth (Handshake T1 & T2)")
    print("=" * 60)
    resp = requests.post(
        f"{AUTH_URL}/auth/login",
        json={"email": "charly@interno.com", "password": "charly123"}
    )
    if resp.status_code != 200:
        print(f"FAIL: Login failed ({resp.status_code}):", resp.text)
        return None, None
    
    login_data = resp.json()["data"]
    selection_token = login_data["selection_token"]
    companies = login_data.get("companies", [])
    
    if not companies:
        print("FAIL: No companies available for this user.")
        return None, None
    
    # Pick the first company dynamically
    target_company = companies[0]
    company_id = target_company["company_id"]
    print(f"   Using company: {target_company['company_name']} ({company_id})")
    
    resp = requests.post(
        f"{AUTH_URL}/auth/select-company",
        json={"company_id": company_id},
        headers={
            "Authorization": f"Bearer {selection_token}",
            "X-Selection-Token": selection_token
        }
    )
    if resp.status_code != 200:
        print(f"FAIL: Select-Company failed ({resp.status_code}):", resp.text)
        return None, None
    
    data = resp.json()["data"]
    access_token = data["access_token"]
    print(f"DONE: Authenticated successfully. Roles: {data.get('roles', [])}")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Company-ID": str(company_id),
        "X-Trace-Id": str(uuid.uuid4())
    }
    return headers, str(company_id)

def run_tests():
    headers, company_id = authenticate()
    if not headers:
        print("ABORT: Authentication failed.")
        return

    # 1. Create a Ticket with an assigned department
    print(f"\n{'=' * 60}")
    print("PASO 2: Crear Ticket con asignación de departamento")
    print("=" * 60)
    
    dept_id = str(uuid.uuid4())
    ticket_payload = {
        "company_id": company_id,
        "title": f"Downtime in Station B - Area {str(uuid.uuid4())[:8]}",
        "description": "Critical calibration required for plant sensors.",
        "ticket_type": "Soporte",
        "priority": "Alta",
        "assigned_department_id": dept_id,
        "area": "Plant Floor"
    }
    
    resp = requests.post(f"{TICKETS_URL}/", json=ticket_payload, headers=headers)
    if resp.status_code != 200:
        print(f"FAIL: Create ticket failed ({resp.status_code}): {resp.text}")
        return
        
    ticket = resp.json()["data"]
    ticket_id = ticket["id"]
    print(f"DONE: Ticket creado exitosamente con ID={ticket_id}")
    print(f"   - reference_code: {ticket.get('reference_code')}")
    print(f"   - assigned_department_id: {ticket.get('assigned_department_id')}")
    print(f"   - assigned_to_id: {ticket.get('assigned_to_id')}")

    # 2. Triage: REASSIGN to individual technician first
    print(f"\n{'=' * 60}")
    print("PASO 3: Triaje - Reasignar a Técnico Individual")
    print("=" * 60)
    
    tech_id = str(uuid.uuid4())
    triage_payload_tech = {
        "action": "REASSIGN",
        "new_assigned_to_id": tech_id,
        "comment": "Asignando temporalmente a técnico individual."
    }
    
    resp = requests.post(f"{TICKETS_URL}/{ticket_id}/triage", json=triage_payload_tech, headers=headers)
    if resp.status_code != 200:
        print(f"FAIL: Triage individual failed ({resp.status_code}): {resp.text}")
        return
        
    ticket = resp.json()["data"]
    print(f"DONE: Reasignado a técnico:")
    print(f"   - assigned_to_id: {ticket.get('assigned_to_id')}")
    print(f"   - assigned_department_id: {ticket.get('assigned_department_id')} (should be null after individual reassign)")

    # 3. Triage: REASSIGN to department (verify individual assignments cleared)
    print(f"\n{'=' * 60}")
    print("PASO 4: Triaje - Reasignar a Departamento (verificar limpieza atómica)")
    print("=" * 60)
    
    new_dept_id = str(uuid.uuid4())
    triage_payload_dept = {
        "action": "REASSIGN",
        "assigned_department_id": new_dept_id,
        "comment": "Devolviendo a cola de departamento para reasignación general."
    }
    
    resp = requests.post(f"{TICKETS_URL}/{ticket_id}/triage", json=triage_payload_dept, headers=headers)
    if resp.status_code != 200:
        print(f"FAIL: Triage departamento failed ({resp.status_code}): {resp.text}")
        return
        
    ticket = resp.json()["data"]
    print(f"DONE: Reasignado a departamento exitosamente:")
    print(f"   - assigned_department_id: {ticket.get('assigned_department_id')}")
    print(f"   - assigned_to_id: {ticket.get('assigned_to_id')} (must be null)")
    print(f"   - collaborator_id: {ticket.get('collaborator_id')} (must be null)")
    print(f"   - external_contact_id: {ticket.get('external_contact_id')} (must be null)")
    
    # Assertions
    ok = True
    if ticket.get("assigned_department_id") != new_dept_id:
        print("   [ FAIL ] Department ID does not match!")
        ok = False
    if ticket.get("assigned_to_id") is not None:
        print("   [ FAIL ] Individual technician ID was not cleared!")
        ok = False
    if ticket.get("collaborator_id") is not None:
        print("   [ FAIL ] Collaborator ID was not cleared!")
        ok = False
    if ticket.get("external_contact_id") is not None:
        print("   [ FAIL ] External contact ID was not cleared!")
        ok = False
    
    if ok:
        print("\n   [ OK ] La limpieza de asignaciones individuales fue atómica y correcta!")

    # 4. Query visibility via /mine route
    print(f"\n{'=' * 60}")
    print("PASO 5: Filtrado de Visibilidad por Departamento (GET /mine?department_id=...)")
    print("=" * 60)
    
    resp = requests.get(f"{TICKETS_URL}/mine", params={"department_id": new_dept_id}, headers=headers)
    if resp.status_code != 200:
        print(f"FAIL: GET /mine visibility filter failed ({resp.status_code}): {resp.text}")
        return
        
    my_tickets = resp.json()["data"]
    found = False
    for t in my_tickets:
        if t["id"] == ticket_id:
            found = True
            break
            
    print(f"DONE: Obtenidos {len(my_tickets)} tickets en bandeja personal /mine.")
    if found:
        print(f"   [ OK ] El ticket {ticket_id} fue correctamente filtrado por departamento!")
    else:
        print(f"   [ FAIL ] El ticket {ticket_id} no apareció en los resultados del departamento.")
        
    print(f"\n{'=' * 60}")
    print("FIN: Phase 118 — Pruebas Completadas")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
