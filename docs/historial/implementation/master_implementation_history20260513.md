# InternoCore: Historia de Implementación Maestra (2026-05-13)

## Arquitectura de Persistencia Idempotente (Phase 105)

### 1. El Problema: DuplicateTableError
Al desplegar en entornos compartidos o tras ejecuciones de `Base.metadata.create_all()`, las migraciones iniciales de Alembic fallaban al intentar recrear tablas existentes. Esto bloqueaba el registro de la versión actual en la tabla `alembic_version`.

### 2. La Solución: Zero-Trust Migrations
Se implementó un patrón de idempotencia en las migraciones críticas:
```python
def table_exists(name):
    from sqlalchemy import inspect
    ins = inspect(op.get_bind())
    return name in ins.get_table_names()

def upgrade():
    if not table_exists('users'):
        op.create_table(...)
```
Esto permite que Alembic "marque" la versión actual como `head` sin fallar si la infraestructura ya está en el estado deseado.

### 3. Auditoría de Esquema (Schema Auditor)
Se añadió una capa de introspección a `generate_code_graph.py` que:
1. Lee los modelos SQLAlchemy definidos en el código.
2. Consulta el esquema real en `public` de PostgreSQL.
3. Reporta discrepancias de columnas (faltantes, tipo incorrecto).

### 4. Parcheo Industrial (Phase 83 - Physical Locations)
El modelo `InventoryLocation` tenía una deuda técnica de 16 columnas necesarias para el "Density Guard" (unidades, peso, volumen, direccionamiento jerárquico). Se consolidó en la migración `c83f_phase83` del `inventory_service`.

### 5. Resiliencia del Gateway (Monolito Lite)
El Gateway (Nginx) ahora es compatible con el stack de desarrollo limitado. Se eliminaron las dependencias de resolución de nombres para servicios no desplegados, permitiendo que el punto de entrada unificado (Puerto 8000) esté operativo de inmediato.

## Decisiones Clave
- **Aislamiento de Alembic**: Cada servicio mantiene su propia tabla de versiones (`alembic_version_auth`, `alembic_version_inv`, etc.) para evitar colisiones en la DB compartida `dbname`.
- **Patrón de Parcheo**: Se prefiere el uso de migraciones formales de Alembic sobre scripts SQL directos para mantener la trazabilidad del ADN infraestructural.
