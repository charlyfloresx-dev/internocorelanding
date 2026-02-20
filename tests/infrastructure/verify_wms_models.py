import sys
import os

# Set PYTHONPATH for local imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from wms_service.app.models import Warehouse, InventoryDocument, InventoryMovement, InventorySnapshot
from common.models import MultiTenantBase, AuditBase, BaseEntity
from sqlalchemy import Numeric

def verify_wms_models():
    print("🔍 Iniciando validación de Modelos WMS Enriquecidos (SQLAlchemy 2.0)...")
    
    models = [Warehouse, InventoryDocument, InventoryMovement, InventorySnapshot]
    
    for model in models:
        print(f"\n--- Validando {model.__name__} ---")
        
        # 1. Verificar Herencia ADN
        if issubclass(model, MultiTenantBase) and issubclass(model, AuditBase) and issubclass(model, BaseEntity):
            print(f"ADN (Mixins): ✅ Pasó")
        else:
            print(f"ADN (Mixins): ❌ FALLÓ")
            
        # 2. Verificar Multi-tenancy (company_id)
        if hasattr(model, 'company_id'):
            col = model.__table__.columns.get('company_id')
            if col is not None and not col.nullable:
                print(f"Multi-tenancy (company_id NOT NULL): ✅ Pasó")
            else:
                print(f"Multi-tenancy (company_id): ❌ FALLÓ")
        
        # 3. Verificar Precisión Decimal (Numeric 18,4)
        has_numeric = False
        for col_name, col in model.__table__.columns.items():
            if isinstance(col.type, Numeric):
                has_numeric = True
                if col.type.precision == 18 and col.type.scale == 4:
                    print(f"Precisión [{col_name}]: ✅ Numeric(18,4)")
                else:
                    print(f"Precisión [{col_name}]: ❌ {col.type}")
                    
        if model.__name__ in ["InventoryMovement", "InventorySnapshot"] and not has_numeric:
            print("Precisión Decimal: ❌ No se encontraron columnas Numeric")

        # 4. Verificar Campos Específicos
        if model.__name__ == "Warehouse":
            if 'description' in model.__table__.columns: print("Warehouse.description: ✅")
            if 'type_id' in model.__table__.columns: print("Warehouse.type_id: ✅")
        elif model.__name__ == "InventoryDocument":
            if 'currency_code' in model.__table__.columns: print("InventoryDocument.currency_code: ✅")
        elif model.__name__ == "InventoryMovement":
            if 'lot_number' in model.__table__.columns: print("InventoryMovement.lot_number: ✅")

    print("\n✅ Validación de Modelos WMS Completada.")

if __name__ == "__main__":
    verify_wms_models()
