import logging
import sys
from typing import Any, Dict
from common.context import request_context

class TenantFilter(logging.Filter):
    """
    Filtro de logging que inyecta company_id y user_id del contexto actual en cada registro.
    """
    def filter(self, record):
        ctx = request_context.get()
        record.company_id = str(ctx.company_id) if ctx and ctx.company_id else "SYSTEM"
        record.user_id = str(ctx.user_id) if ctx and ctx.user_id else "ANONYMOUS"
        record.trace_id = ctx.trace_id if ctx and ctx.trace_id else "NONE"
        return True

def setup_global_logging(service_name: str, level: int = logging.INFO):
    """
    Configura el sistema de logging estándar para los microservicios de Interno Core.
    Incluye formateo con Tenant ID y Trace ID para observabilidad.
    """
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Limpiar handlers existentes para evitar duplicados en recargas de Uvicorn
    if logger.handlers:
        for handler in logger.handlers:
            logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    
    # Formato premium con colores (si se desea) o estructurado
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(company_id)s] [%(user_id)s] [%(trace_id)s] [%(name)s]: %(message)s'
    )
    
    handler.setFormatter(formatter)
    handler.addFilter(TenantFilter())
    
    logger.addHandler(handler)
    
    # Evitar logs excesivos de librerías
    logging.getLogger("uvicorn.access").addFilter(TenantFilter())
    logging.getLogger("uvicorn.error").addFilter(TenantFilter())
    
    logging.info(f"Logging initialized for {service_name}")
    return logger

# Singleton-like logger proxy
def get_logger(name: str):
    return logging.getLogger(name)
