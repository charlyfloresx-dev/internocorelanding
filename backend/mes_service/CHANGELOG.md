# Changelog - mes_service

## [0.1.0] - 2026-02-14
### Added
- Inicialización del microservicio `mes_service` siguiendo el estándar `MANIFEST.md`.
- Modelos de manufactura completos (`Resource`, `Downtime`, `Labor`, `WorkOrder`, `Rout`, `OperationTime`, `KPI`, `Ledger`).
- Implementación de `ScannerService` con **Labor Guard** (Regla de Oro) y periodo de gracia de 10 min.
- Motor de KPIs (`KPIService`) con lógica de tendencias horarias (`ResourceGraphic`).
- Endpoints de API para Escaneo, Labor, Paros y Dashboard.

## [0.2.0] - 2026-02-14
### Added (MVP Focus)
- **Servicio de Turnos Dinámicos**: Resolución jerárquica (Empresa/Línea).
- **Escalación de Paros**: Monitor de 5 minutos para notificaciones críticas.
- **Ajuste de Capacidad (Staffing)**: Meta dinámica basada en registro de `Labor`.
- **Módulo de Planeación Nativo**: Sugerencia de producción basada en BOM y stock (WMS).
