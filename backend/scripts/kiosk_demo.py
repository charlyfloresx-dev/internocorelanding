import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
from PIL import Image, ImageDraw
import qrcode
import base64
import time
import os
import subprocess
import uuid
from io import BytesIO

BASE_URL = "http://localhost:8020/api/v1/kiosk"
EVENT_ID   = "10000000-0000-0000-0000-000000000001"
COMPANY_ID = "00000000-0000-0000-0000-000000000002"
GUEST_ID   = "INVITADO_JUAN_001"
LINE = "=" * 58

def banner(msg):
    print(f"\n{LINE}\n  {msg}\n{LINE}")

# ==========================================================
# 1. SETUP DEL EVENTO
# ==========================================================
def step1_setup():
    banner("PASO 1 | Configuracion del Evento")
    wm = Image.new("RGBA", (600, 200), (0, 0, 0, 0))
    d = ImageDraw.Draw(wm)
    d.text((50, 60),  "C & P",                     fill=(255, 255, 255, 220))
    d.text((50, 130), "Boda 2026 - Valle de Guadalupe", fill=(255, 215, 0, 180))
    buf = BytesIO()
    wm.save(buf, format="PNG")
    wm_b64 = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

    payload = {
        "event_name": "BodaCarlosYPaulina",
        "photo_price": 50,
        "rule_paparazzi": True,
        "watermark_b64": wm_b64,
        "frontend_base_url": "http://localhost:4200"
    }
    r = requests.post(f"{BASE_URL}/onboarding/setup", json=payload)
    r.raise_for_status()
    d = r.json()
    print(f"  [OK] Evento: {d['event_name']}")
    print(f"  [$]  Precio: ${d['config']['photo_price'] // 100} MXN por foto")
    print(f"  [*]  Watermark: {'Subido a MinIO' if d['config']['watermark_active'] else 'Sin subir'}")
    print(f"  [QR-Novios]    -> {d['qrs']['groom_bride_url']}")
    print(f"  [QR-Invitados] -> {d['qrs']['guest_url']}")
    print(f"  [QR-Staff]     -> {d['qrs']['staff_url']}")

# ==========================================================
# 2. SUBIDA DE FOTO (Invitado)
# ==========================================================
def generate_demo_photo() -> bytes:
    img = Image.new("RGB", (1800, 1200))
    d = ImageDraw.Draw(img)
    for y in range(1200):
        r = int(255 - (y/1200)*20)
        g = int(250 - (y/1200)*40)
        b = int(240 - (y/1200)*60)
        d.line([(0, y), (1800, y)], fill=(r, g, b))
    for i in range(12, 0, -1):
        c = int(255 * i / 12)
        d.ellipse([(700-i*25, 400-i*25), (1100+i*25, 800+i*25)], fill=(255, 220, 150))
    d.text((620, 470), "Carlos & Paulina",   fill=(100, 60, 20))
    d.text((660, 560), "11 . Abril . 2026",  fill=(140, 100, 40))
    d.text((680, 640), "Valle de Guadalupe", fill=(160, 120, 60))
    d.rectangle([(80, 80), (1720, 1120)], outline=(200, 180, 140), width=15)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=92)
    return buf.getvalue()

def step2_upload() -> str:
    banner("PASO 2 | Invitado sube foto")
    filename = f"demo_{uuid.uuid4().hex[:6]}.jpg"
    req = {
        "event_id": EVENT_ID,
        "company_id": COMPANY_ID,
        "guest_session_id": GUEST_ID,
        "guest_name": "Juan Invitado",
        "filename": filename,
        "content_type": "image/jpeg",
        "file_size_bytes": 400000
    }
    r = requests.post(f"{BASE_URL}/photos/upload-url", json=req)
    r.raise_for_status()
    data = r.json()
    photo_id = data["photo_id"]
    upload_url = data["upload_url"]
    print(f"  [ID] Photo ID: {photo_id}")
    
    # La presigned URL usa el hostname interno de Docker ("minio").
    # Desde Windows, la reemplazamos por localhost:9000 para poder subir directo.
    upload_url = upload_url.replace("http://minio:9000", "http://localhost:9000")
    
    img_bytes = generate_demo_photo()
    up = requests.put(upload_url, data=img_bytes, headers={"Content-Type": "image/jpeg"})
    if up.status_code in (200, 204):
        print(f"  [OK] Foto generada y subida a MinIO ({len(img_bytes)//1024} KB)")
    else:
        print(f"  [!!] MinIO status {up.status_code} - continuando")
    return photo_id

# ==========================================================
# 3. APROBACION DUAL
# ==========================================================
def step3_approve(photo_id: str) -> str:
    banner("PASO 3 | Aprobacion Dual de los Novios")
    r = requests.post(f"{BASE_URL}/photos/{photo_id}/review",
                      json={"action": "APPROVE", "reviewer": "GROOM"})
    r.raise_for_status()
    state = r.json()["photo_state"]
    print(f"  [OK] Carlos (GROOM) aprueba -> Estado: {state}")

    time.sleep(0.5)
    r = requests.post(f"{BASE_URL}/photos/{photo_id}/review",
                      json={"action": "APPROVE", "reviewer": "BRIDE"})
    r.raise_for_status()
    state = r.json()["photo_state"]
    print(f"  [OK] Paulina (BRIDE) aprueba -> Estado: {state}")
    
    if state == "APPROVED":
        print(f"\n  *** MATCH! Ambos novios aprobaron ***")
        print(f"      [En la PWA: confetti + foto visible en galeria publica]")
    return state

# ==========================================================
# 4. CHECKOUT / PAGO EN EFECTIVO
# ==========================================================
def step4_checkout(photo_id: str) -> dict:
    banner("PASO 4 | Checkout del Invitado (Efectivo)")
    payload = {
        "photo_ids": [photo_id],
        "company_id": COMPANY_ID,
        "event_id": EVENT_ID,
        "guest_session_id": GUEST_ID,
        "method": "CASH",
        "use_wallet_balance": False
    }
    r = requests.post(f"{BASE_URL}/payments/checkout", json=payload)
    r.raise_for_status()
    data = r.json()
    print(f"  [$]  Total: ${data['total_cents']/100:.2f} MXN")
    print(f"  [M]  Metodo: EFECTIVO")
    print(f"  [QR] Token: {data.get('cash_qr_token')}")
    print(f"  Estado de la orden: {data.get('status')}")
    return data

# ==========================================================
# 5. CONFIRMACION DE PAGO (Staff)
# ==========================================================
def step5_confirm(cash_token: str):
    banner("PASO 5 | Staff Confirma Pago en Efectivo")
    r = requests.post(f"{BASE_URL}/payments/cash/confirm",
                      json={"cash_qr_token": cash_token})
    r.raise_for_status()
    d = r.json()
    print(f"  [OK] {d['message']}")
    print(f"  [->] Foto marcada como PURCHASED")
    print(f"  [*]  Print Worker detectara en proximo ciclo (5s)")

# ==========================================================
# 6. ESPERAR PDF DEL PRINT WORKER
# ==========================================================
def step6_print(photo_id: str):
    banner("PASO 6 | Esperando al Print Worker (PDF)")
    print("  [...] scanning /app/spool/ cada 5s (max 45s)...")
    for i in range(9):
        time.sleep(5)
        chk = subprocess.run(
            ["docker", "exec", "kiosk-image-service",
             "ls", f"/app/spool/{photo_id}_4x6.pdf"],
            capture_output=True, text=True
        )
        if chk.returncode == 0:
            print(f"\n  [OK] PDF listo: /app/spool/{photo_id}_4x6.pdf")
            out = os.path.join(os.path.dirname(__file__), f"{photo_id}_4x6.pdf")
            subprocess.run(["docker", "cp",
                f"kiosk-image-service:/app/spool/{photo_id}_4x6.pdf", out],
                capture_output=True)
            if os.path.exists(out):
                print(f"  [->] PDF copiado a: {out}")
                os.startfile(out)
            return True
        print(f"     Ciclo {i+1}/9 — sin PDF aun...")
    print("\n  [!!] Tiempo de espera agotado. Revisando logs...")
    logs = subprocess.run(["docker", "logs", "kiosk-image-service", "--tail", "15"],
                           capture_output=True, text=True)
    print(logs.stdout[-1000:] if logs.stdout else logs.stderr[-600:])
    return False

# ==========================================================
# MAIN
# ==========================================================
def main():
    print(f"\n{LINE}")
    print("  BODA CARLOS & PAULINA — Kiosko Demo End-to-End")
    print(f"  Backend: {BASE_URL}")
    print(f"{LINE}\n")
    
    try:
        step1_setup()
        photo_id = step2_upload()
        state = step3_approve(photo_id)
        if state != "APPROVED":
            print("[ERR] Foto no aprobada. Abortando.")
            return
        checkout = step4_checkout(photo_id)
        cash_token = checkout.get("cash_qr_token")
        if not cash_token:
            print("[ERR] No se genero token de efectivo.")
            return
        step5_confirm(cash_token)
        step6_print(photo_id)
    except requests.exceptions.HTTPError as e:
        print(f"\n[ERR] HTTP {e.response.status_code}: {e.response.text}")
    except Exception as e:
        import traceback; traceback.print_exc()

    print(f"\n{LINE}")
    print("  FIN DEL DEMO")
    print(LINE)

if __name__ == "__main__":
    main()
