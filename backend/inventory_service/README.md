# 📦 Inventory Service (Port 8006)

El **Inventory Service** es el núcleo transaccional de Interno Core. Su responsabilidad es la gestión, trazabilidad y control de existencias en tiempo real a través de múltiples almacenes y localidades, asegurando la integridad del stock ante operaciones concurrentes.

## 1. Responsabilidades Principales
- **Control de Stock Real**: Gestión de cantidades disponibles, reservadas y en tránsito.
- **Transaccionalidad Atómica**: Registro de entradas, salidas y transferencias internas (ej. de WH-TIJ a WH-SDY).
- **Soporte Multi-tenant**: Aislamiento estricto de inventarios por `company_id`.
- **Validación de Reglas de Negocio**: Prevención de stock negativo y validación de capacidades por localidad.

## 2. Arquitectura Técnica
- **Framework**: FastAPI (Python 3.11+).
- **Patrones**: Clean Architecture + CQRS (Command Query Responsibility Segregation).
- **Base de Datos**: PostgreSQL (compartida en el cluster pero aislada lógicamente por esquema/tenant).
- **Integración**: Consumido principalmente por el WMS Service mediante un `InventoryClient` interno para operaciones de despacho y recepción.

## 🔧 Configuración de Entorno y PYTHONPATH
Para el correcto funcionamiento del servicio y la resolución de dependencias compartidas (`common`), se requiere la siguiente configuración:

```bash
PYTHONPATH=/app:/app/inventory_service
```

Esto permite que el código haga `from common.config import settings` y `from app.models import ...` sin conflictos de resolución.

## 🧪 Escenario de Demo: Empresa "Logistic"
El script `scripts/seed.py` inicializa el stock crítico para la operación binacional del demo:
- **Items**: MAT-001 a MAT-010 (Materiales de empaque y componentes).
- **Nodos**:
    - **Tijuana (WH-TIJ)**: Centro de producción con 100 unidades por item.
    - **San Diego (WH-SDY)**: Centro de distribución con 50 unidades por item.

## 🚀 Monitoreo
- **Health Check**: `/health` (vital para el monitoreo de estado del servicio).
