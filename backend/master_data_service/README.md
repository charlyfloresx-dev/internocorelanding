# 🗂️ Master Data Service (Port 8003)

El **Master Data Service** actúa como la Única Fuente de Verdad (SSOT) para las entidades maestras que consumen los demás módulos (Ventas, Compras, Inventarios).

## 🎯 Responsabilidad
Gestión centralizada de:
- **Productos**: Definición base, SKU e identificación.
- **Unidades de Medida (UOM)**: Estándares de conversión y empaque.
- **Categorías y Marcas**: Clasificación jerárquica del catálogo.

## 🏛️ Arquitectura de Datos
- **Catálogos Híbridos**: Permite registros globales (`company_id IS NULL`) creados por el sistema y registros privados por tenant (`company_id = UUID`).
- **Optimistic Locking**: Implementado mediante `version_id` en todos los modelos para evitar colisiones en actualizaciones concurrentes.
- **Inmutabilidad de Auditoría**: Todo registro persiste `created_at`, `updated_at`, `created_by` (UUID) y `transaction_id`.

## 🛡️ Seguridad y Gobernanza
- **Zero Trust Tenancy**: El `company_id` se extrae exclusivamente de tokens verificados.
- **Identidad del Sistema**: Los registros de infraestructura utilizan el `SYSTEM_USER_ID`: `00000000-0000-0000-0000-000000000000`.
- **Integración**: Los servicios externos (ej. Inventarios) deben consumir estos datos vía API (Puerto 8003) o consultas de solo lectura si comparten el clúster de base de datos.
