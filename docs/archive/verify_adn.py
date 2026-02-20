import sys
import os

# 1. Asegurar que el orquestador y PYTHONPATH funcionen como en run.py
sys.path.append(os.path.join(os.getcwd(), "backend"))
sys.path.append(os.path.join(os.getcwd(), "backend", "common"))

from common.models import Base, BaseEntity, AuditBase, MultiTenantBase
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import inspect

# 2. Definir una entidad de prueba que use el ADN completo
class TestProduct(Base, BaseEntity, AuditBase, MultiTenantBase):
    __tablename__ = "test_products"
    name: Mapped[str] = mapped_column(nullable=False)

def verify_adn_integrity():
    print("🔍 Iniciando validación de ADN (InternoCore Mirror)...")
    
    # Verificar Herencia
    attrs = [column.key for column in inspect(TestProduct).mapper.column_attrs]
    
    checks = {
        "ID (BaseEntity)": "id" in attrs,
        "Audit (AuditBase)": "created_at" in attrs and "created_by" in attrs,
        "Multitenant (MultiTenantBase)": "company_id" in attrs
    }
    
    for label, passed in checks.items():
        status = "✅ PASÓ" if passed else "❌ FALLÓ"
        print(f"{label}: {status}")

    # Verificar restricción de CompanyID obligatorio
    is_nullable = inspect(TestProduct).column_attrs['company_id'].columns[0].nullable
    if not is_nullable:
        print("✅ Validación de Seguridad: company_id es MANDATORIO (nullable=False).")
    else:
        print("❌ ERROR: company_id permite valores nulos.")

if __name__ == "__main__":
    try:
        verify_adn_integrity()
    except Exception as e:
        print(f"❌ Error crítico en la estructura del ADN: {e}")
