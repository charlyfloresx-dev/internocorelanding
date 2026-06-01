class DomainException(Exception):
    """
    Base exception for all business logic errors in the Interno Core system.
    Allows capturing any domain error generically.
    """
    status_code: int = 400

    def __init__(self, message: str, details: dict = None, status_code: int = None, code: str = None):
        self.message = message
        self.details = details or {}
        self.code = code
        if status_code is not None:
            self.status_code = status_code
        super().__init__(self.message)

class NotFoundException(DomainException):
    """
    Raised when a resource (User, Company, Product, etc.) 
    does not exist in the database.
    """
    def __init__(self, message: str, details: dict = None, code: str = "NOT_FOUND"):
        super().__init__(message, details, status_code=404, code=code)

class UnauthorizedException(DomainException):
    """
    Raised when credentials are invalid or the user 
    does not have permission to perform an action (HTTP 401/403).
    """
    status_code: int = 403

    def __init__(self, message: str, details: dict = None, code: str = "UNAUTHORIZED"):
        super().__init__(message, details, status_code=403, code=code)

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
    def __init__(self, message: str, details: dict = None, code: str = "BUSINESS_RULE_VIOLATION"):
        super().__init__(message, details, status_code=422, code=code)

class ValidationException(DomainException):
    """
    Raised when input data does not comply with the format 
    or validation rules of the schemas.
    """
    def __init__(self, message: str, details: dict = None, code: str = "VALIDATION_ERROR"):
        super().__init__(message, details, status_code=422, code=code)

class ConflictException(DomainException):
    """
    Raised when there is a state conflict
    (e.g., trying to delete a record with active dependencies).
    """
    def __init__(self, message: str, details: dict = None, code: str = "CONFLICT"):
        super().__init__(message, details, status_code=409, code=code)

class OptimisticLockError(ConflictException):
    """
    Optimistic locking conflict: another process modified the record.
    Used in RTR for concurrent refresh token rotation detection.
    """
    def __init__(self, message: str, details: dict = None, code: str = "OPTIMISTIC_LOCK_FAILED"):
        super().__init__(message, details, code=code)