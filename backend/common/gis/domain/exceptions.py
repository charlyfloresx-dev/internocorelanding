from common.exceptions import DomainException

class GisServiceException(DomainException):
    """Excepción base para errores relacionados con servicios GIS."""
    def __init__(self, message: str = "Error en el servicio GIS", details: dict = None):
        super().__init__(message=message, details=details)
        self.status_code = 500

class GisProviderUnavailableException(GisServiceException):
    """El proveedor GIS (ej. Ayuntamiento de Tijuana) no está disponible o devolvió un error (ej. 404, 500)."""
    def __init__(self, message: str = "Proveedor GIS no disponible. Intente de nuevo más tarde.", details: dict = None):
        super().__init__(message=message, details=details)
        self.status_code = 502

class GisOutsideBoundaryException(GisServiceException):
    """Las coordenadas están fuera de un predio o municipio soportado."""
    def __init__(self, message: str = "Las coordenadas provistas no caen dentro de un predio delimitado.", details: dict = None):
        super().__init__(message=message, details=details)
        self.status_code = 404

class CadastralKeyNotFoundException(GisServiceException):
    """La clave catastral solicitada no devolvió resultados en el cruce de información."""
    def __init__(self, message: str = "No se encontró información legal o espacial para la clave catastral indicada.", details: dict = None):
        super().__init__(message=message, details=details)
        self.status_code = 404
