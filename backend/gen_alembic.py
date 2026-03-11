import sys
import os

sys.path.insert(0, r"C:\API\interno\backend")
sys.path.insert(0, r"C:\API\interno\backend\mes_service")

from app.models import *
from common.models.base_models import Base

def generate_alembic_file():
    tables_to_create = [
        'mes_production_runs',
        'mes_downtime_events',
        'mes_labor_allocations',
        'mes_run_metrics_snapshots'
    ]
    
    upgrade_code = ""
    downgrade_code = ""
    
    for table_name in tables_to_create:
        table = Base.metadata.tables[table_name]
        upgrade_code += f"    op.create_table('{table_name}',\n"
        for col in table.columns:
            type_str = str(col.type)
            if "VARCHAR" in type_str:
                type_str = f"sa.String(length={col.type.length})"
            elif "INTEGER" in type_str:
                type_str = "sa.Integer()"
            elif "BOOLEAN" in type_str:
                type_str = "sa.Boolean()"
            elif "UUID" in type_str:
                type_str = "sa.UUID()"
            elif "DATETIME" in type_str:
                type_str = "sa.DateTime(timezone=True)"
            elif "DATE" in type_str:
                type_str = "sa.Date()"
            elif "NUMERIC" in type_str:
                type_str = f"sa.Numeric(precision={col.type.precision}, scale={col.type.scale})"
            else:
                type_str = f"sa.{col.type.__class__.__name__}()"
            
            nullable = f"nullable={col.nullable}"
            pk = "primary_key=True" if col.primary_key else ""
            default = f"server_default=sa.text('{col.server_default.arg}')" if col.server_default else ""
            
            args = [f"'{col.name}'", type_str, nullable]
            if pk: args.append(pk)
            if default: args.append(default)
            
            upgrade_code += f"        sa.Column({', '.join(args)}),\n"
        
        # Constraints logic
        if table_name == 'mes_production_runs':
            upgrade_code += "        sa.ForeignKeyConstraint(['resource_id'], ['mes_resources.id']),\n"
            upgrade_code += "        sa.ForeignKeyConstraint(['work_order_id'], ['mes_work_orders.id']),\n"
            upgrade_code += "        sa.UniqueConstraint('resource_id', 'date', 'shift_id', 'company_id', name='uq_production_run_schedule'),\n"
        elif table_name == 'mes_downtime_events':
            upgrade_code += "        sa.ForeignKeyConstraint(['production_run_id'], ['mes_production_runs.id']),\n"
        elif table_name == 'mes_labor_allocations':
            upgrade_code += "        sa.ForeignKeyConstraint(['production_run_id'], ['mes_production_runs.id']),\n"
        elif table_name == 'mes_run_metrics_snapshots':
            upgrade_code += "        sa.ForeignKeyConstraint(['production_run_id'], ['mes_production_runs.id']),\n"
        
        upgrade_code += "    )\n"
        for idx in table.indexes:
            columns = [c.name for c in idx.columns]
            upgrade_code += f"    op.create_index(op.f('{idx.name}'), '{table_name}', {columns}, unique={idx.unique})\n"
            
    for table_name in reversed(tables_to_create):
        table = Base.metadata.tables[table_name]
        for idx in table.indexes:
            downgrade_code += f"    op.drop_index(op.f('{idx.name}'), table_name='{table_name}')\n"
        downgrade_code += f"    op.drop_table('{table_name}')\n"
        
    alembic_path = r"C:\API\interno\backend\mes_service\alembic\versions\04dfb9667459_mes_models.py"
    with open(alembic_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    parts0 = content.split("def downgrade() -> None:")
    top_part = parts0[0].strip()
    # Find where to append inside upgrade
    
    with open(alembic_path, 'w', encoding='utf-8') as f:
        f.write(top_part)
        f.write("\n")
        f.write(upgrade_code)
        f.write("\n\ndef downgrade() -> None:\n")
        f.write(downgrade_code)
        f.write(parts0[1].strip() + "\n")

if __name__ == "__main__":
    generate_alembic_file()
