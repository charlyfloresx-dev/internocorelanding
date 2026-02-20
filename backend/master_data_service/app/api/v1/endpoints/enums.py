from typing import List, Any
from fastapi import APIRouter
from pydantic import BaseModel

from common.enums import ProductStatus, VersionStatus, ProductType
from common.responses import ApiResponse

router = APIRouter()

class EnumItem(BaseModel):
    id: Any
    name: str

@router.get("/product-status", response_model=ApiResponse[List[EnumItem]], summary="Listar estados de producto")
async def get_product_status():
    """Devuelve los valores posibles para el estado de un producto."""
    data = [{"id": e.value, "name": e.name} for e in ProductStatus]
    return ApiResponse(status="success", data=data, message="Estados de producto recuperados")

@router.get("/version-status", response_model=ApiResponse[List[EnumItem]], summary="Listar estados de versión")
async def get_version_status():
    """Devuelve los valores posibles para el estado de una versión de producto."""
    data = [{"id": e.value, "name": e.name} for e in VersionStatus]
    return ApiResponse(status="success", data=data, message="Estados de versión recuperados")

@router.get("/product-types", response_model=ApiResponse[List[EnumItem]], summary="Listar tipos de producto")
async def get_product_types():
    """Devuelve los tipos de productos (Good, Service, etc.)."""
    data = [{"id": e.value, "name": e.name} for e in ProductType]
    return ApiResponse(status="success", data=data, message="Tipos de producto recuperados")