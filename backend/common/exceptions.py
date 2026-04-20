class DomainException(Exception):
    """
    Base exception for all business logic errors in the Interno Core system.
    Allows capturing any domain error generically.
    """
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class NotFoundException(DomainException):
    """
    Raised when a resource (User, Company, Product, etc.) 
    does not exist in the database.
    """
    pass

class UnauthorizedException(DomainException):
    """
    Raised when credentials are invalid or the user 
    does not have permission to perform an action (HTTP 401/403).
    """
    pass

class SelfTransferReceiptException(UnauthorizedException):
    """
    Security Exception: A user cannot receive a 
    transfer that they originated themselves (Segregation of Duties).
    """
    pass

class BusinessRuleException(DomainException):
    """
    Violation of a specific business rule 
    (e.g., insufficient stock, duplicate product version, inactive company).
    """
    pass

class ValidationException(DomainException):
    """
    Raised when input data does not comply with the format 
    or validation rules of the schemas.
    """
    pass

class ConflictException(DomainException):
    """
    Raised when there is a state conflict 
    (e.g., trying to delete a record with active dependencies).
    """
    pass