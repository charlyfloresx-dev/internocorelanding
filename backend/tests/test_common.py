import pytest
import uuid
from decimal import Decimal
from dataclasses import FrozenInstanceError

# Imports del módulo common
# Asumimos que PYTHONPATH incluye 'backend/'
from common.models import MultiTenantBase
from common.value_objects import Money, UOM
from common.enums import CurrencyType
from common.exceptions import NotFoundException
from common.responses import ApiResponse

# --- Test de Modelos ---
class TempModel(MultiTenantBase):
    __tablename__ = "temp_model_test"
    # MultiTenantBase es abstracta, necesitamos una concreta para inspeccionar
    pass

def test_model_defaults_configuration():
    """
    Verifica que los modelos base tengan configurados los defaults correctos en SQLAlchemy.
    Nota: Al no usar sesión de DB ni flush, los valores no se generan en __init__ automáticamente,
    por lo que validamos la configuración de la columna (metadata).
    """
    # Verificamos que la columna ID tenga el default generator correcto (uuid.uuid4)
    id_column = TempModel.__table__.c.id
    assert id_column.default.is_callable and id_column.default.arg.__name__ == "uuid4"
    
    # Verificamos que is_active tenga default True
    is_active_column = TempModel.__table__.c.is_active
    assert is_active_column.default.arg is True
    
    # Verificamos que company_id sea obligatorio (nullable=False) e indexado
    company_id_column = TempModel.__table__.c.company_id
    assert company_id_column.nullable is False
    assert company_id_column.index is True

# --- Test de Value Objects ---
def test_money_operations():
    m1 = Money(amount=Decimal("10.00"), currency=CurrencyType.USD)
    m2 = Money(amount=Decimal("20.00"), currency=CurrencyType.USD)
    
    # Suma correcta
    result = m1 + m2
    assert result.amount == Decimal("30.00")
    assert result.currency == CurrencyType.USD
    
    # Inmutabilidad: la suma retorna un nuevo objeto
    assert result is not m1
    assert result is not m2

def test_money_different_currencies_error():
    m_usd = Money(amount=Decimal("10.00"), currency=CurrencyType.USD)
    m_mxn = Money(amount=Decimal("10.00"), currency=CurrencyType.MXN)
    
    # Validamos que sumar peras con manzanas lance error
    with pytest.raises(ValueError, match="Cannot add different currencies"):
        _ = m_usd + m_mxn

def test_uom_immutability():
    uom = UOM(code="KG", name="Kilogram")
    
    # Validamos que sea frozen (inmutable)
    with pytest.raises(FrozenInstanceError):
        uom.code = "LB"

# --- Test de Excepciones ---
def test_not_found_exception_structure():
    entity = "User"
    entity_id = "12345"
    exc = NotFoundException(entity=entity, entity_id=entity_id)
    
    # Verificamos status code HTTP
    assert exc.status_code == 404
    
    # Verificamos que detail sea un diccionario estructurado (para el Middleware)
    assert isinstance(exc.detail, dict)
    assert exc.detail["code"] == "NOT_FOUND"
    assert f"{entity} with id {entity_id} not found" in exc.detail["message"]

# --- Test de Responses ---
def test_api_response_auto_trace_id():
    response = ApiResponse(
        status="success",
        message="Operation successful"
    )
    
    # Verificamos que meta se genere automáticamente
    assert response.meta is not None
    
    # Verificamos que trace_id sea un UUID válido
    try:
        uuid_obj = uuid.UUID(response.meta.trace_id)
        assert str(uuid_obj) == response.meta.trace_id
    except ValueError:
        pytest.fail("trace_id generado automáticamente no es un UUID válido")