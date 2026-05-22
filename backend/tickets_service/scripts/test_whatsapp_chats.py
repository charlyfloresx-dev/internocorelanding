"""
Flow de prueba: Descubrir JIDs de grupos WhatsApp y registrar WhatsAppGroupMapping.

Valida el stack completo:
  Login -> select-company -> JWT -> session/initialize -> session/chats -> mappings

Uso:
    python tickets_service/scripts/test_whatsapp_chats.py
    python tickets_service/scripts/test_whatsapp_chats.py --register TECNICOS_PLANTA "120363xxxxxxxx@g.us"
"""

import sys
import time
import argparse
import requests

BASE_AUTH    = "http://localhost:8001/api/v1/auth"
BASE_NOTIFY  = "http://localhost:8009/api/v1/whatsapp"
BASE_GATEWAY = "http://localhost:3011/api/v1/whatsapp"
GATEWAY_KEY  = "DEV_INTERNAL_KEY_123"

EMAIL    = "charly@interno.com"
PASSWORD = "charly123"


def step(label: str):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print('='*60)


def get_jwt():
    step("PASO 1 - Login")
    r = requests.post(f"{BASE_AUTH}/login", json={"email": EMAIL, "password": PASSWORD}, timeout=10)
    r.raise_for_status()
    data = r.json()["data"]
    sel_token = data["selection_token"]
    company   = data["companies"][0]
    print(f"OK  Login exitoso. Empresa: {company['company_name']} ({company['company_id']})")

    step("PASO 2 - Select Company")
    r2 = requests.post(
        f"{BASE_AUTH}/select-company",
        json={"company_id": company["company_id"]},
        headers={"Authorization": f"Bearer {sel_token}", "X-Selection-Token": sel_token},
        timeout=10,
    )
    r2.raise_for_status()
    access_token = r2.json()["data"]["access_token"]
    company_id   = r2.json()["data"]["company_id"]
    print(f"OK  JWT obtenido. company_id={company_id}")
    return access_token, company_id


def ensure_connected(token: str, company_id: str) -> bool:
    step("PASO 3 - Verificar / Inicializar sesión WhatsApp")

    r = requests.get(
        f"{BASE_NOTIFY}/session/status",
        headers={"Authorization": f"Bearer {token}"},
        timeout=8,
    )
    status = r.json()["data"]["status"]
    print(f"Estado actual: {status}")

    if status == "CONNECTED":
        print("OK  Ya está CONNECTED.")
        return True

    if status in ("NOT_INITIALIZED", "DISCONNECTED", "FAILED"):
        print("Inicializando sesión (puede tardar 20-40s con LocalAuth guardado)...")
        r2 = requests.post(
            f"{BASE_NOTIFY}/session/initialize",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=15,
        )
        print(f"  Initialize -> HTTP {r2.status_code}")

    # Poll hasta CONNECTED (máx 60s)
    for i in range(30):
        time.sleep(2)
        r3 = requests.get(
            f"{BASE_GATEWAY}/session/{company_id}/status",
            headers={"Authorization": f"Bearer {GATEWAY_KEY}"},
            timeout=5,
        )
        s = r3.json().get("status")
        print(f"  [{i*2:>3}s] Gateway status: {s}")
        if s == "CONNECTED":
            print("OK  Sesión CONNECTED.")
            return True
        if s in ("QR_READY",):
            print("\nAVISO: Se generó un QR nuevo. Escanéalo desde el drawer WhatsApp en Angular.")
            print("       Luego vuelve a correr este script.")
            return False

    print("TIMEOUT: La sesión no se conectó en 60s.")
    return False


def list_group_chats(token: str, company_id: str):
    step("PASO 4 - Listar grupos de WhatsApp (vía notification_service)")

    # Via notification_service (Iron Wall ADR-02)
    r = requests.get(
        f"{BASE_NOTIFY}/session/chats",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    if r.status_code != 200:
        print(f"ERROR HTTP {r.status_code}: {r.text}")
        return []

    data = r.json()["data"]
    chats = data.get("chats", [])

    if not chats:
        print("No se encontraron grupos. Asegúrate de que el número esté en al menos un grupo de WhatsApp.")
        return []

    print(f"Se encontraron {len(chats)} grupo(s):\n")
    print(f"  {'JID':<35} {'Participantes':<14} Nombre")
    print("  " + "-"*70)
    for c in sorted(chats, key=lambda x: x.get("name", "")):
        jid   = c.get("id", "")
        name  = c.get("name", "")
        count = c.get("participantCount")
        count_str = str(count) if count is not None else "?"
        print(f"  {jid:<35} {count_str:<14} {name}")

    return chats


def list_existing_mappings(token: str):
    step("PASO 5 - Mappings registrados en DB")
    r = requests.get(
        f"{BASE_NOTIFY}/mappings",
        headers={"Authorization": f"Bearer {token}"},
        timeout=8,
    )
    mappings = r.json().get("data", [])
    if not mappings:
        print("  (ninguno registrado aún)")
    else:
        print(f"  {'group_name':<25} {'display_name':<25} whatsapp_group_id")
        print("  " + "-"*80)
        for m in mappings:
            print(f"  {m['group_name']:<25} {(m.get('display_name') or ''):<25} {m['whatsapp_group_id']}")
    return mappings


def register_mapping(token: str, group_name: str, jid: str, display_name: str = None):
    step(f"PASO 6 - Registrar mapping: {group_name} -> {jid}")
    payload = {
        "group_name": group_name.upper(),
        "whatsapp_group_id": jid,
    }
    if display_name:
        payload["display_name"] = display_name

    r = requests.post(
        f"{BASE_NOTIFY}/mappings",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=payload,
        timeout=10,
    )
    if r.status_code in (200, 201):
        print(f"OK  Mapping registrado:")
        import json
        print(json.dumps(r.json()["data"], indent=2, ensure_ascii=False))
    else:
        print(f"ERROR HTTP {r.status_code}: {r.text}")


def main():
    parser = argparse.ArgumentParser(description="Descubrir JIDs de grupos WhatsApp y registrar mappings")
    parser.add_argument("--register", nargs=2, metavar=("GROUP_NAME", "JID"),
                        help="Registra un mapping: --register TECNICOS_PLANTA '120363xxx@g.us'")
    parser.add_argument("--display-name", default=None, help="Nombre legible para el mapping")
    parser.add_argument("--skip-connect", action="store_true", help="Saltar verificación de sesión (asume CONNECTED)")
    args = parser.parse_args()

    print("\nINTERNOCORE - WHATSAPP GROUP JID DISCOVERY")
    print("Stack: notification_service:8009 -> gateway:3011 -> WhatsApp\n")

    try:
        token, company_id = get_jwt()

        if not args.skip_connect:
            connected = ensure_connected(token, company_id)
            if not connected:
                sys.exit(1)

        if args.register:
            group_name, jid = args.register
            register_mapping(token, group_name, jid, args.display_name)
            list_existing_mappings(token)
        else:
            chats = list_group_chats(token, company_id)
            list_existing_mappings(token)
            if chats:
                print("\nPARA REGISTRAR UN GRUPO:")
                print("  python tickets_service/scripts/test_whatsapp_chats.py --register TECNICOS_PLANTA '<JID>'")

    except requests.exceptions.ConnectionError as e:
        print(f"\nERROR de conexión: {e}")
        print("Verifica que el stack esté corriendo: docker compose up -d")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrumpido.")


if __name__ == "__main__":
    main()
