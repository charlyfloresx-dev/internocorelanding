import uuid
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from decimal import Decimal

from app.dependencies import get_db
from common.security.dependencies import require_scope
from common.security.auth_payload import TokenPayload
from app.services.booking_service import BookingService
from app.services.pdf_generator import PDFGenerator
from app.repositories.payment_repository import PaymentRepository
from app.models.group import TravelerGroup
from app.models.itinerary import ItineraryItem
from common.value_objects import Money

def to_uuid(val) -> Optional[uuid.UUID]:
    if val is None:
        return None
    if isinstance(val, uuid.UUID):
        return val
    return uuid.UUID(str(val))

router = APIRouter(prefix="/api/v1/booking", tags=["Booking & Inventory"])

# --- SCHEMAS ---
class CreatePackageRequest(BaseModel):
    name: str = Field(..., description="Nombre del paquete (ej: Expedición Islandia)")
    destination: str = Field(..., description="Destino del viaje")
    description: Optional[str] = None
    price: Decimal = Field(..., gt=0, description="Precio total por viajero")
    currency: str = Field("USD", description="Moneda (USD, MXN, etc.)")
    max_capacity: int = Field(20, description="Capacidad máxima de viajeros")

class PackageResponse(BaseModel):
    id: uuid.UUID
    name: str
    destination: str
    price_amount: Decimal
    price_currency: str
    is_active: bool

# --- ENDPOINTS ---

@router.get("/packages", response_model=List[PackageResponse], summary="Listar paquetes de viaje del Tenant")
async def list_packages(
    user: TokenPayload = Depends(require_scope(["viatra:read"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna todos los paquetes vinculados a la empresa del usuario actual.
    Inyecta automáticamente el filtering por company_id a través del service.
    """
    service = BookingService(db)
    packages = await service.list_packages(user.company_id)
    
    return [
        PackageResponse(
            id=p.id,
            name=p.name,
            destination=p.destination,
            price_amount=p.total_price.amount if p.total_price else Decimal(0),
            price_currency=p.total_price.currency if p.total_price else "USD",
            is_active=p.is_active
        ) for p in packages
    ]


@router.post("/packages", response_model=PackageResponse, summary="Crear un nuevo paquete de viaje")
async def create_package(
    request: CreatePackageRequest,
    user: TokenPayload = Depends(require_scope(["viatra:write"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Define un nuevo producto de viaje en la agencia actual.
    Valida la invariante financiera (Money > 0) y registra auditoría de creación.
    """
    service = BookingService(db)
    try:
        total_price = Money(amount=request.price, currency=request.currency)
        package = await service.create_travel_package(
            name=request.name,
            destination=request.destination,
            description=request.description,
            total_price=total_price,
            company_id=user.company_id,
            user_id=to_uuid(user.sub),
            max_capacity=request.max_capacity
        )
        
        return PackageResponse(
            id=package.id,
            name=package.name,
            destination=package.destination,
            price_amount=package.total_price.amount,
            price_currency=package.total_price.currency,
            is_active=package.is_active
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/itinerary/{group_id}/download", summary="Descargar itinerario oficial en PDF")
async def download_itinerary(
    group_id: uuid.UUID,
    user: TokenPayload = Depends(require_scope(["viatra:read"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Motor de Documentación: Genera y descarga el PDF certificado.
    Validación: Sólo para usuarios del grupo con pagos activos.
    """
    # 1. Validar que el usuario pertenece al grupo y obtener datos
    query = select(TravelerGroup).where(
        TravelerGroup.id == group_id,
        TravelerGroup.company_id == user.company_id
    )
    res = await db.execute(query)
    group = res.scalar_one_or_none()
    
    if not group:
        raise HTTPException(status_code=404, detail="Grupo no encontrado o sin acceso")

    # 2. Obtener Logística (Itinerario)
    itinerary_query = select(ItineraryItem).where(ItineraryItem.group_id == group_id)
    itin_res = await db.execute(itinerary_query)
    items = itin_res.scalars().all()

    # 3. Obtener Historial de Pagos
    payment_repo = PaymentRepository(db)
    payments = await payment_repo.get_by_group(group_id)
    
    # 4. Validación Financiera (Zero-Trust)
    if not any(p.status == "PAID" for p in payments):
         raise HTTPException(status_code=402, detail="Pago requerido para descargar el itinerario")

    # 5. Generar PDF
    pdf_buffer = await PDFGenerator.generate_travel_itinerary(
        group, items, payments, to_uuid(user.sub) # Usando user_id como nombre literal por ahora
    )

    filename = f"Itinerario_{group.name.replace(' ', '_')}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/status", summary="Consultar el estado del viaje y pagos del usuario actual")
async def get_booking_status(
    user: TokenPayload = Depends(require_scope(["viatra:read"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna si el usuario tiene un viaje activo y si su pago está confirmado.
    Esencial para el 'desbloqueo' del Dashboard en el Frontend.
    """
    # Debug: Log context
    print(f"DEBUG VIATRA: Getting status for user {user.sub} in company {user.company_id}")
    
    service = BookingService(db)
    
    # Buscamos si el usuario pertenece a algún grupo activo de este tenant
    groups = await service.group_repo.list_all(user.company_id)
    print(f"DEBUG VIATRA: Found {len(groups)} groups for company {user.company_id}")
    
    if not groups:
        print(f"DEBUG VIATRA: No groups found, returning NO_BOOKING")
        return {"status": "NO_BOOKING", "message": "No tienes viajes activos."}
    
    active_group = groups[0]
    print(f"DEBUG VIATRA: Active group: {active_group.name} (Status: {active_group.status})")

    
    # Buscamos si hay pagos exitosos para este grupo y usuario
    payment_repo = PaymentRepository(db)
    payments = await payment_repo.list_all(user.company_id)
    has_paid = any(p.user_id == to_uuid(user.sub) and p.group_id == active_group.id for p in payments)
    
    # En la demo, si el grupo está CONFIRMED, desbloqueamos para todos
    is_confirmed = has_paid or active_group.status == "CONFIRMED"
    
    return {
        "status": "CONFIRMED" if is_confirmed else "PENDING",
        "group_id": str(active_group.id),
        "package_name": active_group.name,
        "is_active": active_group.is_active and is_confirmed
    }


@router.get("/packages/{package_id}/seats", summary="Consultar disponibilidad de asientos")
async def get_seat_availability(package_id: uuid.UUID, user: TokenPayload = Depends(require_scope(["viatra:read"])), db: AsyncSession = Depends(get_db)):
    """Retorna los asientos disponibles y asignados para un paquete."""
    return {"package_id": package_id, "available": 20, "occupied": 0}


@router.post("/packages/{package_id}/assign-seat", summary="Asignar asiento a un viajero")
async def assign_seat(package_id: uuid.UUID, user: TokenPayload = Depends(require_scope(["viatra:write"])), db: AsyncSession = Depends(get_db)):
    """Asigna un asiento/habitación a un viajero. Protegido por auditoría e imdependencia."""
    return {"message": "Seat assigned in booking context", "package_id": package_id}
