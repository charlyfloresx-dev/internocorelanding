import asyncio
import logging
import os
import boto3
from io import BytesIO
from PIL import Image
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.event_photo import EventPhoto, PhotoStatus
from app.core.config import settings

logger = logging.getLogger(__name__)

try:
    import cups
    HAS_CUPS = True
except ImportError:
    HAS_CUPS = False
    logger.warning("pycups is not installed or failed to load. Printer integration will run in Mock Mode.")

def get_s3_client():
    return boto3.client(
        's3',
        endpoint_url=settings.MINIO_URL,
        aws_access_key_id=settings.MINIO_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_SECRET_KEY
    )

def crop_and_watermark(photo_bytes: bytes, watermark_bytes: bytes = None) -> bytes:
    """Crops the image to 3:2 aspect ratio and superimposes a watermark."""
    img = Image.open(BytesIO(photo_bytes)).convert("RGBA")
    
    # 1. Aspect Ratio Crop to 3:2 (4x6 photo standard)
    width, height = img.size
    target_aspect = 3.0 / 2.0
    aspect = width / height
    
    if aspect > target_aspect:
        new_w = int(height * target_aspect)
        left = (width - new_w) / 2
        img = img.crop((left, 0, left + new_w, height))
    elif aspect < target_aspect:
        new_h = int(width / target_aspect)
        top = (height - new_h) / 2
        img = img.crop((0, top, width, top + new_h))
        
    width, height = img.size

    # 2. Apply Watermark
    if watermark_bytes:
        try:
            wm = Image.open(BytesIO(watermark_bytes)).convert("RGBA")
            # Scale to 20% of the image's width
            wm_w, wm_h = wm.size
            scale = (width * 0.20) / float(wm_w)
            new_wm_size = (int(wm_w * scale), int(wm_h * scale))
            wm = wm.resize(new_wm_size, Image.Resampling.LANCZOS)
            
            # Position at Bottom Right corner with a 5% margin
            pos_x = width - new_wm_size[0] - int(width * 0.05)
            pos_y = height - new_wm_size[1] - int(height * 0.05)
            
            # Use alpha composite directly on the original image coordinate frame
            img.alpha_composite(wm, (pos_x, pos_y))
        except Exception as e:
            logger.error(f"Failed to apply watermark mask: {e}")

    img = img.convert("RGB")
    out = BytesIO()
    img.save(out, format="JPEG", quality=95)
    return out.getvalue()


async def check_purchased_and_print():
    """
    Monitors database for photos with PURCHASED status.
    Downloads them, crops to 4x6, applies watermark, and routes to CUPS.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(EventPhoto).where(EventPhoto.status == PhotoStatus.PURCHASED)
        )
        photos = result.scalars().all()
        
        if not photos:
            return

        s3 = get_s3_client()
        bucket = settings.MINIO_BUCKET_NAME

        for photo in photos:
            # Atomic state transition
            photo.status = PhotoStatus.PRINTING
            db.add(photo)
            await db.commit()

            try:
                logger.info(f"[JOB] Start Processing minio object: {photo.object_key}")
                photo_obj = s3.get_object(Bucket=bucket, Key=photo.object_key)
                img_data = photo_obj['Body'].read()

                # Dynamic Event Watermark (Assuming only 1 in local node)
                wm_data = None
                wm_resp = s3.list_objects_v2(Bucket=bucket, Prefix="watermarks/")
                if 'Contents' in wm_resp and len(wm_resp['Contents']) > 0:
                    wm_key = wm_resp['Contents'][0]['Key']
                    wm_obj = s3.get_object(Bucket=bucket, Key=wm_key)
                    wm_data = wm_obj['Body'].read()

                # Process
                final_img_data = crop_and_watermark(img_data, wm_data)
                
                # Write High-Res Asset temporarily
                tmp_dir = "/app/spool"
                os.makedirs(tmp_dir, exist_ok=True)
                pdf_path = f"{tmp_dir}/{photo.id}_4x6.pdf"
                
                # We save natively to PDF since CUPS handles PDF rendering beautifully
                img_pil = Image.open(BytesIO(final_img_data))
                img_pil.save(pdf_path, "PDF", resolution=300.0)
                
                # Dispatch Hardware Call
                if HAS_CUPS:
                    try:
                        conn = cups.Connection()
                        printers = conn.getPrinters()
                        if printers:
                            printer_name = list(printers.keys())[0] # Usually DNP/Hiti default
                            job_id = conn.printFile(printer_name, pdf_path, f"KioskPhoto_{photo.id}", {"fit-to-page": "True", "media": "4x6"})
                            logger.info(f"[CUPS] Sent ID {photo.id} to {printer_name}. Job: {job_id}")
                        else:
                            logger.warning("[CUPS] Accessible but no installed printers. PDF kept in spool.")
                    except Exception as e:
                        logger.error(f"[CUPS] Print exception: {e}")
                else:
                    logger.info(f"Mock Print: Engine built and PDF saved to {pdf_path}")

                # Terminal successful state
                photo.status = PhotoStatus.DONE
                db.add(photo)
                await db.commit()
                
            except Exception as e:
                logger.error(f"Failed to complete print pipeline for photo {photo.id}: {str(e)}")

async def print_worker_loop():
    logger.info("Initializing Print Worker Daemon...")
    while True:
        await check_purchased_and_print()
        await asyncio.sleep(5)  # Short 5 second interval loop

if __name__ == "__main__":
    asyncio.run(print_worker_loop())
