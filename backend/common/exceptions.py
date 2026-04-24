class DomainException(Exception):
    """
    Base exception for all business logic errors in the Interno Core system.
    Allows capturing any domain error generically.
    """
    status_code: int = 400

    def __init__(self, message: str, details: dict = None, status_code: int = None):
        self.message = message
        self.details = details or {}
        if status_code is not None:
            self.status_code = status_code
        super().__init__(self.message)

class NotFoundException(DomainException):
    """
    Raised when a resource (User, Company, Product, etc.) 
    does not exist in the database.
    """
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, details, status_code=404)

class UnauthorizedException(DomainException):
    """
    Raised when credentials are invalid or the user 
    does not have permission to perform an action (HTTP 401/403).
    """
    status_code: int = 403

    def __init__(self, message: str, details: dict = None):
        super().__init__(message, details, status_code=403)

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
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, details, status_code=422)

class ValidationException(DomainException):
    """
    Raised when input data does not comply with the format 
    or validation rules of the schemas.
    """
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, details, status_code=422)

class ConflictException(DomainException):
    """
    Raised when there is a state conflict 
    (e.g., trying to delete a record with active dependencies).
    """
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, details, status_code=409)