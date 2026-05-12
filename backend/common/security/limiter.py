import logging
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request
from common.config import settings

logger = logging.getLogger(__name__)

def multi_layer_key_func(request: Request) -> str:
    """
    Estrategia de Identificación Multi-capa para InternoCore:
    1. Layer 3 (User): Si el usuario está autenticado, el límite es por UUID de usuario.
    2. Layer 2 (Tenant): Si hay un company_id en el contexto/headers, el límite es por empresa.
    3. Layer 1 (IP): Fallback a la dirección IP del cliente.
    """
    # 1. Intentar obtener el ID del usuario (Capa 3)
    user_token = getattr(request.state, "user_token", None)
    if user_token and hasattr(user_token, "sub") and user_token.sub:
        return f"user:{user_token.sub}"

    # 2. Intentar obtener el ID de la empresa (Capa 2)
    company_id = request.headers.get("X-Company-ID")
    if company_id:
        return f"tenant:{company_id}"

    # 3. Fallback a IP (Capa 1)
    return get_remote_address(request)

# Configuración del Limiter
# Si CORE_REDIS_URL está presente, usamos Redis para unificar límites entre microservicios.
storage_uri = settings.REDIS_URL if settings.REDIS_URL else "memory://"

limiter = Limiter(
    key_func=multi_layer_key_func,
    storage_uri=storage_uri,
    default_limits=["2000 per hour", "100 per minute"] # Límites globales de seguridad
)

logger.info(f"Rate Limiter inicializado con storage: {storage_uri} (Strategy: multi-layer)")
