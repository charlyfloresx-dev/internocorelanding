import os
import re

root_dir = r"c:\API\interno\backend"

# List of files from the audit report
files_to_fix = [
    "asset_manager_service/asset_app/application/schemas/opportunity.py",
    "auth_service/auth_app/domain/entities/user_aggregate.py",
    "auth_service/auth_app/schemas/auth.py",
    "auth_service/auth_app/schemas/company.py",
    "cmms_service/cmms_app/schemas/storage_schemas.py",
    "common/gis/domain/dtos.py",
    "common/gis/domain/interfaces/gis_service.py",
    "common/models/company.py",
    "inventory_service/inventory_app/models/backflush_error.py",
    "inventory_service/inventory_app/models/bom.py",
    "inventory_service/inventory_app/models/customs_pedimento.py",
    "inventory_service/inventory_app/models/stock_lot.py",
    "inventory_service/inventory_app/schemas/customs.py",
    "inventory_service/inventory_app/schemas/inventory.py",
    "inventory_service/inventory_app/schemas/pos.py",
    "master_data_service/master_app/models/product.py",
    "master_data_service/master_app/schemas/exchange_rate.py",
    "master_data_service/master_app/schemas/product.py",
    "mes_service/mes_app/models/downtime_event.py",
    "mes_service/mes_app/models/production_snapshot.py",
    "mes_service/mes_app/models/run_metrics_snapshot.py",
    "mes_service/mes_app/models/standard_time.py",
    "subscription_service/subscription_app/domain/entities/subscription.py",
    "viatra_service/app/domain/ports/hotel_availability_provider.py",
    "wms_service/wms_app/models/sales_order.py",
    "wms_service/wms_app/schemas/sales_order.py"
]

for file_path in files_to_fix:
    full_path = os.path.join(root_dir, file_path.replace("/", os.sep))
    if not os.path.exists(full_path):
        continue
        
    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Inject Decimal import if not exists
    if "from decimal import Decimal" not in content:
        # Find first import
        content = re.sub(r"^(import|from)\s", r"from decimal import Decimal\n\g<1> ", content, count=1)
        
    if "Numeric" not in content and "Mapped[float]" in content:
        content = re.sub(r"^(import|from)\s", r"from sqlalchemy import Numeric\n\g<1> ", content, count=1)
        
    # Replace Pydantic/Dataclass floats
    content = re.sub(r":\s*float(\s*=)", r": Decimal\1", content)
    content = re.sub(r":\s*float\s*\n", r": Decimal\n", content)
    content = re.sub(r"\[float\]", r"[Decimal]", content)
    
    # Replace SQLAlchemy Mapped[float]
    content = re.sub(r"Mapped\[float\]\s*=\s*mapped_column\(([^)]*)\)", r"Mapped[Decimal] = mapped_column(Numeric(18,4), \1)", content)
    content = re.sub(r"Mapped\[float\]\s*=\s*mapped_column\(\)", r"Mapped[Decimal] = mapped_column(Numeric(18,4))", content)
    
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
        
print("Mass float replacement completed.")
