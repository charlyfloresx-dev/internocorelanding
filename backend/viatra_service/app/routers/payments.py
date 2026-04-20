import uuid
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.dependencies import get_current_user, get_db
from app.services.stripe_service import StripeService
from app.services.booking_service import BookingService
from app.repositories.payment_repository import PaymentRepository
from app.models.payment_history import PaymentHistory
from app.models.group import TravelerGroup


from common.models.user_context import UserContext
from common.security.idempotency import idempotent

router = APIRouter(prefix="/api/v1/payments", tags=["Fintech & Payments"])

class CheckoutSessionRequest(BaseModel):
    group_id: uuid.UUID
    success_url: str
    cancel_url: str

@router.post("/create-checkout-session")
@idempotent()
async def create_checkout_session(
    request: Request,
    payload: CheckoutSessionRequest,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_request_id: Optional[str] = None
):
    """
    Generates a Stripe Checkout Session for a traveler joining a trip group.
    Uses the @idempotent decorator to prevent duplicate subscriptions.
    """
    booking_service = BookingService(db)
    
    # 1. Fetch the group and verify it exists within the tenant
    group = await booking_service.group_repo.get_by_id(payload.group_id, user.company_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="El grupo de viaje no existe."
        )

    # 2. Fetch the linked package to get the stripe_price_id
    package = await booking_service.package_repo.get_by_id(group.package_id, user.company_id)
    if not package or not package.stripe_price_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="El paquete vinculado no tiene una configuración de pago activa en Stripe."
        )

    # 3. Create Stripe Checkout Session
    try:
        checkout_url = await StripeService.create_checkout_session(
            price_id=package.stripe_price_id,
            success_url=payload.success_url,
            cancel_url=payload.cancel_url,
            metadata={
                "group_id": str(group.id),
                "package_id": str(package.id),
                "user_id": str(user.user_id),
                "company_id": str(user.company_id),
                "client_request_id": client_request_id
            }
        )
        return {"checkout_url": checkout_url}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error al generar sesión de Stripe: {str(e)}"
        )

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Public endpoint for Stripe Webhook events.
    Verifies signature and updates TravelerGroup status.
    """
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = StripeService.verify_webhook_signature(payload, sig_header)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    booking_service = BookingService(db)
    payment_repo = PaymentRepository(db)

    # 1. Payment Success (Initial Checkout)
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.get("metadata", {})
        
        user_id = metadata.get("user_id")
        group_id = metadata.get("group_id")
        company_id = metadata.get("company_id")

        if group_id and company_id:
            # Update Group Status (CONFIRMED)
            group = await booking_service.group_repo.get_by_id(uuid.UUID(group_id), uuid.UUID(company_id))
            if group:
                group.is_active = True # Or a specific status like "CONFIRMED"
                
                # Audit Payment
                payment = PaymentHistory(
                    id=uuid.uuid4(),
                    company_id=uuid.UUID(company_id),
                    user_id=uuid.UUID(user_id),
                    group_id=uuid.UUID(group_id),
                    stripe_session_id=session.id,
                    stripe_subscription_id=session.get("subscription"),
                    amount=Decimal(session.get("amount_total", 0)) / 100,
                    currency=session.get("currency", "usd").upper(),
                    status="PAID",
                    created_by=uuid.UUID(user_id)
                )
                await payment_repo.create(payment)
                
                # TODO: Trigger notification_service call
                print(f"INFO: Payment Webhook Success for Group {group_id}")
                
        await db.commit()

    # 2. Monthly Installment Success
    elif event["type"] == "invoice.paid":
        # Extend visibility
        invoice = event["data"]["object"]
        # Logic to find group via subscription_id ...
        pass

    # 3. Grace Period - Payment Failed (Strategy of Rescue)
    elif event["type"] == "invoice.payment_failed":
        invoice = event["data"]["object"]
        subscription_id = invoice.get("subscription")
        
        # Look up group linked to this subscription
        query = select(TravelerGroup).where(TravelerGroup.status == "PAID") # Simplified look-up
        res = await db.execute(query)
        group = res.scalar_one_or_none()
        
        if group:
            from datetime import datetime, timedelta
            group.status = "GRACE_PERIOD"
            group.grace_period_until = datetime.now() + timedelta(hours=48)
            
            # TODO: Trigger notification_service (Resend)
            # Subject: "Misión en Riesgo: Actualiza tu método de pago"
            print(f"CRITICAL: Grace Period started for Group {group.id}")
            
        await db.commit()

    return {"status": "success"}


@router.get("/history", summary="Consultar el historial de pagos del usuario actual")
async def get_payment_history(
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna el listado de transacciones exitosas / fallidas del viajero.
    Requerido por el PaymentService del frontend.
    """
    payment_repo = PaymentRepository(db)
    # Por ahora limitamos la carga a los pagos recientes,
    # TODO: Implementar un .get_user_payments_history real en el repo
    payments = await payment_repo.list_all(user.company_id)
    user_payments = [p for p in payments if p.user_id == user.user_id]
    
    return [
        {
            "id": str(p.id),
            "amount": p.amount,
            "currency": p.currency,
            "status": p.status,
            "date": p.created_at.isoformat() if p.created_at else None
        } for p in user_payments
    ]


