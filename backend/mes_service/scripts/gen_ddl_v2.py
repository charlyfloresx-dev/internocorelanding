import sys
import os
from sqlalchemy import create_mock_engine
from sqlalchemy.schema import CreateTable, CreateIndex

# Setup path
sys.path.insert(0, os.getcwd())

from common.infrastructure.models.base import Base
import app.models # Ensure all models are registered

def dump(sql, *multiparams, **params):
    print(sql.compile(dialect=engine.dialect))

engine = create_mock_engine("postgresql://", dump)

print("-- DDL for ScrapEntry")
print(CreateTable(app.models.scrap_entry.ScrapEntry.__table__).compile(engine))

print("\n-- DDL for added columns in RunMetricsSnapshot")
# Note: This is simpler than full migration logic for a single column
from sqlalchemy import Column, Numeric
col = Column("quality", Numeric(5, 4), default=0.0)
print(f"ALTER TABLE mes_run_metrics_snapshots ADD COLUMN quality NUMERIC(5, 4) DEFAULT 0.0;")

print("\n-- DDL for rename and FK update in HourlyProductionSnapshot (Manual check)")
print("ALTER TABLE mes_hourly_production_snapshots RENAME COLUMN production_plan_id TO production_run_id;")
print("ALTER TABLE mes_hourly_production_snapshots DROP CONSTRAINT IF EXISTS mes_hourly_production_snapshots_production_plan_id_fkey;")
print("ALTER TABLE mes_hourly_production_snapshots ADD CONSTRAINT mes_hourly_production_snapshots_production_run_id_fkey FOREIGN KEY (production_run_id) REFERENCES mes_production_runs(id);")
