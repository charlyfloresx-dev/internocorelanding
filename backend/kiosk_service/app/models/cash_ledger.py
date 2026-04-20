from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey
from app.core.database import Base
import enum
from datetime import datetime

class TransactionCategory(str, enum.Enum):
    SALE = "SALE"           # Venta de foto (vía QR)
    FLOAT = "FLOAT"         # Fondo inicial
    PAYOUT = "PAYOUT"       # Gasto operativo
    ADJUSTMENT = "ADJUSTMENT" # Ajuste manual del Staff

class CashTransaction(Base):
    __tablename__ = "cash_transactions"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, nullable=False) # TransactionCategory
    amount = Column(Integer, nullable=False)  # En centavos
    concept = Column(String, nullable=False)
    staff_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relación opcional con evento si queremos cortes por evento
    event_id = Column(String, nullable=True)
