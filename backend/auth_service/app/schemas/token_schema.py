from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class CompanyAccessDto(BaseModel):
    """
    DTO para la lista de empresas disponibles en el login.
    Refleja los datos del modelo CompanyStub y UserCompanyRole.
    """
    company_id: UUID
    company_name: str
    tax_id: Optional[str] = None
    domain: Optional[str] = None
    logo: Optional[str] = None
    scopes: List[str] = []

    model_config = ConfigDict(from_attributes=True)

class LoginResponseData(BaseModel):
    selection_token: str
    companies: List[CompanyAccessDto]
    # message: str = "Login successful" # Opcional, según tu estructura de respuesta
