import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

try:
    from wms_service.app.models.warehouse import Warehouse
    print("Warehouse import directly: OK")
    from wms_service.app.models import Warehouse
    print("Warehouse import from package: OK")
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()
