import uuid
import stripe
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import base64
import urllib.parse
from app.core.database import get_db
from app.core.config import settings
from app.models.event_photo import EventPhoto, PhotoStatus
from app.models.payment_order import PaymentOrder, PaymentMethod, PaymentStatus
from app.schemas.payment import CreatePaymentIn, PaymentOrderOut, ConfirmCashPaymentIn

# Setup Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

router = APIRouter()

def generate_qr_b64(text: str) -> str:
    """Helper to generate a base64 inline QR Code (requires qrcode package later if needed)."""
    # For MVP, we pass a URL to an external generator or return the raw token for client to generate
    # In production, use `qrcode` library to generate locally.
    url_encoded = urllib.parse.quote(text)
    return f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={url_encoded}"

@router.post("/checkout")
async def create_checkout(payload: CreatePaymentIn, db: AsyncSession = Depends(get_db)):
    """
    Guest selects photos to print and pays as a batch.
    Creates a PaymentOrder per photo, but a single Stripe Intent.
    """
    valid_photos = []
    for pid in payload.photo_ids:
        photo = await db.get(EventPhoto, pid)
        if photo and photo.status == PhotoStatus.APPROVED:
            valid_photos.append(photo)
            
    if not valid_photos:
        raise HTTPException(status_code=400, detail="No hay fotos válidas para comprar.")

    total_cents = len(valid_photos) * settings.PRICE_PER_PHOTO_CENTS
    rem_cents = total_cents
    wallet_paid = 0

    if payload.use_wallet_balance:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"http://subscription-service:8000/api/v1/wallet/balance/{payload.guest_session_id}", timeout=2.0)
                if resp.status_code == 200:
                    balance = resp.json().get("balance_cents", 0)
                    wallet_paid = min(rem_cents, balance)
                    if wallet_paid > 0:
                        # Deduct it
                        await client.post("http://subscription-service:8000/api/v1/wallet/deduct", json={
                            "guest_session_id": payload.guest_session_id,
                            "amount_cents": wallet_paid,
                            "reason": "PHOTO_BATCH_PURCHASE",
                            "reference_id": f"BATCH-{uuid.uuid4().hex[:8]}"
                        })
                        rem_cents -= wallet_paid
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"No se pudo usar monedero: {e}")

    intent = None
    cash_token = None

    if rem_cents > 0:
        if payload.method == PaymentMethod.STRIPE:
            # ONLY ONE INTENT for the bundle!
            intent = stripe.PaymentIntent.create(
                amount=rem_cents,
                currency=settings.STRIPE_CURRENCY,
                metadata={"guest_session_id": payload.guest_session_id, "amount_photos": len(valid_photos)}
            )
        elif payload.method == PaymentMethod.CASH:
            cash_token = f"CASH-{uuid.uuid4().hex[:8]}"

    orders_out = []
    # Create DB Orders
    for p in valid_photos:
        order = PaymentOrder(
            id=uuid.uuid4(),
            photo_id=p.id,
            company_id=payload.company_id,
            event_id=payload.event_id,
            guest_session_id=payload.guest_session_id,
            amount_cents=settings.PRICE_PER_PHOTO_CENTS,
            currency=settings.STRIPE_CURRENCY,
            method=payload.method,
            status=PaymentStatus.PENDING if rem_cents > 0 else PaymentStatus.COMPLETED
        )
        if intent:
            order.stripe_payment_intent_id = intent.id
        if cash_token:
            order.cash_qr_token = cash_token

        if order.status == PaymentStatus.COMPLETED:
            p.status = PhotoStatus.PURCHASED
            db.add(p)

        db.add(order)
        orders_out.append({"photo_id": str(p.id), "order_id": str(order.id)})

    await db.commit()

    return {
        "orders": orders_out,
        "total_cents": total_cents,
        "wallet_deducted": wallet_paid,
        "amount_due": rem_cents,
        "stripe_client_secret": intent.client_secret if intent else None,
        "cash_qr_token": cash_token,
        "qr_image_url": generate_qr_b64(cash_token) if cash_token else None,
        "status": "COMPLETED" if rem_cents == 0 else "REQUIRES_PAYMENT"
    }


@router.post("/cash/confirm")
async def confirm_cash_payment(payload: ConfirmCashPaymentIn, db: AsyncSession = Depends(get_db)):
    """
    Staff scans the QR code from the guest's phone.
    The QR code contains the `cash_qr_token`.
    This endpoint marks the order as COMPLETED and sets the photo to PURCHASED.
    """
    result = await db.execute(
        select(PaymentOrder).where(PaymentOrder.cash_qr_token == payload.cash_qr_token)
    )
    order = result.scalars().first()
    
    if not order:
        raise HTTPException(status_code=404, detail="QR Token no válido o expirado.")
        
    if order.status == PaymentStatus.COMPLETED:
        return {"status": "already_paid", "message": "Esta impresión ya fue pagada."}

    # Update Order
    order.status = PaymentStatus.COMPLETED
    
    # Update Photo to PURCHASED so the Print Worker picks it up
    photo = await db.get(EventPhoto, order.photo_id)
    if photo:
        photo.status = PhotoStatus.PURCHASED
        
        # Gamification: Reward the original photographer if someone else buys it
        if photo.guest_session_id and photo.guest_session_id != order.guest_session_id:
            try:
                import httpx
                async with httpx.AsyncClient() as client:
                    # Async post to the local subscription-service ledger
                    await client.post("http://subscription-service:8000/api/v1/wallet/award", json={
                        "guest_session_id": photo.guest_session_id,
                        "amount_cents": int(settings.PRICE_PER_PHOTO_CENTS * 0.10), # 10% = 10 a 1 Reward
                        "reason": "PHOTO_SOLD",
                        "reference_id": str(photo.id)
                    }, timeout=2.0)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Gamification Wallet Error: {e}")

    await db.commit()
    return {"status": "ok", "message": "Pago en efectivo confirmado. Impresión en progreso."}

import fastapi

@router.post("/webhook")
async def stripe_webhook(request: fastapi.Request, db: AsyncSession = Depends(get_db)):
    """Stripe webhook to listen for payment_intent.succeeded."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    if not sig_header or not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=400, detail="Missing signature or webhook secret")
        
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Stripe Webhook Signature Error: {e}")
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")

    if event["type"] == "payment_intent.succeeded":
        intent = event["data"]["object"]
        order_id = intent.get("metadata", {}).get("order_id")
        
        if order_id:
            # 1. Marcar orden como PAID
            result = await db.execute(select(PaymentOrder).where(PaymentOrder.id == order_id))
            order = result.scalar_one_or_none()
            if order and order.status != PaymentStatus.COMPLETED:
                order.status = PaymentStatus.COMPLETED
                
                # Update Photo to PURCHASED
                photo = await db.get(EventPhoto, order.photo_id)
                if photo:
                    photo.status = PhotoStatus.PURCHASED
                    
                    # 2. Paparazzi Reward 10 a 1
                    if photo.guest_session_id and photo.guest_session_id != order.guest_session_id:
                        try:
                            import httpx
                            async with httpx.AsyncClient() as client:
                                await client.post("http://subscription-service:8000/api/v1/wallet/award", json={
                                    "guest_session_id": photo.guest_session_id,
                                    "amount_cents": int(settings.PRICE_PER_PHOTO_CENTS * 0.10),
                                    "reason": "PHOTO_SOLD_STRIPE",
                                    "reference_id": str(photo.id)
                                }, timeout=2.0)
                        except Exception as e:
                            import logging
                            logging.getLogger(__name__).warning(f"Gamification Wallet Error (Stripe): {e}")

                db.add(order)
                if photo: db.add(photo)
                await db.commit()

    return {"status": "success"}
