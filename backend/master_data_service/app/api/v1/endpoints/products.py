from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Any
import uuid

from app.schemas.product import ProductCreate, ProductReadWithVersions, ProductRead
from app.services.product_service import ProductService
from app.dependencies import get_db, get_current_user
from common.responses import ApiResponse
from common.exceptions import DomainException

router = APIRouter()

# --- CRUD BÁSICO ---

@router.post("/", response_model=ApiResponse[ProductReadWithVersions], status_code=status.HTTP_201_CREATED)
async def create_product(
    product_in: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """ Crear un nuevo producto con su versión inicial. """
    try:
        service = ProductService(db)
        product = await service.create_product(product_in, current_user.company_id)
        return ApiResponse(status="success", data=product, message="Producto creado exitosamente")
    except DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=ApiResponse[List[ProductRead]])
async def get_products(
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """ Listar productos de la compañía actual. """
    service = ProductService(db)
    products = await service.get_products_by_company(current_user.company_id)
    return ApiResponse(status="success", data=products, message="Listado de productos recuperado")

@router.get("/{product_id}", response_model=ApiResponse[ProductReadWithVersions])
async def get_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """ Obtener detalle de un producto específico. """
    service = ProductService(db)
    # El servicio debe validar que el producto pertenezca a la empresa
    product = await service.get_product_by_id(product_id, current_user.company_id)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return ApiResponse(status="success", data=product)

# --- GESTIÓN DE VERSIONES ---

@router.post("/{product_id}/versions", response_model=ApiResponse[ProductReadWithVersions])
async def create_product_version(
    product_id: uuid.UUID,
    version_in: Any, # Debería ser un schema ProductVersionCreate
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """ Crear una nueva versión técnica para un producto existente. """
    service = ProductService(db)
    product = await service.add_version_to_product(product_id, version_in, current_user.company_id)
    return ApiResponse(status="success", data=product, message="Nueva versión creada")