from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.dependencies import get_db
from common.security.dependencies import require_scope
from common.security.auth_payload import TokenPayload
from app.models.group import TravelerGroup
from app.models.price_alert import PriceAlert
from app.models.itinerary import ItineraryItem



router = APIRouter(prefix="/api/v1/sentinel", tags=["SkySentinel — Monitoring"])

@router.get("/status", summary="Consultar salud y métricas del bot SkySentinel")
async def get_sentinel_status(
    user: TokenPayload = Depends(require_scope(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Dashboard del Administrador: Visualiza el desempeño de los bots de rastreo.
    """
    # 1. Contar activos monitoreados
    flights_q = select(func.count(TravelerGroup.id)).where(
        TravelerGroup.flight_number != None,
        TravelerGroup.is_active == True,
        TravelerGroup.company_id == user.company_id
    )
    hotels_q = select(func.count(ItineraryItem.id)).where(
        ItineraryItem.item_type == "ACCOMMODATION",
        ItineraryItem.is_active == True,
        ItineraryItem.company_id == user.company_id
    )
    
    flights_res = await db.execute(flights_q)
    hotels_res = await db.execute(hotels_q)

    # 2. Obtener alertas generadas
    alerts_query = select(PriceAlert).where(
        PriceAlert.company_id == user.company_id
    ).order_by(PriceAlert.created_at.desc()).limit(15)
    alerts_res = await db.execute(alerts_query)
    recent_alerts = alerts_res.scalars().all()

    return {
        "bot_status": "ONLINE",
        "services": {
            "sky_sentinel": "V1.2 (Active)",
            "stay_guardian": "V1.0 (Active)"
        },
        "metrics": {
            "monitored_flights": flights_res.scalar(),
            "monitored_hotels": hotels_res.scalar(),
        },
        "recent_alerts": [
            {
                "type": a.alert_type,
                "asset": a.flight_number if a.alert_type == "FLIGHT_DROP" else "HOTEL_BLOCK",
                "message": a.notes,
                "timestamp": a.created_at
            } for a in recent_alerts
        ]
    }

