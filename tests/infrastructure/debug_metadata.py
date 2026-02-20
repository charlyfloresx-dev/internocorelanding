import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from wms_service.app.models import Base
print(f"Tables in Metadata: {list(Base.metadata.tables.keys())}")
