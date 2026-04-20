from slowapi import Limiter
from slowapi.util import get_remote_address

# Inicialización genérica. 
# Utiliza get_remote_address como estrategia por defecto para rastrear la IP del cliente.
# NOTA PARA AWS: Tras un ALB, asegurar que el servidor (Uvicorn/Proxy) confíe en X-Forwarded-For
# para evitar que todas las peticiones se cuenten para la IP interna del balanceador.
limiter = Limiter(key_func=get_remote_address)
