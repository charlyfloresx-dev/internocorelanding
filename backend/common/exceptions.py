class DomainException(Exception):
    """
    Excepción base para todos los errores de lógica de negocio del sistema Interno Core.
    Permite capturar cualquier error de dominio de forma genérica.
    """
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class NotFoundException(DomainException):
    """
    Se lanza cuando un recurso (Usuario, Empresa, Producto, etc.) 
    no existe en la base de datos.
    """
    pass

class UnauthorizedException(DomainException):
    """
    Se lanza cuando las credenciales son inválidas o el usuario 
    no tiene permisos para realizar una acción (HTTP 401/403).
    """
    pass

class BusinessRuleException(DomainException):
    """
    Violación de regla de negocio específica 
    (ej. stock insuficiente, versión de producto duplicada, empresa inactiva).
    """
    pass

class ValidationException(DomainException):
    """
    Se lanza cuando los datos de entrada no cumplen con el formato 
    o las reglas de validación de los esquemas.
    """
    pass

class ConflictException(DomainException):
    """
    Se lanza cuando hay un conflicto de estado 
    (ej. intentar borrar un registro que tiene dependencias activas).
    """
    pass