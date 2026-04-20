from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.event import Event
from app.services.onboarding_service import EventOnboardingService

router = APIRouter()

class SetupEventIn(BaseModel):
    event_name: str
    photo_price: int
    rule_paparazzi: bool
    required_approvals: int = 2
    watermark_b64: Optional[str] = None
    frontend_base_url: str = "http://localhost:4200"

@router.get("/", response_model=List[dict])
async def list_events(db: AsyncSession = Depends(get_db)):
    """Lists all configured events."""
    result = await db.execute(select(Event).order_by(Event.created_at.desc()))
    events = result.scalars().all()
    return [
        {
            "id": str(e.id),
            "name": e.name,
            "slug": e.slug,
            "photo_price": e.photo_price,
            "rule_paparazzi": e.rule_paparazzi,
            "required_approvals": e.required_approvals,
            "watermark_active": e.watermark_key is not None,
            "created_at": e.created_at.isoformat() if e.created_at else None
        } for e in events
    ]

@router.post("/setup")
async def setup_event(payload: SetupEventIn, db: AsyncSession = Depends(get_db)):
    """
    Onboards a new event locally.
    1. Stores the watermark logo to MinIO.
    2. Persists event to Database.
    3. Generates 3 operational QR codes for the event.
    """
    try:
        # Check if exists
        slug = payload.event_name.lower().replace(" ", "_")
        existing = await db.execute(select(Event).where(Event.slug == slug))
        if existing.scalars().first():
             # If exists, we just return the QRs (or we could update)
             # Let's assume for now we want to support recovering QRs
             pass

        # Save Watermark if supplied
        watermark_key = None
        if payload.watermark_b64:
            watermark_key = EventOnboardingService.process_watermark(
                payload.event_name, 
                payload.watermark_b64
            )
            
        # Generar QRs Maestros
        qrs = EventOnboardingService.generate_event_qrs(
            payload.event_name, 
            payload.frontend_base_url,
            payload.required_approvals
        )
        
        # Persistir en DB
        new_event = Event(
            name=payload.event_name,
            slug=slug,
            photo_price=payload.photo_price,
            rule_paparazzi=payload.rule_paparazzi,
            required_approvals=payload.required_approvals,
            watermark_key=watermark_key
        )
        db.add(new_event)
        await db.commit()
        await db.refresh(new_event)
        
        return {
            "status": "success",
            "message": "Evento configurado correctamente",
            "event_id": str(new_event.id),
            "event_name": new_event.name,
            "config": {
                "photo_price": new_event.photo_price,
                "rule_paparazzi": new_event.rule_paparazzi,
                "required_approvals": new_event.required_approvals,
                "watermark_active": watermark_key is not None
            },
            "qrs": qrs
        }
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error in Event Onboarding: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="No se pudo inicializar el evento")

@router.get("/{event_id}/qrs")
async def get_event_qrs(event_id: str, frontend_base_url: str = "http://localhost:4200", db: AsyncSession = Depends(get_db)):
    """Retrieves QRs for an existing event."""
    import uuid
    try:
        ev_id = uuid.UUID(event_id)
        result = await db.execute(select(Event).where(Event.id == ev_id))
        event = result.scalars().first()
        if not event:
            raise HTTPException(status_code=404, detail="Evento no encontrado")
            
        qrs = EventOnboardingService.generate_event_qrs(
            event.name, 
            frontend_base_url,
            event.required_approvals
        )
        return {
            "event_name": event.name,
            "qrs": qrs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
