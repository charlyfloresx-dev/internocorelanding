import uuid
from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Optional, Literal, Generic, TypeVar

# Define the generic type
T = TypeVar("T")

class ApiMeta(BaseModel):
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    latency: Optional[str] = None
    
    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow"
    )
    
# Inherit from Generic[T] to allow ApiResponse[Model]
class ApiResponse(BaseModel, Generic[T]):
    status: Literal["success", "error"] = "success"
    data: Optional[T] = None
    message: str = "Operation successful"
    code: Optional[str] = None  # For i18n on the frontend
    meta: ApiMeta = Field(default_factory=ApiMeta)
    
    model_config = ConfigDict(
        populate_by_name=True
    )

    @classmethod
    def error(cls, message: str, code: Optional[str] = None, data: Any = None, trace_id: Optional[str] = None):
        """Metodo de conveniencia para crear respuestas de error estandarizadas."""
        response = cls(
            status="error",
            message=message,
            code=code,
            data=data
        )
        if trace_id:
            response.meta.trace_id = trace_id
        return response