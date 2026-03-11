import sys
import os
from sqlalchemy import create_mock_engine
from sqlalchemy.schema import CreateTable

# Setup path
sys.path.insert(0, os.getcwd())

from common.models import Base
import app.models # Ensure all models are registered

def dump(sql, *multiparams, **params):
    print(sql.compile(dialect=engine.dialect))

engine = create_mock_engine("postgresql://", dump)

print("-- DDL for BOM")
print(CreateTable(app.models.bom.BOM.__table__).compile(engine))

print("\n-- DDL for BackflushError")
print(CreateTable(app.models.backflush_error.BackflushError.__table__).compile(engine))
