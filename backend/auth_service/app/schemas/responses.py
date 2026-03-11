from typing import Generic, TypeVar, Any
from pydantic import BaseModel, ConfigDict

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    """
    Estructura estándar de respuesta para todos los microservicios.
    Soporta tipado genérico para el campo 'data'.
    """
    model_config = ConfigDict(from_attributes=True)
    
    status: str = "success"
    data: T | None = None
    message: str | None = None
    meta: dict[str, Any] | None = None