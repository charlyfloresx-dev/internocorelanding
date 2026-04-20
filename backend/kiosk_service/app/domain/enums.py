import enum

class PaymentMethod(str, enum.Enum):
    STRIPE = "STRIPE"
    CASH = "CASH"
    WALLET = "WALLET"

class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class PhotoStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PURCHASED = "PURCHASED"
    PRINTING = "PRINTING"
    DONE = "DONE"
