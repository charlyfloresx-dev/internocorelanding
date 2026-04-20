"""
Product Price Management Endpoint (Phase 33.5)
==============================================
Full CRUD for the 10 price lists per company.
Includes support for:
  - Intelligent price resolution (warehouse > company) for the frontend.
  - Price Override: the "resolve" endpoint returns the suggested price but
    the system never blocks if allow_price_override==True in the product.
"""
from fastapi import APIRouter, Depends, status, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import List, Optional
from datetime import datetime
import uuid
import csv
import io

from app.models.product import Product
from app.models.product_price import ProductPrice, UnitType
from app.models.price_agreement import PriceAgreement
from app.models.partner import Partner
from app.dependencies import get_current_user, get_db
from common.responses import ApiResponse
from common.domain.entities.user_context import UserContext
from pydantic import BaseModel, Field
from decimal import Decimal

router = APIRouter()

# ── [INDUSTRIAL DOWNLOAD BRIDGE] ──────────────────────────────────────────
# Global in-memory store for one-time download tickets.
# In a multi-worker production environment, this should be moved to Redis.
DOWNLOAD_TICKETS = {}

# ── [INDUSTRIAL DOWNLOAD BRIDGE] ──────────────────────────────────────────
# Global in-memory store for one-time download tickets.
# In a multi-worker production environment, this should be moved to Redis.
DOWNLOAD_TICKETS = {}


# ── Pydantic Schemas (inline for simplicity) ─────────────────────────────

class ProductPriceCreate(BaseModel):
    product_id: uuid.UUID
    price_list_index: int = Field(default=1, ge=0, le=10, description="0 (COMPRA / Costo), 1-10 (Listas de Venta)")
    amount: Decimal = Field(gt=0, description="Net price without taxes")
    currency: str = Field(default="MXN", max_length=3)
    unit_type: UnitType = UnitType.SALE
    warehouse_id: Optional[uuid.UUID] = None


class ProductPriceUpdate(BaseModel):
    amount: Decimal = Field(gt=0)
    is_active: Optional[bool] = None


class ProductPriceRead(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    price_list_index: int
    amount: Decimal
    currency: str
    unit_type: UnitType
    warehouse_id: Optional[uuid.UUID]
    is_active: bool

    class Config:
        from_attributes = True

def map_price(p: ProductPrice) -> ProductPriceRead:
    return ProductPriceRead(
        id=p.id,
        product_id=p.product_id,
        price_list_index=p.price_list_index,
        amount=p.price.amount,
        currency=p.price.currency,
        unit_type=p.unit_type,
        warehouse_id=p.warehouse_id,
        is_active=p.is_active
    )


class PriceAgreementCreate(BaseModel):
    product_id: uuid.UUID
    partner_id: uuid.UUID
    amount: Decimal = Field(gt=0)
    currency: str = Field(default="MXN", max_length=3)

class PriceAgreementRead(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    partner_id: uuid.UUID
    amount: Decimal
    currency: str
    valid_from: datetime
    valid_until: Optional[datetime]
    source: str
    is_manual: bool

    class Config:
        from_attributes = True


class PriceResolutionResult(BaseModel):
    """Price resolver result for the frontend (suggested, non-blocking)."""
    product_id: uuid.UUID
    resolved_amount: Decimal
    currency: str
    unit_type: UnitType
    price_list_index: int
    warehouse_id: Optional[uuid.UUID]
    resolution_level: str  # "WAREHOUSE_SPECIFIC" | "COMPANY_GLOBAL" | "NOT_FOUND"
    allow_override: bool
    warning: Optional[str] = None


# ── ENDPOINTS ──────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=ApiResponse[List[ProductPriceRead]],
    summary="List all company prices"
)
async def list_all_prices(
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists all active prices for the current company."""
    query = select(ProductPrice).where(
        and_(
            ProductPrice.company_id == current_user.company_id,
            ProductPrice.is_active == True
        )
    )
    result = await db.execute(query)
    prices = result.scalars().all()
    return ApiResponse(status="success", data=[map_price(p) for p in prices])


@router.get(
    "/products/{product_id}/prices",
    response_model=ApiResponse[List[ProductPriceRead]],
    summary="List all price lists for a product"
)
async def list_product_prices(
    product_id: uuid.UUID,
    currency: Optional[str] = Query(None, description="Filter by MXN or USD"),
    list_index: Optional[int] = Query(None, ge=0, le=10),
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists all price lists (1-10) for a product of the current company."""
    query = select(ProductPrice).where(
        and_(
            ProductPrice.product_id == product_id,
            ProductPrice.company_id == current_user.company_id,
            ProductPrice.is_active == True
        )
    )
    if currency:
        query = query.where(ProductPrice._currency == currency.upper())
    if list_index:
        query = query.where(ProductPrice.price_list_index == list_index)

    result = await db.execute(query)
    prices = result.scalars().all()
    return ApiResponse(status="success", data=[map_price(p) for p in prices])


@router.post(
    "/products/{product_id}/prices",
    response_model=ApiResponse[ProductPriceRead],
    status_code=status.HTTP_201_CREATED,
    summary="Create or update a list price"
)
async def upsert_product_price(
    product_id: uuid.UUID,
    price_in: ProductPriceCreate,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Creates a list price for the product. If the combination already exists,
    deactivates the previous one and creates a new one (immutable history)."""
    if price_in.product_id != product_id:
        raise HTTPException(status_code=400, detail="product_id in body does not match URL")

    # Deactivate previous price for the same list+unit+warehouse+currency
    existing_q = select(ProductPrice).where(
        and_(
            ProductPrice.product_id == product_id,
            ProductPrice.company_id == current_user.company_id,
            ProductPrice.price_list_index == price_in.price_list_index,
            ProductPrice.unit_type == price_in.unit_type,
            ProductPrice._currency == price_in.currency.upper(),
            ProductPrice.warehouse_id == price_in.warehouse_id,
            ProductPrice.is_active == True,
        )
    )
    existing_result = await db.execute(existing_q)
    old_price = existing_result.scalar_one_or_none()
    if old_price:
        old_price.is_active = False
        db.add(old_price)

    new_price = ProductPrice(
        id=uuid.uuid4(),
        product_id=product_id,
        company_id=current_user.company_id,
        tenant_id=current_user.company_id,
        group_id=current_user.group_id,
        price_list_index=price_in.price_list_index,
        _amount=price_in.amount,
        _currency=price_in.currency.upper(),
        unit_type=price_in.unit_type,
        warehouse_id=price_in.warehouse_id,
        is_active=True,
        version_id=1,
        created_by=current_user.user_id,
    )
    db.add(new_price)
    await db.commit()
    await db.refresh(new_price)
    return ApiResponse(status="success", data=map_price(new_price), message="Price registered successfully")


@router.get(
    "/products/{product_id}/prices/resolve",
    response_model=ApiResponse[PriceResolutionResult],
    summary="Resolve the suggested price for a transaction"
)
async def resolve_price(
    product_id: uuid.UUID,
    warehouse_id: Optional[uuid.UUID] = Query(None),
    price_list_index: int = Query(default=1, ge=0, le=10),
    currency: str = Query(default="MXN"),
    unit_type: UnitType = Query(default=UnitType.SALE),
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Resolves the suggested price for a transaction following the hierarchy:
      1. Specific warehouse (warehouse_id matches)
      2. Global company (warehouse_id IS NULL)
    
    The returned price is SUGGESTED. If Product.allow_price_override == True,
    the user can modify it freely in the transaction.
    """
    # Get product to verify allow_price_override
    prod_result = await db.execute(
        select(Product).where(
            and_(Product.id == product_id, Product.company_id == current_user.company_id)
        )
    )
    product = prod_result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    base_filter = and_(
        ProductPrice.product_id == product_id,
        ProductPrice.company_id == current_user.company_id,
        ProductPrice.price_list_index == price_list_index,
        ProductPrice.unit_type == unit_type,
        ProductPrice._currency == currency.upper(),
        ProductPrice.is_active == True,
    )

    # Level 1: specific warehouse price
    if warehouse_id:
        spec_result = await db.execute(
            select(ProductPrice).where(and_(base_filter, ProductPrice.warehouse_id == warehouse_id))
        )
        specific = spec_result.scalar_one_or_none()
        if specific:
            return ApiResponse(status="success", data=PriceResolutionResult(
                product_id=product_id, resolved_amount=specific._amount,
                currency=specific._currency, unit_type=specific.unit_type,
                price_list_index=specific.price_list_index,
                warehouse_id=specific.warehouse_id,
                resolution_level="WAREHOUSE_SPECIFIC",
                allow_override=product.allow_price_override,
            ))

    # Level 2: global company price
    global_result = await db.execute(
        select(ProductPrice).where(and_(base_filter, ProductPrice.warehouse_id.is_(None)))
    )
    global_price = global_result.scalar_one_or_none()
    if global_price:
        return ApiResponse(status="success", data=PriceResolutionResult(
            product_id=product_id, resolved_amount=global_price._amount,
            currency=global_price._currency, unit_type=global_price.unit_type,
            price_list_index=global_price.price_list_index, warehouse_id=None,
            resolution_level="COMPANY_GLOBAL",
            allow_override=product.allow_price_override,
        ))

    # No configured price — user can always enter override
    warning = None if product.allow_price_override else "No configured price found and allow_price_override=False"
    return ApiResponse(status="success", data=PriceResolutionResult(
        product_id=product_id, resolved_amount=Decimal("0"),
        currency=currency.upper(), unit_type=unit_type,
        price_list_index=price_list_index, warehouse_id=warehouse_id,
        resolution_level="NOT_FOUND",
        allow_override=product.allow_price_override,
        warning=warning or "No master price configured. Manual price required.",
    ))



# ── [DOWNLOAD CONTEXT / TICKET CREATION] ─────────────────────────────────

class DownloadTicket(BaseModel):
    ticket: str
    export_url: str

@router.post(
    "/export/ticket",
    summary="Create a temporary ticket for native browser download",
    response_model=ApiResponse[DownloadTicket]
)
async def create_price_export_ticket(
    entity_id: Optional[uuid.UUID] = None,
    current_user: UserContext = Depends(get_current_user),
):
    """
    Step 1: Create a secure ticket with the user's context.
    This bypasses the 'Blob naming' issue in Chrome by allowing native navigation.
    """
    ticket_id = str(uuid.uuid4())
    DOWNLOAD_TICKETS[ticket_id] = {
        "company_id": current_user.company_id,
        "user_id": current_user.user_id,
        "group_id": current_user.group_id,
        "entity_id": entity_id,
        "created_at": datetime.now()
    }
    
    # We return the frontend-ready URL with a dummy .csv suffix to force Chrome naming
    return ApiResponse(data=DownloadTicket(
        ticket=ticket_id,
        export_url=f"/api/v1/prices/download/native/{ticket_id}/plantilla_precios.csv"
    ))


@router.get(
    "/download/native/{ticket_id}/{filename}",
    summary="Redeem ticket for native file download with naming suffix",
    response_class=StreamingResponse
)
async def native_price_download_bridge(
    ticket_id: str,
    filename: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Step 2: Native browser navigation (GET). 
    This uses the ticket to authorize the download without Bearer headers,
    ensuring Chrome respects the filename in Content-Disposition.
    """
    if ticket_id not in DOWNLOAD_TICKETS:
        raise HTTPException(status_code=404, detail="Ticket de descarga inválido o expirado")
    
    ctx = DOWNLOAD_TICKETS.pop(ticket_id)
    company_id = ctx["company_id"]
    entity_id = ctx["entity_id"]
    
    # Logic path A: B2B Agreements (Entity specific)
    if entity_id:
        partner = await db.get(Partner, entity_id)
        if not partner or partner.company_id != company_id:
            raise HTTPException(status_code=403, detail="Acceso denegado a entidad")
            
        query = (
            select(PriceAgreement, Product)
            .join(Product, PriceAgreement.product_id == Product.id)
            .where(and_(
                PriceAgreement.partner_id == entity_id,
                PriceAgreement.company_id == company_id,
                PriceAgreement.valid_until.is_(None)
            ))
        )
        result = await db.execute(query)
        agreements = result.all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["SKU", "Nombre", "Nivel", "Moneda", "Monto", "IVA_Flag", "IEPS_Flag", "Entidad_ID", "Tipo_Entidad"])
        
        for ag, prod in agreements:
            writer.writerow([
                prod.sku, prod.name, "ACUERDO", ag._currency, str(ag._amount),
                "SI" if prod.is_taxable else "NO", "NO", str(partner.id), partner.type.value
            ])
            
        output.seek(0)
        filename = f"acuerdos_{partner.code}_{datetime.now().strftime('%Y%m%d')}.csv"
        response = StreamingResponse(iter([output.getvalue()]), media_type="text/csv")
        response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    # Logic path B: General Prices
    else:
        query = (
            select(Product, ProductPrice)
            .outerjoin(ProductPrice, and_(
                Product.id == ProductPrice.product_id,
                ProductPrice.is_active == True,
                ProductPrice.price_list_index.in_([0, 1]),
                ProductPrice.warehouse_id.is_(None)
            ))
            .where(and_(Product.company_id == company_id, Product.is_active == True))
        )
        result = await db.execute(query)
        data = result.all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["SKU", "Nombre", "Nivel", "Moneda", "Monto", "IVA_Flag", "IEPS_Flag", "Entidad_ID", "Tipo_Entidad"])
        
        for prod, price in data:
            amount = str(price._amount) if price else "0.00"
            currency = price._currency if price else "MXN"
            level = "COMPRA" if price and price.price_list_index == 0 else "1"
            writer.writerow([prod.sku, prod.name, level, currency, amount, "SI", "NO", "", ""])
            
        output.seek(0)
        filename = f"plantilla_precios_{datetime.now().strftime('%Y%m%d')}.csv"
        response = StreamingResponse(iter([output.getvalue()]), media_type="text/csv")
        response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


@router.post(
    "/agreements",
    response_model=ApiResponse[PriceAgreementRead],
    status_code=status.HTTP_201_CREATED,
    summary="Create or update a special B2B price agreement"
)
async def upsert_price_agreement(
    agreement_in: PriceAgreementCreate,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Creates or updates a client-specific price. Follows Soft-Close & Insert rule.
    """
    # 1. Soft-Close any active agreement for this product+partner+currency
    old_stmt = select(PriceAgreement).where(
        and_(
            PriceAgreement.product_id == agreement_in.product_id,
            PriceAgreement.partner_id == agreement_in.partner_id,
            PriceAgreement.company_id == current_user.company_id,
            PriceAgreement.currency == agreement_in.currency.upper(),
            PriceAgreement.valid_until.is_(None)
        )
    )
    for old_ag in (await db.execute(old_stmt)).scalars().all():
        old_ag.valid_until = func.now()
        db.add(old_ag)

    # 2. Insert new immutable version
    new_agreement = PriceAgreement(
        id=uuid.uuid4(),
        product_id=agreement_in.product_id,
        partner_id=agreement_in.partner_id,
        company_id=current_user.company_id,
        tenant_id=current_user.company_id,
        group_id=current_user.group_id,
        amount=agreement_in.amount,
        currency=agreement_in.currency.upper(),
        source="MANUAL",
        is_manual=True,
        version_id=1,
        created_by=current_user.user_id,
    )
    db.add(new_agreement)
    await db.commit()
    await db.refresh(new_agreement)
    
    return ApiResponse(status="success", data=PriceAgreementRead.model_validate(new_agreement))

@router.get(
    "/products/{product_id}/agreements",
    response_model=ApiResponse[List[PriceAgreementRead]],
    summary="List special B2B price agreements for a product"
)
async def list_product_agreements(
    product_id: uuid.UUID,
    partner_id: Optional[uuid.UUID] = Query(None),
    currency: Optional[str] = Query(None),
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(PriceAgreement).where(
        and_(
            PriceAgreement.product_id == product_id,
            PriceAgreement.company_id == current_user.company_id,
            PriceAgreement.valid_until.is_(None) # solo vigentes
        )
    )
    if partner_id:
        query = query.where(PriceAgreement.partner_id == partner_id)
    if currency:
        query = query.where(PriceAgreement.currency == currency.upper())

    result = await db.execute(query)
    agreements = result.scalars().all()
    return ApiResponse(status="success", data=[PriceAgreementRead.model_validate(p) for p in agreements])

@router.get(
    "/agreements/export/template/{entity_id}",
    response_class=StreamingResponse
)
async def download_agreements_template(
    entity_id: uuid.UUID,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generates a CSV filled with the CURRENT agreements for a specific partner (customer/vendor).
    """
    partner_res = await db.execute(select(Partner).where(and_(Partner.id == entity_id, Partner.company_id == current_user.company_id)))
    partner = partner_res.scalar_one_or_none()
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")

    query = select(PriceAgreement, Product).join(Product, PriceAgreement.product_id == Product.id).where(
        and_(
            PriceAgreement.company_id == current_user.company_id,
            PriceAgreement.partner_id == entity_id,
            PriceAgreement.is_active == True
        )
    )
    result = await db.execute(query)
    agreements = result.all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["SKU", "Nombre", "Nivel", "Moneda", "Monto", "IVA_Flag", "IEPS_Flag", "Entidad_ID", "Tipo_Entidad"])
    
    if not agreements:
        # Si no hay acuerdos, por lo menos mandar el encabezado
        pass
    
    for ag, prod in agreements:
        writer.writerow([
            prod.sku, prod.name, "ACUERDO", ag.currency, str(ag.amount),
            "SI" if prod.is_taxable else "NO", "NO", str(partner.id), partner.type.value
        ])
    
    output.seek(0)
    response = StreamingResponse(iter([output.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename=acuerdos_{partner.code}.csv"
    return response


@router.post(
    "/import",
    summary="Mass import pricing via CSV — Immutable Soft-Close pipeline"
)
async def import_prices_csv(
    file: UploadFile = File(...),
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Implements the Soft-Close + Insert immutability contract atomically.

    IMMUTABILITY RULES:
      - 'amount' is NEVER updated in-place on an existing row.
      - Soft-Close seals valid_until = NOW() on the current active record.
      - A brand-new row (new UUID) is inserted as the next version.
      - If the insert fails, the Soft-Close is rolled back too — Version 1 stays alive.

    CSV columns:
      SKU, Nivel (COMPRA | 0-10 | ACUERDO), Moneda, Monto,
      IVA_Flag (SI/NO), IEPS_Flag (SI/NO), Entidad_ID (UUID, optional)
    """
    content = await file.read()
    # Encoding defense: Cali-Baja Excel exports are often Latin-1 or utf-8-sig (BOM)
    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        decoded = content.decode("iso-8859-1")

    reader = csv.DictReader(io.StringIO(decoded))

    required_cols = {"SKU", "Nivel", "Moneda", "Monto"}
    if not required_cols.issubset(set(reader.fieldnames or [])):
        raise HTTPException(
            status_code=422,
            detail=f"Formato invalido. Columnas requeridas: {required_cols}. "
                   f"Columnas detectadas: {set(reader.fieldnames or [])}"
        )

    # Pre-load product map once — avoids N+1 lookups
    prod_q = await db.execute(
        select(Product.id, Product.sku).where(Product.company_id == current_user.company_id)
    )
    products_map = {row.sku: row.id for row in prod_q.all()}

    rows = list(reader)
    processed = 0
    errors: list = []

    try:
        for i, row in enumerate(rows, start=2):
            sku = row.get("SKU", "").strip()
            if not sku or sku not in products_map:
                errors.append({"fila": i, "sku": sku, "error": "SKU no encontrado para este tenant"})
                continue

            product_id = products_map[sku]

            monto_str = row.get("Monto", "").strip()
            try:
                monto = Decimal(monto_str)
                if monto < 0:
                    raise ValueError("negative")
            except Exception:
                errors.append({"fila": i, "sku": sku, "error": f"Monto invalido: '{monto_str}'"})
                continue

            nivel = str(row.get("Nivel", "")).strip().upper()
            moneda = row.get("Moneda", "MXN").strip().upper()
            entidad_id_str = row.get("Entidad_ID", "").strip()

            # ── Branch A: PriceAgreement (B2B Contract) ──────────────────────
            if nivel == "ACUERDO" or entidad_id_str:
                if not entidad_id_str:
                    errors.append({"fila": i, "sku": sku, "error": "ACUERDO requiere Entidad_ID"})
                    continue

                try:
                    partner_uuid = uuid.UUID(entidad_id_str)
                except ValueError:
                    errors.append({"fila": i, "sku": sku, "error": f"Entidad_ID no es UUID: {entidad_id_str}"})
                    continue

                partner_exists = await db.execute(
                    select(Partner.id).where(
                        and_(Partner.id == partner_uuid, Partner.company_id == current_user.company_id)
                    )
                )
                if not partner_exists.scalar_one_or_none():
                    errors.append({"fila": i, "sku": sku, "error": f"Partner no pertenece al tenant"})
                    continue

                # SOFT-CLOSE: only valid_until is touched — amount stays immutable
                old_stmt = select(PriceAgreement).where(
                    and_(
                        PriceAgreement.product_id == product_id,
                        PriceAgreement.partner_id == partner_uuid,
                        PriceAgreement.company_id == current_user.company_id,
                        PriceAgreement.currency == moneda,
                        PriceAgreement.valid_until.is_(None)
                    )
                )
                for old_ag in (await db.execute(old_stmt)).scalars().all():
                    old_ag.valid_until = func.now()   # seal — amount NOT changed
                    db.add(old_ag)

                # NEW VERSION: fresh UUID, fresh row, valid_until=NULL (active)
                db.add(PriceAgreement(
                    id=uuid.uuid4(),
                    product_id=product_id,
                    partner_id=partner_uuid,
                    company_id=current_user.company_id,
                    tenant_id=current_user.company_id,
                    group_id=current_user.group_id,
                    amount=monto,
                    currency=moneda,
                    source="CSV_IMPORT",
                    is_manual=False,
                    version_id=1,
                    created_by=current_user.user_id,
                ))

            # ── Branch B: General Price List (Nivel 0-10) ─────────────────────
            else:
                if nivel == "COMPRA":
                    list_index = 0
                else:
                    try:
                        list_index = int(nivel)
                        if not (0 <= list_index <= 10):
                            raise ValueError
                    except ValueError:
                        errors.append({"fila": i, "sku": sku, "error": f"Nivel invalido: '{nivel}'. Usar COMPRA, ACUERDO o 0-10"})
                        continue

                # SOFT-CLOSE on general price
                for old_pr in (await db.execute(
                    select(ProductPrice).where(
                        and_(
                            ProductPrice.product_id == product_id,
                            ProductPrice.company_id == current_user.company_id,
                            ProductPrice.price_list_index == list_index,
                            ProductPrice._currency == moneda,
                            ProductPrice.warehouse_id.is_(None),
                            ProductPrice.is_active == True
                        )
                    )
                )).scalars().all():
                    old_pr.is_active = False
                    old_pr.valid_until = func.now()
                    db.add(old_pr)

                # NEW VERSION
                from common.value_objects import Money
                print(f"DEBUG: Importando precio para {sku} - Monto: {monto} {moneda}")
                db.add(ProductPrice(
                    id=uuid.uuid4(),
                    product_id=product_id,
                    company_id=current_user.company_id,
                    tenant_id=current_user.company_id,
                    group_id=current_user.group_id,
                    price_list_index=list_index,
                    price=Money(amount=monto, currency=moneda),
                    unit_type=UnitType.SALE,
                    is_active=True,
                    is_manual=False,
                    version_id=1,
                    created_by=current_user.user_id,
                ))

            # ── Tax Flag Sync (optional column) ──────────────────────────────
            iva_flag = str(row.get("IVA_Flag", "")).strip().upper()
            if iva_flag in {"SI", "NO"}:
                prod_q2 = await db.execute(select(Product).where(Product.id == product_id))
                prod_to_upd = prod_q2.scalar_one_or_none()
                if prod_to_upd:
                    prod_to_upd.is_taxable = (iva_flag == "SI")
                    db.add(prod_to_upd)

            processed += 1

        # ATOMIC COMMIT — reaches here only if no unhandled exception above
        await db.commit()

    except Exception as exc:
        # FULL ROLLBACK — Soft-Close reversals are also undone, zero data mutation
        await db.rollback()
        return ApiResponse(
            status="error",
            data={"procesados": 0, "errores": [{"fila": "SISTEMA", "error": str(exc)}]},
            message="Error critico — transaccion revertida. Ningun dato fue modificado."
        )

    return ApiResponse(
        status="success",
        data={"procesados": processed, "errores": errors},
        message=f"Importacion finalizada. {processed} nuevas versiones creadas, {len(errors)} omitidas."
    )

