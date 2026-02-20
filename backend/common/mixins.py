from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Numeric
from sqlalchemy.orm import Mapped, mapped_column

class MoneyMixin:
    """
    Value Object: Money (Flattened Strategy)
    Se aplana en la tabla contenedora como columnas 'amount' y 'currency'.
    
    Nota: Si una entidad requiere múltiples campos de dinero (ej: costo y precio),
    se deberá usar herencia con @declared_attr para prefijar las columnas.
    """
    # Decimal(18, 4) es estándar financiero para evitar errores de redondeo flotante
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

class AddressMixin:
    """
    Value Object: Address (Flattened Strategy)
    Representa una dirección física estándar.
    """
    street: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    exterior_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    interior_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    neighborhood: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    zip_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Coordenadas opcionales para logística futura
    geo_lat: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6), nullable=True)
    geo_lng: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6), nullable=True)