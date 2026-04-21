import sys
import os

# Simulando PYTHONPATH
sys.path.append(os.getcwd())
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "..")))

try:
    print("Intentando importar common.domain...")
    from common.domain import Base, MultiTenantBase, ProductStatus
    print("OK: common.domain importado.")
    
    print("Intentando importar app.models...")
    from master_app.models import Product, UM
    print("OK: app.models importado.")
    
    print(f"Base Metadata Tables: {Base.metadata.tables.keys()}")
    print(f"Product inherited from MultiTenantBase: {issubclass(Product, MultiTenantBase)}")
    
except Exception as e:
    import traceback
    traceback.print_exc()
