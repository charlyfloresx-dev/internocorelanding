from fastapi import APIRouter, Depends, status, HTTPException, Header, Query, File, UploadFile, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Any, Optional
import uuid

from master_app.schemas.product import ProductCreate, ProductRead, ProductReadWithVersions, ProductUpdate
from master_app.services.product_service import ProductService
from common.domain import ProductStatus, VersionStatus
from master_app.dependencies import get_current_user, get_product_service
from common.responses import ApiResponse
from common.exceptions import DomainException, NotFoundException
from common.domain.entities.user_context import UserContext
from common.security.limiter import limiter

router = APIRouter()

# --- CRUD BÁSICO ---

@router.post("/", response_model=ApiResponse[ProductReadWithVersions], status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def create_product(
    request: Request,
    product_in: ProductCreate,
    photo: Optional[UploadFile] = File(None),
    current_user: UserContext = Depends(get_current_user),
    service: ProductService = Depends(get_product_service)
):
    """ Crear un nuevo producto con su versión inicial y opcionalmente una foto. """
    try:
        product = await service.create_product(product_in, photo=photo)
        # El servicio debe retornar el objeto con sus relaciones cargadas si se espera ProductReadWithVersions
        return ApiResponse(status="success", data=product, message="Product created successfully")
    except DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=ApiResponse[List[ProductRead]])
async def get_products(
    q: Optional[str] = Query(None, description="Buscar por SKU o Nombre"),
    warehouse_id: Optional[uuid.UUID] = Query(None, description="Resolver precios para este almacén"),
    current_user: UserContext = Depends(get_current_user),
    service: ProductService = Depends(get_product_service)
):
    """ Listar productos de la compañía actual con filtro opcional. """
    products = await service.get_products_by_company(current_user.company_id, q=q, warehouse_id=warehouse_id)
    return ApiResponse(status="success", data=products, message="Product list retrieved successfully")

@router.get("/{product_id}", response_model=ApiResponse[ProductReadWithVersions])
async def get_product(
    product_id: uuid.UUID,
    current_user: UserContext = Depends(get_current_user),
    service: ProductService = Depends(get_product_service)
):
    """ Obtener detalle de un producto específico con sus versiones. """
    product = await service.get_product_by_id(product_id, current_user.company_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return ApiResponse(status="success", data=product)

@router.patch("/{product_id}", response_model=ApiResponse[ProductRead])
async def update_product(
    product_id: uuid.UUID,
    update_in: ProductUpdate,
    current_user: UserContext = Depends(get_current_user),
    service: ProductService = Depends(get_product_service)
):
    """ Actualizar campos de un producto existente. """
    update_data = update_in.model_dump(exclude_unset=True)
    product = await service.update_product(product_id, current_user.company_id, update_data)
    return ApiResponse(status="success", data=product, message="Product updated successfully")

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: uuid.UUID,
    current_user: UserContext = Depends(get_current_user),
    service: ProductService = Depends(get_product_service)
):
    """ Soft-delete un producto. """
    await service.delete_product(product_id, current_user.company_id)
    return None

# --- GESTIÓN DE VERSIONES ---

@router.post("/{product_id}/versions", response_model=ApiResponse[ProductReadWithVersions])
async def create_product_version(
    product_id: uuid.UUID,
    version_in: Any, # Debería ser un schema ProductVersionCreate
    current_user: UserContext = Depends(get_current_user),
    service: ProductService = Depends(get_product_service)
):
    """ Crear una nueva versión técnica para un producto existente. """
    product = await service.approve_version(product_id, version_in.version_number, current_user.company_id)
    return ApiResponse(status="success", data=product, message="New version created successfully")
# --- INTERNAL ENDPOINTS (Inter-service) ---

@router.get("/internal/{product_id}", response_model=ApiResponse[ProductRead])
async def get_product_internal(
    product_id: uuid.UUID,
    service: ProductService = Depends(get_product_service),
    x_company_id: uuid.UUID = Header(...)
):
    """
    Endpoint interno para validación entre microservicios (bypass auth usuario).
    """
    try:
        product = await service.get_product_by_id(product_id, x_company_id)
        return ApiResponse(status="success", data=product)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
