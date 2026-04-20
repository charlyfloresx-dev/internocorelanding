import qrcode
import base64
import boto3
from io import BytesIO
from app.core.config import settings

import socket

def get_lan_ip():
    """Returns the machine's LAN IP, falling back to 127.0.0.1."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def generate_qr_b64(data: str) -> str:
    """Generates a base64 encoded QR code PNG given a string data."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffered.getvalue()).decode("utf-8")

class EventOnboardingService:
    @staticmethod
    def process_watermark(event_name: str, watermark_b64: str) -> str | None:
        """Saves the base64 watermark logo to MinIO and returns the object key."""
        if not watermark_b64:
            return None
            
        s3 = boto3.client(
            's3',
            endpoint_url=settings.MINIO_URL,
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY
        )
        
        try:
            # Check if bucket exists, create if not
            try:
                s3.head_bucket(Bucket=settings.MINIO_BUCKET_NAME)
            except:
                s3.create_bucket(Bucket=settings.MINIO_BUCKET_NAME)
                
            if "base64," in watermark_b64:
                watermark_b64 = watermark_b64.split("base64,")[1]
                
            img_data = base64.b64decode(watermark_b64)
            key = f"watermarks/{event_name}_logo.png"
            
            s3.put_object(
                Bucket=settings.MINIO_BUCKET_NAME, 
                Key=key, 
                Body=img_data, 
                ContentType="image/png"
            )
            return key
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error subiendo watermark a Minio: {e}")
            return None

    @staticmethod
    def generate_event_qrs(event_name: str, base_url: str, required_approvals: int = 1):
        """Generates the essential QR codes for the event staff, guests, and dynamic approvers."""
        # If the user accessed via IP (e.g. 192.168.x.x), 
        # base_url will already be correct. Only replace if it's localhost.
        if "localhost" in base_url or "127.0.0.1" in base_url:
            lan_ip = settings.CORE_KIOSK_LAN_IP or get_lan_ip()
            base_url = base_url.replace("localhost", lan_ip).replace("127.0.0.1", lan_ip)

        guest_url = f"{base_url}/join?event={event_name}"
        staff_url = f"{base_url}/staff/scan"
        
        approver_qrs = []
        for i in range(1, required_approvals + 1):
            url = f"{base_url}/approval?event={event_name}&approver={i}"
            approver_qrs.append({
                "index": i,
                "url": url,
                "qr": generate_qr_b64(url)
            })

        return {
            "guest_qr": generate_qr_b64(guest_url),
            "staff_qr": generate_qr_b64(staff_url),
            "guest_url": guest_url,
            "staff_url": staff_url,
            "approvers": approver_qrs
        }
