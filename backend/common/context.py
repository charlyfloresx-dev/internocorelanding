from contextvars import ContextVar
from typing import Optional
from common.models.user_context import UserContext

# Esta es la pieza que falta y que detiene todo el sistema
request_context: ContextVar[Optional[UserContext]] = ContextVar("request_context", default=None)