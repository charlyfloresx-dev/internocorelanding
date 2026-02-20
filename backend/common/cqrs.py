from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Any

# Tipos genéricos para el resultado
R = TypeVar('R')

class ICommand(ABC):
    """
    Marcador para Comandos (Escritura/Mutación).
    Debe ser inmutable.
    """
    pass

class IQuery(Generic[R], ABC):
    """
    Marcador para Consultas (Lectura).
    Retorna un tipo R específico.
    """
    pass

class ICommandHandler(Generic[R], ABC):
    """
    Manejador de lógica de negocio para un Comando específico.
    """
    @abstractmethod
    async def handle(self, command: ICommand) -> R:
        raise NotImplementedError

class IQueryHandler(Generic[R], ABC):
    """
    Manejador de lógica de lectura para una Consulta específica.
    """
    @abstractmethod
    async def handle(self, query: IQuery[R]) -> R:
        raise NotImplementedError

# Nota: En Python, la implementación del 'Mediator' concreto se haría
# inyectando dinámicamente los handlers basados en el tipo de mensaje.