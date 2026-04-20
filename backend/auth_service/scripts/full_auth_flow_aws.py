import requests
import json
import jwt
import argparse

# Configuraciones Base
LOCAL_URL = "http://localhost:8001/api/v1/auth"
AWS_URL = "https://s3mukfdmmx.us-east-2.awsapprunner.com/api/v1/auth"
CREDENTIALS = {"email": "charly@interno.com", "password": "charly123"}

def run_full_flow(target_env="local"):
    base_url = AWS_URL if target_env == "aws" else LOCAL_URL
    print(f"\n[START] INICIANDO SMOKE TEST ({target_env.upper()})")
    print("="*70)
    print(f"Target: {base_url}")

    # --- PASO 1: LOGIN ---
    print(f"\nPASO 1: Intentando Login en {target_env.upper()}...")
    try:
        r_login = requests.post(f"{base_url}/login", json=CREDENTIALS, timeout=10)
        r_login.raise_for_status()
        login_data = r_login.json()["data"]
        
        sel_token = login_data["selection_token"]
        # Buscamos una empresa válida en el retorno
        target_company = next((c for c in login_data["companies"] if "Tijuana" in c["company_name"]), login_data["companies"][0])
        
        print(f"[OK] Login exitoso en {target_env.upper()}. Selection Token recibido.")
    except Exception as e:
        print(f"[ERROR] Falló el Login en {target_env.upper()}: {e}")
        if hasattr(e, 'response') and e.response is not None:
             print(f"Response: {e.response.text}")
        return

    # --- PASO 2: SELECCION DE EMPRESA ---
    print(f"\nPASO 2: Seleccionando empresa ({target_company['company_name']})...")
    
    headers = {
        "Authorization": f"Bearer {sel_token}",
        "X-Selection-Token": sel_token
    }
    payload = {"company_id": target_company["company_id"]}

    try:
        r_select = requests.post(f"{base_url}/select-company", json=payload, headers=headers, timeout=10)
        r_select.raise_for_status()
        final_resp = r_select.json()
        
        data = final_resp["data"]
        access_token = data["access_token"]
        
        # --- PASO 3: DECODIFICACION ---
        print("\nPASO 3: Decodificando Final JWT (Handshake E2E)...")
        decoded = jwt.decode(access_token, options={"verify_signature": False})

        print("\n" + "="*40)
        print(f"🚀 REGISTRO DE ÉXITO ({target_env.upper()}):")
        print("="*40)
        print(f"   Status:   ACTIVO")
        print(f"   Company:  {target_company['company_name']}")
        print(f"   Scopes:   {decoded.get('scopes', [])}")
        print(f"   Endpoint: {target_env.upper()}")
        print("="*40)

    except Exception as e:
        print(f"[ERROR] Falló la Selección de Empresa en {target_env.upper()}: {e}")
        if hasattr(e, 'response') and e.response is not None:
             print(f"Response: {e.response.text}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="InternoCore Auth Smoke Test")
    parser.add_argument("--env", choices=["local", "aws"], default="local", help="Entorno a probar (local o aws)")
    args = parser.parse_args()
    
    # Si corre sin argumentos, pregunta de forma interactiva
    import sys
    if len(sys.argv) == 1:
        eleccion = input("¿Dónde quieres ejecutar la prueba de flujo E2E? (local/aws) [default: local]: ").strip().lower()
        if eleccion in ['aws', 'local']:
            args.env = eleccion
            
    run_full_flow(args.env)
