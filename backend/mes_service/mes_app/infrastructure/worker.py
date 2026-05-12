import asyncio
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, update, and_
from common.infrastructure.database import AsyncSessionLocal as async_session_local
from mes_app.models.downtime import Downtime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mes.worker")

async def evaluate_downtime_escalations():
    """
    AL-006: Evalúa paros OPEN cada 5 min y dispara escalaciones.
    """
    logger.info(f"Running escalation evaluation at {datetime.now()}")
    
    async with async_session_local() as db:
        # 1. Buscar paros OPEN que no han escalado en los últimos 5 min 
        # o que acaban de abrirse y llevan > 5 min sin respuesta.
        threshold_time = datetime.now() - timedelta(minutes=5)
        
        query = select(Downtime).where(
            and_(
                Downtime.status == "OPEN",
                (Downtime.last_escalation_at == None) | (Downtime.last_escalation_at <= threshold_time)
            )
        )
        
        result = await db.execute(query)
        open_downtimes = result.scalars().all()
        
        for dt in open_downtimes:
            # Lógica de Escalación: Por ahora incrementamos nivel y logeamos
            # En el futuro esto llama al infra_service / notifications
            new_level = dt.escalation_level + 1
            logger.warning(f"ESCALATION: Downtime {dt.id} (Resource {dt.resource_result_id}) escalated to Level {new_level}")
            
            dt.escalation_level = new_level
            dt.last_escalation_at = datetime.now()
            
        await db.commit()

def start_worker():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(evaluate_downtime_escalations, 'interval', minutes=5)
    scheduler.start()
    logger.info("MES Background Worker started (Interval: 5min)")
    
    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass

if __name__ == "__main__":
    start_worker()
