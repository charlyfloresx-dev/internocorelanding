import uuid

class LicenseService:
    """
    Stub para la generación de firmas JWS para despliegues On-Premise.
    """
    @staticmethod
    def generate_license_signature(payload: dict) -> str:
        # TODO: Implement JWS signing logic with python-jose
        # Por ahora es un mock
        return f"JWS_STUB_{uuid.uuid4().hex}"

    @staticmethod
    def verify_license(signature: str) -> bool:
        # Placeholder para validación
        return signature.startswith("JWS_STUB_")
