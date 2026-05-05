# Changelog - Interno Core MES

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-03-14
### Added
- **Inventory Module**: Decomposed `InventoryEditor` with granular `Header`, `Table`, and `Footer` components.
- **Micro-interactions**: `ExcelNavigationDirective` for arrows and Enter/Shift+Enter matrix navigation.
- **Validation**: Forensic mass discrepancy tooltips and neon alerts.
- **Security**: Idempotency via `X-Client-Request-ID` and native UUIDv4 generation.
- **Infrastructure**: Environment configuration for microservice endpoints.
## [1.9.5] - 2026-03-30
### Added
- **Zero-Trust Physical Contexting**: Added global location awareness by transforming the module's main title into a robust Warehouse Selector.
- **Payload Assurance**: Intelligently populated backend-required properties (`uom_id` and semantic `company_id`) preventing 422 Unprocessable Entity routing crashes during Cross-Border transfers.
- **Architectural Blueprints**: Initiated plans for a Global Modal block covering the `/inventory` module entry point to govern Warehouse-level RBAC (Role-Based Access Control).
### Changed
- **UI Topology**: Flattened the Transfer Dashboard routing grid from a dual-panel configuration (Origin/Destination) into a unified Header-Origin and isolated Destination panel to maximize ledger barcode scanning estate on the viewport.

## [1.9.0] - 2026-03-30
### Added
- **Industrial Resilience**: Refactored `loadCatalogs` to use `Promise.allSettled()`. This guarantees the dashboard remains operational even if secondary catalogs (Categories/Brands) fail.
- **Silent Error Interception**: Implemented `X-Silent-Error` header handling to suppress "Critical System Failure" alerts for non-fatal metadata misses.
- **Improved Metadata Mapping**: Robust icon mapping for diverse movement naming conventions (`IN/OUT`, `ENTRY/EXIT`, `ENTRADA/SALIDA`).
### Fixed
- **UI Layering**: Resolved z-index occlusion issues in the header/dashboard interaction area.
- **Template Symmetry**: Optimized "Mission Control" title scaling for iPad Pro and high-density displays.
- **Operational Loops**: Added a direct "Back to Dashboard" exit path in the movement confirmation view.
### Changed
- **Header Aesthetics**: Transitioned to a minimalist, borderless "Catalog-style" company selector.

## [1.2.0] - 2026-03-15
### Added
- **Mission Control Resiliency**: Protected `forkJoin` operations in `InventoryService` catalog loading with individual `catchError` fallbacks.
- **Live Search Integration**: Replaced mock data in `ItemSearchComponent` with live `searchItems` API connection, heavily optimized using RxJS `debounceTime(300)` and `distinctUntilChanged`.
- **Kardex Pagination**: Enhanced the `SQLAlchemyInventoryRepository` to extract `total_count` via `func.count()` to feed dashboard metadata without breaking the limit/offset pipeline.

## [1.1.0] - 2026-03-14
### Added
- Initial project structure following Interno Core blueprint.
- Zoneless Angular 19 configuration.
- Core models for Multi-tenancy and Identity Triple.
- AuthService with 2-step handshake logic.
- AuthInterceptor for X-Company-Id and Authorization headers.
- Basic layout with Sidebar and Header.
