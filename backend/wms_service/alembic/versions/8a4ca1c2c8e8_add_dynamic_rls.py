"""Add Dynamic RLS

Revision ID: 8a4ca1c2c8e8
Revises: 43a7412121f6
Create Date: 2026-05-12 15:07:52.467147

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8a4ca1c2c8e8'
down_revision: Union[str, None] = '43a7412121f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Creamos una función de ayuda en Postgres para simplificar las políticas
    op.execute("""
        CREATE OR REPLACE FUNCTION get_current_tenant() RETURNS uuid AS $$
            BEGIN
                RETURN current_setting('app.current_tenant', True)::uuid;
            EXCEPTION WHEN OTHERS THEN
                RETURN NULL;
            END;
        $$ LANGUAGE plpgsql STABLE;
    """)

    # 2. Bloque dinámico para activar RLS en todas las tablas con company_id
    op.execute("""
        DO $$ 
        DECLARE 
            r RECORD;
        BEGIN
            FOR r IN (
                SELECT table_name 
                FROM information_schema.columns 
                WHERE column_name = 'company_id' 
                AND table_schema = 'public'
                AND table_name NOT LIKE 'alembic_%'
            ) LOOP
                -- Activar RLS en la tabla
                EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', r.table_name);
                
                -- Forzar RLS incluso para el dueño de la tabla (Sello de Calidad de InternoCore)
                EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', r.table_name);
                
                -- Eliminar política si ya existe (idempotencia)
                EXECUTE format('DROP POLICY IF EXISTS tenant_isolation_policy ON %I', r.table_name);
                
                -- Crear la política de aislamiento
                EXECUTE format(
                    'CREATE POLICY tenant_isolation_policy ON %I USING (company_id = get_current_tenant())', 
                    r.table_name
                );
                
                RAISE NOTICE 'RLS activado para la tabla: %', r.table_name;
            END LOOP;
        END $$;
    """)

def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP FUNCTION IF EXISTS get_current_tenant CASCADE;")
