# Manifiesto de Herramientas y Scripts (InternoCore)

Este directorio contiene scripts de automatización, diagnóstico y mantenimiento para el ecosistema InternoCore.

## 🛠️ Herramientas de Diagnóstico (Forensic Tools)
- **`check_db_monolith.py`**: Verifica la integridad de la base de datos del monolito, contando registros en tablas críticas (inventarios, notificaciones).
- **`check_charly_scopes.py`**: Diagnóstico de permisos (scopes) para el usuario principal en el sistema multi-tenant.
- **`check_notifs_db.py`**: Verifica específicamente la cola de notificaciones en la base de datos.
- **`test_auth.py`**: Prueba el flujo de obtención de headers JWT mediante la API de autenticación.
- **`test_sqla_keys.py`**: Script de prueba para validar la sintaxis y tipos de datos en modelos de SQLAlchemy.

## 🚀 Despliegue y Mantenimiento
- **`seed.py`**: Semilla maestra para poblar la base de datos con datos industriales iniciales.
- **`init_db.sh`**: Inicialización rápida del esquema de base de datos.
- **`audit_inventory_integrity.py`**: Auditoría profunda de discrepancias en niveles de inventario.
- **`rebuild_inventory_levels.py`**: Recalcula los stocks físicos basados en el historial de movimientos de documentos.
- **`deploy_auth_to_ecr.ps1`**: Automatización de subida de imagen de Auth Service a AWS ECR.
- **`modo_offline.ps1`**: Configura el entorno para desarrollo sin conexión a internet (Modo Avión).

## 🌍 Utilidades Especiales
- **`scrape_predial.py`**: Herramienta de consulta automática del Predial de Tijuana (Uso personal/administrativo).
- **`dns_server.py`**: Servidor DNS ligero para resolución de nombres en redes locales de prueba.
- **`scratch_run_gis.py`**: Validador de geolocalización y datos catastrales mediante el proveedor ArcGIS de Tijuana.
- **`run_kiosk.ps1`**: Orquestador para levantar el entorno de Kiosco/Evento en una terminal local.

## 🧪 Pruebas de Flujo (End-to-End)
- **`test_sales_flow.py`**: Simulación de una venta completa (Venta > Inventario > Notificación).
- **`walkthrough_test.py`**: Recorrido automatizado por las funcionalidades principales del sistema.
- **`test_audit.py`**: Verifica que las acciones se estén registrando correctamente en el log forense.

---
**Nota:** Los scripts duplicados o redundantes han sido eliminados durante la purificación de la Phase 98.
