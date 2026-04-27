from sqlalchemy import Column, Numeric, String, create_mock_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, composite
from decimal import Decimal
import dataclasses

class Base(DeclarativeBase):
    pass

@dataclasses.dataclass
class Money:
    amount: Decimal
    currency: str

class Movement(Base):
    __tablename__ = "test"
    id: Mapped[int] = mapped_column(primary_key=True)
    _amount: Mapped[Decimal] = mapped_column("unit_price", Numeric(18, 4), key="_amount")
    _currency: Mapped[str] = mapped_column("currency", String(3), key="_currency")
    price: Mapped[Money] = composite(Money, _amount, _currency)

for column in Movement.__table__.columns:
    print(f"Column: {column.name}, Key: {column.key}")
