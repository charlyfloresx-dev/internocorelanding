from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from common.infrastructure.database import get_db
from common.config import settings
from subscription_app.models.wallet import GuestWallet, WalletTransaction

router = APIRouter()


async def verify_admin_master_key(x_admin_key: str = Header(..., alias="X-Admin-Master-Key")):
    if not settings or not settings.int_admin_master_key or x_admin_key != settings.int_admin_master_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acceso Denegado: Admin Master Key inválida o no configurada."
        )

class CreditAwardRequest(BaseModel):
    guest_session_id: str
    amount_cents: int
    reason: str
    reference_id: str = None

@router.post("/award", dependencies=[Depends(verify_admin_master_key)])
async def award_credit(req: CreditAwardRequest, db: AsyncSession = Depends(get_db)):
    # 1. Provide Wallet
    result = await db.execute(select(GuestWallet).where(GuestWallet.guest_session_id == req.guest_session_id))
    wallet = result.scalar_one_or_none()
    
    if not wallet:
        wallet = GuestWallet(guest_session_id=req.guest_session_id, balance_cents=0)
        db.add(wallet)
        await db.commit()
        await db.refresh(wallet)
        
    # 2. Add transaction
    tx = WalletTransaction(
        guest_wallet_id=wallet.id,
        amount_cents=req.amount_cents,
        transaction_type="REWARD",
        reference_id=req.reference_id,
        reason=req.reason
    )
    wallet.balance_cents += req.amount_cents
    
    db.add(tx)
    db.add(wallet)
    await db.commit()
    
    # 3. Fire Notification!
    # Llama al Notification Service
    try:
        async with httpx.AsyncClient() as client:
            await client.post("http://notification-service:8000/api/v1/notify", json={
                "guest_session_id": req.guest_session_id,
                "message": f"¡Ganaste ${req.amount_cents / 100} MXN en crédito en tu monedero!"
            }, timeout=2.0)
    except Exception as e:
        print(f"Failed to notify guest: {e}")

    return {"status": "success", "new_balance_cents": wallet.balance_cents}


class DeductCreditRequest(BaseModel):
    guest_session_id: str
    amount_cents: int
    reason: str
    reference_id: str = None

@router.get("/balance/{guest_session_id}")
async def get_balance(guest_session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(GuestWallet).where(GuestWallet.guest_session_id == guest_session_id))
    wallet = result.scalar_one_or_none()
    return {"balance_cents": wallet.balance_cents if wallet else 0}

@router.get("/history/{guest_session_id}")
async def get_history(guest_session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(GuestWallet).where(GuestWallet.guest_session_id == guest_session_id))
    wallet = result.scalar_one_or_none()
    if not wallet: 
        return {"history": []}
    
    txs = await db.execute(
        select(WalletTransaction)
        .where(WalletTransaction.guest_wallet_id == wallet.id)
        .order_by(WalletTransaction.created_at.desc())
        .limit(20)
    )
    return {"history": txs.scalars().all()}

@router.post("/deduct", dependencies=[Depends(verify_admin_master_key)])
async def deduct_credit(req: DeductCreditRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(GuestWallet).where(GuestWallet.guest_session_id == req.guest_session_id))
    wallet = result.scalar_one_or_none()
    if not wallet or wallet.balance_cents < req.amount_cents:
        raise HTTPException(status_code=400, detail="Fondos insuficientes")

    tx = WalletTransaction(
        guest_wallet_id=wallet.id,
        amount_cents=-req.amount_cents,
        transaction_type="PURCHASE",
        reference_id=req.reference_id,
        reason=req.reason
    )
    wallet.balance_cents -= req.amount_cents
    db.add(tx)
    db.add(wallet)
    await db.commit()
    return {"status": "success", "new_balance_cents": wallet.balance_cents}
