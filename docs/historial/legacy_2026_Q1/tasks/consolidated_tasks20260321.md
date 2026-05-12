# Consolidated Tasks - 2026-03-21

## Completado Hoy
- [x] Refactorizar `CurrencyService` en Master Data Service hacia Clean Architecture.
- [x] Abstraer persistencia con `ICurrencyRepository` y clientes externos con `ICurrencyClient`.
- [x] Aislar modelo propio `CurrencyExchangeRate` para evitar fugas desde `common`.
- [x] Reescribir el middleware in-service `get_current_user_payload` para decodificar y validar rígidamente JWT contra `X-Company-ID`.
- [x] Validar pruebas iter-tenant para Cross-Service Price Fetching (Bloqueo efectivo con Status 403).
- [x] Generar reportes Code Graph y asegurar cero violaciones activas de Invariantes.
- [x] **WMS Deep Cleaning**: Integración de `Money` VO en `InventoryMovement`, `ProductPrice`, `InventoryLevel` y `Movement`.
- [x] **WMS Precision**: Actualización de `Item.stock_quantity` a `Numeric(18, 4)` y uso de `Decimal`.
- [x] **God Mode**: Implementación de Router Administrativo en `auth_service`, `master_key` verification y `handshake` endpoint.
- [x] **Tenant Bypass**: Refactorización de `TenantSecurityMiddleware` para soportar claim `bypass_tenant: true`.

## Tareas Pendientes Inmediatas (Siguiente Fase)

### Despliegue AWS (Próximo Hito)
- [ ] Configurar Repositorios ECR para microservicios `auth_service`, `inventory_service` y `wms_service`.
- [ ] Configurar Bucket S3 y Distribución CloudFront para el Frontend Angular.
- [ ] Implementar GitHub Actions para CI/CD hacia AWS.
- [ ] Validar conectividad de base de datos RDS desde containers ECS.
