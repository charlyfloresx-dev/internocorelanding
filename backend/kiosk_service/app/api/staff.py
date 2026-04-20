from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models.cash_ledger import CashTransaction, TransactionCategory
import os

router = APIRouter()

class CashEntry(BaseModel):
    category: TransactionCategory
    amount: int  # in cents
    concept: str
    staff_id: str
    event_id: str | None = None

@router.get("/manual")
async def get_offline_manual():
    # ... (keeps logic)
    path = "/app/docs/STAFF_OPERATIONS_MANUAL.md"
    if not os.path.exists(path):
        path = "../../eventKiosk/STAFF_OPERATIONS_MANUAL.md"
    try:
        with open(path, "r", encoding="utf-8") as f:
            return {"content": f.read()}
    except Exception as e:
        return {"error": f"Manual no accesible: {str(e)}"}

@router.get("/finance/status")
async def get_finance_status(db: AsyncSession = Depends(get_db)):
    """Calculates the theoretical balance based on transactions."""
    result = await db.execute(select(func.sum(CashTransaction.amount)))
    total_cents = result.scalar() or 0
    
    # Get last 10 transactions
    txs_result = await db.execute(select(CashTransaction).order_by(CashTransaction.created_at.desc()).limit(10))
    transactions = txs_result.scalars().all()
    
    return {
        "theoretical_balance_cents": total_cents,
        "recent_transactions": transactions
    }

@router.post("/finance/cash-entry")
async def register_cash_payment(entry: CashEntry, db: AsyncSession = Depends(get_db)):
    # Adjust amount sign for PAYOUT
    final_amount = entry.amount
    if entry.category == TransactionCategory.PAYOUT:
        final_amount = -abs(entry.amount)
        
    new_tx = CashTransaction(
        category=entry.category,
        amount=final_amount,
        concept=entry.concept,
        staff_id=entry.staff_id,
        event_id=entry.event_id
    )
    db.add(new_tx)
    await db.commit()
    
    return {
        "status": "success", 
        "amount": final_amount,
        "category": entry.category
    }
