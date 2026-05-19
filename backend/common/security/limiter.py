import logging
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request
from common.config import settings

logger = logging.getLogger(__name__)

def multi_layer_key_func(request: Request) -> str:
    """
    Estrategia de Identificación Multi-capa para InternoCore con Bypass:
    1. Bypass: Si tiene X-Internal-Secret o X-Admin-Master-Key válido, retorna None (Exento).
    2. Layer 3 (User): Si el usuario está autenticado, el límite es por UUID.
    3. Layer 2 (Tenant): Si hay un company_id, el límite es por empresa.
    4. Layer 1 (IP): Fallback a la dirección IP.
    """
    # 0. Lógica de Bypass (Muro de Hierro Bypass)
    internal_secret = request.headers.get("X-Internal-Secret")
    if internal_secret and internal_secret == settings.INTERNAL_API_KEY:
        return None
    
    admin_key = request.headers.get("X-Admin-Master-Key")
    if admin_key and admin_key == settings.int_admin_master_key:
        return None

    # 1. Intentar obtener el ID del usuario (Capa 3)
    user_token = getattr(request.state, "user_token", None)
    if user_token and hasattr(user_token, "sub") and user_token.sub:
        return f"user:{user_token.sub}"

    # 2. Intentar obtener el ID de la empresa (Capa 2)
    company_id = request.headers.get("X-Company-ID")
    if company_id:
        return f"tenant:{company_id}"

    # 3. Fallback a IP real (respeta X-Real-IP / X-Forwarded-For de Nginx/ALB)
    # request.client.host sería la IP del proxy, no del cliente — usar headers
    for header in ("X-Real-IP", "X-Forwarded-For"):
        value = request.headers.get(header)
        if value:
            return value.split(",")[0].strip()
    return get_remote_address(request)

# Configuración del Limiter
storage_uri = settings.REDIS_URL if settings.REDIS_URL else "memory://"

limiter = Limiter(
    key_func=multi_layer_key_func,
    storage_uri=storage_uri,
    default_limits=["2000 per hour", "100 per minute"] # Límites globales de seguridad
)



logger.info(f"Rate Limiter inicializado con storage: {storage_uri} (Strategy: multi-layer)")
