from enum import Enum


class InvoiceStatus(str, Enum):
    DRAFT = "DRAFT"
    ISSUED = "ISSUED"
    SENT = "SENT"
    PAID = "PAID"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"
    VOIDED = "VOIDED"

    @property
    def translation_key(self) -> str:
        return f"billing.invoice.status.{self.value.lower()}"


class CreditNoteType(str, Enum):
    RETURN = "RETURN"
    DISCOUNT = "DISCOUNT"
    ERROR_CORRECTION = "ERROR_CORRECTION"

    @property
    def translation_key(self) -> str:
        return f"billing.credit_note.type.{self.value.lower()}"


class PaymentMethod(str, Enum):
    CASH = "CASH"
    BANK_TRANSFER = "BANK_TRANSFER"
    CHECK = "CHECK"
    CREDIT_CARD = "CREDIT_CARD"
    OTHER = "OTHER"

    @property
    def translation_key(self) -> str:
        return f"billing.payment.method.{self.value.lower()}"
