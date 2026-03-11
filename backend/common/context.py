from contextvars import ContextVar
from typing import Any


# Variable de contexto global para la petición.
# NO DEBE IMPORTAR NADA DEL PROYECTO para evitar dependencias circulares.
# El tipo se valida en el middleware al hacer .set()
request_context: ContextVar[Any] = ContextVar("request_context", default=None)