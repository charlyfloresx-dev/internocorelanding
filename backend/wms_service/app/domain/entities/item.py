import uuid
from dataclasses import dataclass
from typing import Optional

@dataclass
class ItemEntity:
    id: uuid.UUID
    company_id: uuid.UUID
    code: str
    name: str
    sku: Optional[str] = None
    version_number: Optional[int] = None
    stock_quantity: float = 0.0
    master_product_id: Optional[uuid.UUID] = None
