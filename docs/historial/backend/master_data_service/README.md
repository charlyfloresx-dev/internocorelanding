# 📦 Microservicio: Master Data Service

**Autor:** Backend Architect / DevOps
**Fecha:** 2026-02-12

## 1. Propósito del Microservicio

Este componente actúa como la **Single Source of Truth (SSOT)** de la plataforma, centralizando la definición de todas las entidades maestras. Su objetivo principal es asegurar la integridad referencial y técnica entre los diferentes módulos (como WMS y MES), garantizando que un producto o unidad de medida sea idéntico en todo el ecosistema.

## 2. Entidades Principales (Catálogos)
El servicio gestiona los diccionarios centrales del sistema:

- **Productos / SKUs:** Incluye definiciones técnicas, nombres, códigos de barras, pesos y dimensiones.
- **Unidades de Medida (UOM):** Gestiona el catálogo de unidades (KG, LB, UN) y sus factores de conversión (ej. pallets a cajas).
- **Categorías / Familias:** Clasificación jerárquica de productos.
- **Business Partners:** Directorio central de clientes y proveedores.
- **Conceptos Globales:** Monedas, impuestos y términos de pago.

## 3. Especificaciones Técnicas y de Integración

- **Arquitectura:** Implementado con FastAPI y SQLAlchemy 2.0 (Async), siguiendo los principios de Clean Architecture (Domain, Application, Infrastructure, API).

### Multitenancy Estricto
Todas las tablas heredan de `MultiTenantBase`, lo que obliga a filtrar cada consulta por `company_id` para garantizar el aislamiento total entre empresas.

### Versionamiento Paralelo
Soporta múltiples versiones de un producto activas simultáneamente. La clave lógica es la combinación de `(product_id, version_number)`.

### Patrón Sidecar (Sincronización Event-Driven)
- Al actualizar un dato maestro, el servicio publica un evento (ej. `product.updated`) vía RabbitMQ.
- Otros servicios (como el WMS) escuchan el evento y actualizan sus réplicas locales para mantener la alta disponibilidad.

## 4. Relación con el Ecosistema
- **Upstream:** Provee datos esenciales a servicios como el WMS (para inventarios) y el MES (para producción/BOM).
- **Dependencias:** Consume servicios del Auth Service para validar tokens JWT y obtener el contexto de la compañía.

## 5. Estado de Implementación (Auditoría)
- ✅ **Schemas:** Soporte completo para creación anidada (Producto + Versión).
- ✅ **Service Layer:** Manejo de transacciones atómicas y captura de `IntegrityError` (SKU duplicado).
- ✅ **Seguridad:** CORS configurado vía `ALLOWED_ORIGINS` y endpoints protegidos.
- ✅ **Modelos:** Implementados `Product`, `ProductVersion`, `ProductCategory`, `UM`.
- ✅ **Eventos:** Publicación asíncrona de `master_data.product.created`.

## 🛡️ Auditoría de Integridad
Para ejecutar el escaneo de violaciones de datos (Null Company IDs, Invalid Enums):
`docker compose exec master-data-service python -m app.scripts.integrity_scan`