import uuid
from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Optional, Literal, Generic, TypeVar

# Definimos el tipo genérico
T = TypeVar("T")

class ApiMeta(BaseModel):
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    latency: Optional[str] = None
    
    model_config = ConfigDict(
        populate_by_name=True
    )
    
# Heredamos de Generic[T] para permitir ApiResponse[Modelo]
class ApiResponse(BaseModel, Generic[T]):
    status: Literal["success", "error"] = "success"
    data: Optional[T] = None # <-- T en lugar de Any
    message: str = "Operation successful"
    meta: ApiMeta = Field(default_factory=ApiMeta)
    
    model_config = ConfigDict(
        populate_by_name=True
    )