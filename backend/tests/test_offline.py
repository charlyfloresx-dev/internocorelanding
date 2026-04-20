import sys
import os

sys.path.insert(0, r"C:\API\interno\backend")
sys.path.insert(0, r"C:\API\interno\backend\mes_service")

from sqlalchemy import create_engine, MetaData
from alembic.autogenerate import compare_metadata, render_python_code
from alembic.migration import MigrationContext
from alembic.operations import ops

from app.models import *
from common.infrastructure.models.base import Base

def generate():
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        
        # We only want to print the 'mes_' tables, but sqlite memory is empty so it will yield ALL tables as added
        diff = compare_metadata(ctx, Base.metadata)
        
        upgrade_ops = ops.UpgradeOps(ops=diff)
        print("--- START ALEMBIC UPGRADE PIPELINE ---")
        print(render_python_code(upgrade_ops))

if __name__ == "__main__":
    generate()
