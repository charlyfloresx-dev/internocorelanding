import requests
import json
import jwt

BASE_URL = "http://localhost:8000/api/v1/auth"
CREDENTIALS = {"email": "charly@interno.com", "password": "charly123"}

def run_full_flow():
    print("\n[START] INICIANDO FLUJO DE AUTENTICACION COMPLETO (AUDITORIA DE ROLES)")
    print("="*70)

    # --- PASO 1: LOGIN ---
    print("PASO 1: Login...")
    try:
        r_login = requests.post(f"{BASE_URL}/login", json=CREDENTIALS)
        r_login.raise_for_status()
        login_data = r_login.json()["data"]
        
        sel_token = login_data["selection_token"]
        target_company = next((c for c in login_data["companies"] if "Tijuana" in c["company_name"]), login_data["companies"][0])
        
        print(f"OK: Login exitoso. Selection Token listo.")
        print("\n[JSON DE LOGIN COMPLETO]:")
        print(json.dumps(r_login.json(), indent=4, ensure_ascii=False))
    except Exception as e:
        print(f"ERR: Error en Paso 1: {e}")
        return

    # --- PASO 2: SELECCION DE EMPRESA ---
    print(f"\nPASO 2: Seleccionando empresa: {target_company['company_name']} (ID: {target_company['company_id']})...")
    
    headers = {
        "Authorization": f"Bearer {sel_token}",
        "X-Selection-Token": sel_token
    }
    payload = {"company_id": target_company["company_id"]} # Usa el ID dinamico del login

    try:
        r_select = requests.post(f"{BASE_URL}/select-company", json=payload, headers=headers)
        r_select.raise_for_status()
        final_resp = r_select.json()
        
        data = final_resp["data"]
        access_token = data["access_token"]
        
        # --- PASO 3: DECODIFICACION Y CONTRASTE ---
        print("\nPASO 3: Verificacion de Claims y Scopes (JWT vs JSON)...")
        decoded = jwt.decode(access_token, options={"verify_signature": False})

        print("\nREPORTE DE PERMISOS POR EMPRESA:")
        print("="*40)
        print(f"Empresa ID: {data['company_id']}")
        print("-" * 40)
        
        # Datos del JSON Plano (Lo que ve el Frontend directo)
        print("DATOS EN JSON PLANO (Response Body):")
        print(f"   - Roles:  {data.get('roles', 'No enviado')}")
        print(f"   - Scopes: {data.get('scopes', 'No enviado')}")
        print("-" * 40)
        
        # Datos del JWT (La Verdad Firmada)
        print("DATOS DENTRO DEL JWT (Cifrado):")
        print(f"   - Role Names: {decoded.get('role_names', 'No encontrado')}")
        print(f"   - Scopes:     {decoded.get('scopes', 'No encontrado')}")
        print(f"   - Group ID:   {decoded.get('group_id', 'No encontrado')}")
        print("="*40)

        # Imprimimos el JSON completo
        print("\n[JSON DE RESPUESTA COMPLETO]:")
        print(json.dumps(final_resp, indent=4, ensure_ascii=False))

    except Exception as e:
        print(f"ERR: Error en validacion: {e}")
        if 'r_select' in locals(): print(r_select.text)

if __name__ == "__main__":
    # Prueba: Flujo Administrativo (Email + Password)
    # Este script simula el login de un administrador que maneja múltiples empresas.
    run_full_flow()
