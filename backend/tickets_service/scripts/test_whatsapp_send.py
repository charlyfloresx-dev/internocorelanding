"""
Flow de prueba: Envío de mensaje WhatsApp via InternoCore Notification Service.

Valida el stack completo:
  Login -> select-company -> JWT -> /whatsapp/session/status -> /whatsapp/test-send -> gateway logs

Uso:
    python tickets_service/scripts/test_whatsapp_send.py
    python tickets_service/scripts/test_whatsapp_send.py --to +526641667684 --msg "Hola desde InternoCore"
"""

import sys
import argparse
import requests
import subprocess

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


def check_session(token: str, company_id: str) -> str:
    step("PASO 3 - Estado de sesión WhatsApp")

    # Via notification_service (proxy seguro con JWT)
    r = requests.get(
        f"{BASE_NOTIFY}/session/status",
        headers={"Authorization": f"Bearer {token}"},
        timeout=8,
    )
    status = r.json()["data"]["status"]
    print(f"notification_service -> status: {status}")

    # Verificación directa en gateway Node.js
    r2 = requests.get(
        f"{BASE_GATEWAY}/session/{company_id}/status",
        headers={"Authorization": f"Bearer {GATEWAY_KEY}"},
        timeout=8,
    )
    gw_status = r2.json().get("status")
    print(f"gateway (directo)    -> status: {gw_status}")

    if gw_status != "CONNECTED":
        print("\nERROR: La sesión no está CONNECTED.")
        print("  1. Abre http://localhost:4200/admin/whatsapp")
        print("  2. Haz clic en 'Iniciar y generar QR'")
        print("  3. Escanea el QR con WhatsApp -> espera CONNECTED")
        sys.exit(1)

    print("\nOK  Sesión CONNECTED - lista para enviar.")
    return gw_status


def send_message(token: str, to: str, message: str):
    step(f"PASO 4 - Enviar mensaje a {to}")
    print(f"Mensaje: {message}")

    # Intento 1: via notification_service (stack completo JWT)
    print("\n[A] Via notification_service (puerto 8009)...")
    r = requests.post(
        f"{BASE_NOTIFY}/test-send",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"to": to, "message": message},
        timeout=15,
    )
    print(f"    HTTP {r.status_code} -> {r.text}")

    if r.status_code == 200 and r.json().get("data", {}).get("status") == "success":
        print("\nOK  Mensaje encolado exitosamente via notification_service.")
        return True

    # Intento 2: directo al gateway (debug)
    print("\n[B] Via gateway directo (puerto 3011)...")
    company_id = _get_company_from_token(token)
    r2 = requests.post(
        f"{BASE_GATEWAY}/send",
        headers={"Authorization": f"Bearer {GATEWAY_KEY}", "Content-Type": "application/json"},
        json={"company_id": company_id, "to": to, "message": message},
        timeout=15,
    )
    print(f"    HTTP {r2.status_code} -> {r2.text}")

    if r2.status_code == 200 and r2.json().get("status") == "success":
        print("\nOK  Mensaje encolado exitosamente via gateway directo.")
        return True

    print("\nFAIL  Ambos intentos fallaron.")
    return False


def _get_company_from_token(token: str) -> str:
    import base64, json
    payload = token.split(".")[1]
    payload += "=" * (4 - len(payload) % 4)
    return json.loads(base64.b64decode(payload))["company_id"]


def tail_gateway_logs():
    step("PASO 5 - Logs del gateway (últimas 15 líneas)")
    try:
        result = subprocess.run(
            ["docker", "logs", "interno-whatsapp-gateway-dev", "--tail", "15"],
            capture_output=True, text=True, timeout=10,
        )
        print(result.stdout or result.stderr)
    except Exception as e:
        print(f"No se pudieron obtener los logs: {e}")


def main():
    parser = argparse.ArgumentParser(description="Test WhatsApp send flow")
    parser.add_argument("--to",  default="+526641667684", help="Número destino o group JID")
    parser.add_argument("--msg", default="InternoCore WhatsApp test - canal local multitenant activo",
                        help="Mensaje a enviar")
    args = parser.parse_args()

    print("\nINTERNOCORE - WHATSAPP SEND TEST FLOW")
    print("Stack: Angular -> Nginx:8000 -> notification_service:8009 -> gateway:3011 -> WhatsApp\n")

    try:
        token, company_id = get_jwt()
        check_session(token, company_id)
        send_message(token, args.to, args.msg)
        tail_gateway_logs()
    except requests.exceptions.ConnectionError as e:
        print(f"\nERROR de conexión: {e}")
        print("Verifica que el stack esté corriendo: docker compose up -d")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrumpido.")


if __name__ == "__main__":
    main()
