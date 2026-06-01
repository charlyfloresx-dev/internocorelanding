"""
Full Auth Flow — Phase 162 RTR Phase D
Tests:
  1. Login (T1 handshake) → selection_token
  2. Select Company (T2 handshake) → access_token + RTR refresh_token (gen 0)
  3. Decode & verify JWT claims
  4. RTR Refresh → rotate gen 0 → gen 1, verify new tokens
"""
import requests
import json
import jwt

BASE_URL = "http://localhost:8001/api/v1/auth"
CREDENTIALS = {"email": "charly@interno.com", "password": "charly123"}

def run_full_flow():
    print("\n[START] FLUJO DE AUTENTICACION COMPLETO CON RTR (Phase D)")
    print("="*70)

    # --- PASO 1: LOGIN ---
    print("PASO 1: Login (T1)...")
    try:
        r_login = requests.post(f"{BASE_URL}/login", json=CREDENTIALS)
        r_login.raise_for_status()
        login_data = r_login.json()["data"]

        sel_token = login_data["selection_token"]
        target_company = next((c for c in login_data["companies"] if "Tijuana" in c["company_name"]), login_data["companies"][0])

        print(f"  OK: Login exitoso. Selection Token listo.")
        print(f"  Empresa objetivo: {target_company['company_name']}")
    except Exception as e:
        print(f"  ERR: {e}")
        return

    # --- PASO 2: SELECT COMPANY (T2) ---
    print(f"\nPASO 2: Select Company (T2) — empresa: {target_company['company_name']}...")

    headers = {
        "Authorization": f"Bearer {sel_token}",
        "X-Selection-Token": sel_token
    }
    payload = {"company_id": target_company["company_id"]}

    try:
        r_select = requests.post(f"{BASE_URL}/select-company", json=payload, headers=headers)
        r_select.raise_for_status()
        final_resp = r_select.json()

        data = final_resp["data"]
        access_token = data["access_token"]
        refresh_token = data.get("refresh_token")

        print(f"  OK: access_token obtenido")
        print(f"  RTR refresh_token: {'presente' if refresh_token else 'AUSENTE (Error)'}")

        if refresh_token:
            rt_payload = jwt.decode(refresh_token, options={"verify_signature": False})
            print(f"  RTR gen:    {rt_payload.get('gen')} (debe ser 0)")
            print(f"  RTR typ:    {rt_payload.get('typ')} (debe ser 'refresh')")
            print(f"  RTR fam:    {rt_payload.get('fam')[:8]}... (family_id)")

    except Exception as e:
        print(f"  ERR: {e}")
        if 'r_select' in locals(): print(r_select.text)
        return

    # --- PASO 3: DECODIFICACION ACCESS TOKEN ---
    print(f"\nPASO 3: Verificacion de Claims del Access Token...")
    decoded = jwt.decode(access_token, options={"verify_signature": False})
    print(f"  Empresa ID:  {data['company_id']}")
    print(f"  Roles:       {data.get('roles')}")
    print(f"  Scopes:      {data.get('scopes')}")
    print(f"  JWT scopes:  {decoded.get('scopes')}")
    print(f"  Group ID:    {decoded.get('group_id')}")

    # --- PASO 4: RTR REFRESH ---
    if not refresh_token:
        print(f"\nPASO 4: SKIPPED — no hay refresh_token (Phase D pendiente o error)")
        return

    print(f"\nPASO 4: RTR Refresh — rotar gen 0 → gen 1...")
    try:
        r_refresh = requests.post(
            f"{BASE_URL}/refresh",
            json={"refresh_token": refresh_token},
            headers={"X-Company-ID": data["company_id"]},
        )
        r_refresh.raise_for_status()
        refresh_resp = r_refresh.json()
        new_access = refresh_resp["data"]["access_token"]
        new_refresh = refresh_resp["data"]["refresh_token"]

        new_rt_payload = jwt.decode(new_refresh, options={"verify_signature": False})
        print(f"  OK: Tokens rotados exitosamente")
        print(f"  Nueva gen:  {new_rt_payload.get('gen')} (debe ser 1)")
        print(f"  Mismo fam:  {new_rt_payload.get('fam')[:8]}... (debe coincidir)")

        old_fam = jwt.decode(refresh_token, options={"verify_signature": False}).get('fam')
        assert new_rt_payload.get('fam') == old_fam, "FAMILY_ID_MISMATCH: familia cambió!"
        assert new_rt_payload.get('gen') == 1, f"GEN_MISMATCH: esperado 1, got {new_rt_payload.get('gen')}"
        print(f"  ASSERTIONS: OK — mismo family_id, gen incrementó a 1")

    except Exception as e:
        print(f"  ERR: {e}")
        if 'r_refresh' in locals(): print(r_refresh.text)

    print(f"\n[DONE] Flujo E2E Login → Select → RTR Refresh completado")

if __name__ == "__main__":
    run_full_flow()
