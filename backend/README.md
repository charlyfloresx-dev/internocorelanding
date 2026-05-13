# ⚙️ InternoCore Backend Workspace

> **Nota:** Este directorio contiene el código fuente de todos los microservicios que conforman el ecosistema InternoCore. Aunque operan como módulos independientes, en entornos de desarrollo local se despliegan bajo un **Monolito Unificado** compartiendo la misma red y base de datos de Docker.

---

## 🏗️ Estándar de Construcción de Microservicios (Gold Standard)

Para garantizar consistencia, evitar colisiones en la base de datos unificada y asegurar que cada contenedor sea autónomo, **todo nuevo microservicio debe seguir rigurosamente esta estructura y reglas**:

### 1. Topología Estricta
Cada servicio debe estar encapsulado en su propia carpeta terminada en `_service`:

```text
backend/<module>_service/
├── Dockerfile          # CRÍTICO: Debe invocar entrypoint.sh vía CMD ["/bin/sh", "/app/entrypoint.sh"]
├── entrypoint.sh       # Secuencia obligatoria: Migrate -> Seed -> Serve
├── requirements.txt    # Dependencias estrictamente necesarias para el servicio
├── alembic.ini         # Configuración local de migraciones (para autogenerate)
├── alembic/            
│   └── env.py          # CRÍTICO: Debe definir un 'version_table' único.
├── scripts/            
│   └── seed.py         # Opcional: Inyección de datos maestros (debe ser idempotente)
└── <module>_app/       # CRÍTICO: Nombrado explícito (Prohibido usar la palabra genérica 'app')
    ├── main.py         # Instancia FastAPI y registro de Routers
    ├── core/           # Configuración (Pydantic Settings) e inyección de dependencias
    ├── models/         # Modelos SQLAlchemy (Heredan de common.models.MultiTenantBase)
    ├── routers/        # Controladores API (Endpoints RESTful)
    ├── schemas/        # Validadores Pydantic (DTOs entrada/salida)
    └── services/       # Lógica de negocio (Donde reside la inteligencia real)
```

### 2. Reglas de Oro (Zero-Collision)

Debido a que operamos en un modelo "Local-First Monolith" (donde múltiples microservicios comparten la instancia `interno-db-dev`), debes aplicar los siguientes blindajes:

#### A. Aislamiento de Historial de Alembic
Si usas las tablas por defecto, todos los servicios sobrescribirán el registro de versiones. En tu archivo `alembic/env.py`, debes forzar un nombre de tabla único:

```python
# alembic/env.py
def do_run_migrations(connection):
    context.configure(
        connection=connection, 
        target_metadata=target_metadata,
        version_table="alembic_version_<nombre_modulo>" # <-- ¡CRÍTICO!
    )
    # ...
```

#### B. Nombres de Módulos (No más `app`)
Nunca llames a tu carpeta de código fuente simplemente `app/`. Si tienes dos servicios con la misma carpeta, Python se confundirá en el PYTHONPATH al compartir el contenedor en desarrollo. Usa el sufijo `_app`:
✅ `auth_app/` 
✅ `inventory_app/`
❌ `app/`

#### C. Entrypoint Autónomo (Auto-Bootstrap)
Tus contenedores no deben requerir que un humano ejecute scripts manuales para funcionar. Usa un `entrypoint.sh` en la raíz de tu servicio:

```bash
#!/bin/sh
echo ">> [1/3] Ejecutando migraciones Alembic..."
python -m alembic upgrade head || echo "⚠️ Alembic falló. Continuando..."

echo ">> [2/3] Ejecutando seed de datos (si existe)..."
if [ -f "scripts/seed.py" ]; then
    python scripts/seed.py || echo "⚠️ Seed falló. Continuando..."
fi

echo ">> [3/3] Iniciando Servidor..."
exec uvicorn <module>_app.main:app --host 0.0.0.0 --port 8000
```

### 3. Código Compartido (`common/`)
Si necesitas modelos base (ej. `AuditBase`), middlewares de validación de Tenant o utilidades comunes, impórtalos de la carpeta `backend/common/`. 

> **Advertencia:** No modifiques `common/` para agregar lógica específica de tu microservicio. `common/` es estrictamente para herramientas transversales.
