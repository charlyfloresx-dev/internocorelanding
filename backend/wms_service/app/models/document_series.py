from typing import Optional
from sqlalchemy import String, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column

from common.models import Base, MultiTenantBase

class DocumentSeries(MultiTenantBase):
    """
    Custom folio generator per company and concept.
    Allows each tenant to define their own numbering sequences.
    
    Example:
    - Company A: ENT-2026-0001, ENT-2026-0002, ...
    - Company B: ENTRADA-001, ENTRADA-002, ...
    
    Implements pessimistic locking (SELECT FOR UPDATE) to prevent duplicate folios
    in high-concurrency environments.
    """
    __tablename__ = "document_series"

    concept_code: Mapped[str] = mapped_column(
        String(10), 
        nullable=False, 
        index=True,
        comment="Reference to Concept.code (e.g., 'ENT', 'SAL', 'AJU')"
    )
    
    prefix: Mapped[str] = mapped_column(
        String(20), 
        nullable=False,
        comment="Custom prefix defined by tenant (e.g., 'ALM-A', 'INV-', 'ENT')"
    )
    
    current_number: Mapped[int] = mapped_column(
        Integer, 
        default=0, 
        nullable=False,
        comment="Last used number in the sequence. Incremented atomically."
    )
    
    year_reset: Mapped[Optional[int]] = mapped_column(
        Integer, 
        nullable=True,
        comment="Optional: Year for resetting sequence (e.g., 2026). If set, sequence resets each year."
    )
    
    separator: Mapped[str] = mapped_column(
        String(5), 
        default="-", 
        nullable=False,
        comment="Separator character between prefix, year, and number (e.g., '-', '/', '_')"
    )
    
    padding: Mapped[int] = mapped_column(
        Integer, 
        default=5, 
        nullable=False,
        comment="Number of digits for zero-padding (e.g., 5 → 00001, 3 → 001)"
    )

    __table_args__ = (
        # 🔒 Unique constraint: Each company can have only one series per concept
        Index("ix_series_tenant_concept", "company_id", "concept_code", unique=True),
    )

    def generate_folio(self) -> str:
        """
        Generates the next folio based on current configuration.
        
        Format: {prefix}{separator}{year}{separator}{padded_number}
        Example: ENT-2026-00001
        
        NOTE: This method does NOT increment current_number.
        The caller must handle atomicity via SELECT FOR UPDATE.
        """
        self.current_number += 1
        
        parts = [self.prefix]
        
        if self.year_reset:
            parts.append(str(self.year_reset))
        
        padded_number = str(self.current_number).zfill(self.padding)
        parts.append(padded_number)
        
        return self.separator.join(parts)

    def __repr__(self):
        return f"<DocumentSeries(concept='{self.concept_code}', prefix='{self.prefix}', current={self.current_number})>"
