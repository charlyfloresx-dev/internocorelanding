import asyncio
import logging
import uuid
from datetime import datetime, time, timedelta

# Clean Architecture: Use services and repositories, not DB sessions directly
from app.db.session import async_session_maker
from app.services.currency_service import CurrencyService
from app.infrastructure.repositories.currency_repository import SQLAlchemyCurrencyRepository
from app.infrastructure.clients.rate_provider import ExternalRateProvider
from common.config import settings

logger = logging.getLogger(__name__)

async def run_daily_currency_fetch():
    """
    Worker que se ejecuta una vez al día a las 12:00 PM (mediodía)
    para recolectar las cuatro fuentes de verdad (Banxico, DolarApi, eldolar, Frankfurter)
    y almacenar el historial.
    """
    target_time = time(hour=12, minute=0, second=0)
    
    # 1. Recuperación de estado:
    # Verificamos si en el día actual ya se ha ejecutado el snapshot automático.
    try:
        async with async_session_maker() as session:
            repo = SQLAlchemyCurrencyRepository(session)
            # Busca si hay al menos un registro automático hoy para el tenant global
            zero_uuid = uuid.UUID(int=0)
            has_run_today = await repo.has_automatic_rates_today(zero_uuid)
        
        if not has_run_today:
            logger.info("[CurrencyWorker] 🚨 No se encontró cosecha automática hoy. Ejecutando ahora mismo (Auto-Recuperación)...")
            await fetch_and_store_all_rates()
        else:
            logger.info("[CurrencyWorker] ✅ La cosecha automática de hoy ya existía. Pasando directo al modo inactivo (Sleep).")
    except Exception as e:
        logger.error(f"[CurrencyWorker] Error al verificar recuperación: {e}")

    # 2. Ciclo infinito de mediodía
    while True:
        now_local = datetime.now()
        next_run = datetime.combine(now_local.date(), target_time)
        
        if now_local.time() > target_time:
            next_run += timedelta(days=1)
            
        wait_seconds = (next_run - now_local).total_seconds()
        logger.info(f"[CurrencyWorker] Durmiendo {wait_seconds} segundos hasta {next_run}...")
        
        await asyncio.sleep(wait_seconds)
        
        logger.info("[CurrencyWorker] Despertando para obtener el snapshot del mediodía...")
        try:
            await fetch_and_store_all_rates()
        except Exception as e:
            logger.error(f"[CurrencyWorker] Error crítico durante la recolección: {e}")


async def fetch_and_store_all_rates():
    provider = ExternalRateProvider(banxico_token=settings.int_banxico_token)
    
    async with async_session_maker() as session:
        # Repositorio inyectado en el Servicio — Sin fugas de sesión en el servicio
        repo = SQLAlchemyCurrencyRepository(session)
        service = CurrencyService(repo, provider)
        
        zero_uuid = uuid.UUID(int=0)
        logger.info(f"[CurrencyWorker] Actualizando historial GLOBAL ({zero_uuid})")
        
        # Se automatiza la recolección del par USD-MXN primario
        await service.update_rates_automatically(company_id=zero_uuid, base="USD", targets=["MXN", "EUR"])
        
        # Guardar cambios (flush ya lo hace el repo, pero el commit final lo hace el worker como orquestador)
        await session.commit()
            
        logger.info("[CurrencyWorker] ¡Cosecha del mediodía completada!")
