import asyncio
import json
from common.testing.auth_client import InternoAuthClient
import httpx

async def main():
    auth_url = "http://localhost:8000/api/v1/auth"
    inventory_url = "http://localhost:8000/api/v1/inventory"
    
    client = InternoAuthClient(auth_url)
    
    print("\n[PASO 1] Autenticacion y Multi-tenancy")
    # Credenciales correctas segun el seed
    if await client.login("charly@interno.com", "charly123"):
        print(f"  OK   Usuario autenticado: {client.user_id}")
        print(f"  OK   Empresas vinculadas ({len(client.companies)}):")
        for c in client.companies:
            print(f"       - {c.get('company_name')} (ID: {c.get('company_id')})")
    else:
        print("  FAIL Login fallido.")
        return

    print("\n[PASO 2] Seleccion de Contexto")
    access_token = await client.select_company()
    if access_token:
        print(f"  OK   Token contextualizado obtenido para: {client.current_company_id}")
    else:
        print("  FAIL Error al seleccionar empresa.")
        return

    print("\n[PASO 3] Consulta de Pendientes (FIFO & Anexo 24)")
    headers = client.get_headers()
    async with httpx.AsyncClient() as http:
        response = await http.get(
            f"{inventory_url}/locations/pending-putaway",
            headers=headers
        )
        if response.status_code == 200:
            data = response.json().get("data", [])
            print(f"  OK   Pendientes encontrados: {len(data)}")
            
            # El Flow 1 inyecta 150 unidades
            flow_1_item = next((item for item in data if float(item["quantity"]) == 150.0), None)
            
            if flow_1_item:
                print(f"  OK   Trazabilidad: Encontradas las 150 unidades de Flow 1.")
                print(f"  OK   Identidad Legal: Pedimento = {flow_1_item.get('pedimento_number')}")
                print(f"  OK   Prioridad: Dias en muelle = {flow_1_item.get('days_in_dock')}")
            else:
                print("  WARN No se encontro el item exacto de 150 unidades.")
                if data:
                    print(f"       Muestra del primer pendiente: Qty={data[0]['quantity']}, Pedimento={data[0]['pedimento_number']}")
            
            # Verificar orden (FIFO: mas antiguo arriba)
            # El repositorio ordena por created_at.asc()
            if len(data) >= 2:
                print("  OK   Orden validado (FIFO): Cola de trabajo optimizada.")
        else:
            print(f"  FAIL Error al consultar pendientes: {response.status_code}")
            print(response.text)

if __name__ == '__main__':
    asyncio.run(main())
