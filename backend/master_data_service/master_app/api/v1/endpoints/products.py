from fastapi import Security, APIRouter, Depends, status, HTTPException, Header, Query, File, UploadFile, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import List, Any, Optional
from decimal import Decimal
import uuid
import logging

from master_app.schemas.product import (
    ProductCreate, ProductRead, ProductReadWithVersions, ProductUpdate,
    ProductBulkItem, ProductBulkResult,
)
from master_app.services.product_service import ProductService
from common.domain import ProductStatus, VersionStatus
from master_app.dependencies import get_current_user, get_product_service, get_db
from common.responses import ApiResponse
from common.exceptions import DomainException, NotFoundException
from common.domain.entities.user_context import UserContext
from common.security.dependencies import require_scope
from common.security.limiter import limiter
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ProductBulkPayload(BaseModel):
    products: List[ProductBulkItem] = []

router = APIRouter()

# --- CRUD BÁSICO ---

@router.post("/", response_model=ApiResponse[ProductReadWithVersions], status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def create_product(
    request: Request,
    product_in: ProductCreate,
    photo: Optional[UploadFile] = File(None),
    current_user: UserContext = Security(require_scope(["master_data:write"])),
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
    current_user: UserContext = Security(require_scope(["master_data:read"])),
    service: ProductService = Depends(get_product_service)
):
    """ Listar productos de la compañía actual con filtro opcional. """
    products = await service.get_products_by_company(current_user.company_id, q=q, warehouse_id=warehouse_id)
    return ApiResponse(status="success", data=products, message="Product list retrieved successfully")

@router.get("/{product_id}", response_model=ApiResponse[ProductReadWithVersions])
async def get_product(
    product_id: uuid.UUID,
    current_user: UserContext = Security(require_scope(["master_data:read"])),
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
    current_user: UserContext = Security(require_scope(["master_data:write"])),
    service: ProductService = Depends(get_product_service)
):
    """ Actualizar campos de un producto existente. """
    update_data = update_in.model_dump(exclude_unset=True)
    product = await service.update_product(product_id, current_user.company_id, update_data)
    return ApiResponse(status="success", data=product, message="Product updated successfully")

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: uuid.UUID,
    current_user: UserContext = Security(require_scope(["master_data:write"])),
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
    current_user: UserContext = Security(require_scope(["master_data:write"])),
    service: ProductService = Depends(get_product_service)
):
    """ Crear una nueva versión técnica para un producto existente. """
    product = await service.approve_version(product_id, version_in.version_number, current_user.company_id)
    return ApiResponse(status="success", data=product, message="New version created successfully")

@router.get("/lookup/{code}", response_model=ApiResponse[ProductRead])
async def lookup_product(
    code: str,
    partner_id: Optional[uuid.UUID] = Query(None),
    service: ProductService = Depends(get_product_service),
    current_user: UserContext = Security(require_scope(["master_data:read"]))
):
    """
    Lookups a product by its SKU or barcode for POS scanning.
    Includes dynamic price resolution if partner_id is provided.
    """
    product = await service.lookup_product_by_code(code, current_user.company_id, partner_id)
    if not product:
        raise HTTPException(status_code=404, detail=f"Producto no encontrado: {code}")
    return ApiResponse(status="success", data=product)


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


# --- BULK IMPORT (Onboarding Wizard) ---

@router.post("/bulk", response_model=ApiResponse[ProductBulkResult], status_code=status.HTTP_200_OK)
@limiter.limit("20/minute")
async def bulk_import_products(
    request: Request,
    payload: ProductBulkPayload,
    current_user: UserContext = Security(require_scope(["master_data:write"])),
    service: ProductService = Depends(get_product_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Importación masiva de productos desde el Onboarding Wizard.
    Idempotente: SKUs ya existentes se omiten (no error).
    La resolución de categoría y UOM es por nombre/código — no requiere UUIDs.
    """
    from master_app.models.product_category import ProductCategory
    from master_app.models.uom import UOM
    from master_app.models.product import Product
    from master_app.models.product_price import ProductPrice
    from common.domain import ProductType

    company_id = current_user.company_id
    result = ProductBulkResult()

    for item in payload.products:
        try:
            # Idempotency — skip if SKU already exists for this company
            exists_stmt = select(Product.id).where(
                Product.company_id == company_id,
                Product.sku == item.sku,
                Product.is_active == True,
            )
            if (await db.execute(exists_stmt)).scalar_one_or_none():
                result.skipped += 1
                continue

            # Resolve UOM by code (global or company-scoped)
            uom_stmt = select(UOM).where(
                UOM.code == item.uom_code.upper(),
                or_(UOM.company_id == company_id, UOM.company_id.is_(None)),
            ).limit(1)
            uom = (await db.execute(uom_stmt)).scalar_one_or_none()
            if not uom:
                result.errors.append(f"{item.sku}: UOM '{item.uom_code}' not found — using PZ default")
                uom_stmt2 = select(UOM).where(
                    UOM.code == "PZ",
                    or_(UOM.company_id == company_id, UOM.company_id.is_(None)),
                ).limit(1)
                uom = (await db.execute(uom_stmt2)).scalar_one_or_none()
                if not uom:
                    result.errors.append(f"{item.sku}: fallback UOM PZ also missing — skipped")
                    continue

            # Resolve category by name (ILIKE, global or company-scoped)
            category_id = None
            if item.category_tag:
                cat_stmt = select(ProductCategory).where(
                    ProductCategory.name.ilike(item.category_tag),
                    or_(ProductCategory.company_id == company_id, ProductCategory.company_id.is_(None)),
                ).limit(1)
                cat = (await db.execute(cat_stmt)).scalar_one_or_none()
                if cat:
                    category_id = cat.id

            product_in = ProductCreate(
                sku=item.sku,
                name=item.name,
                description=item.description,
                product_type=ProductType.GOODS,
                uom_id=uom.id,
                category_id=category_id,
            )
            product = await service.create_product(product_in)

            # Seed initial price if provided (Soft-Close pattern: single INSERT, valid_until=NULL)
            if item.unit_price is not None and item.unit_price > 0:
                price_rec = ProductPrice(
                    company_id=company_id,
                    tenant_id=company_id,
                    product_id=product.id,
                    price_list_index=1,
                    _amount=item.unit_price,
                    _currency=item.currency.upper(),
                )
                db.add(price_rec)
                await db.flush()

            result.created += 1

        except Exception as exc:
            logger.warning("bulk_import_products: %s — %s", item.sku, exc)
            result.errors.append(f"{item.sku}: {str(exc)}")

    await db.commit()
    return ApiResponse(
        status="success",
        data=result,
        message=f"Bulk import: {result.created} created, {result.skipped} skipped, {len(result.errors)} errors.",
    )
