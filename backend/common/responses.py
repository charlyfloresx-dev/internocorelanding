import uuid
from pydantic import BaseModel, Field
from typing import Any, Optional, Literal, Generic, TypeVar

# Definimos el tipo genérico
T = TypeVar("T")

class ApiMeta(BaseModel):
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    latency: Optional[str] = None
    
# Heredamos de Generic[T] para permitir ApiResponse[Modelo]
class ApiResponse(BaseModel, Generic[T]):
    status: Literal["success", "error"]
    data: Optional[T] = None # <-- T en lugar de Any
    message: str
    meta: ApiMeta = Field(default_factory=ApiMeta)