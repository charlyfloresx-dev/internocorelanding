class AssetManagerException(Exception):
    """Base exception for the Asset Manager domain."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class OpportunityNotFoundException(AssetManagerException):
    def __init__(self, cve_cat: str):
        super().__init__(f"No se encontró la oportunidad con clave: {cve_cat}", status_code=404)


class ZoneConfigNotFoundException(AssetManagerException):
    def __init__(self, colonia: str):
        super().__init__(
            f"No existe configuración de VM para la colonia '{colonia}'. "
            f"Por favor, ingresa el valor manualmente.",
            status_code=422
        )


class InsufficientDataException(AssetManagerException):
    def __init__(self, message: str = "Datos insuficientes para calcular el ROI."):
        super().__init__(message, status_code=422)
