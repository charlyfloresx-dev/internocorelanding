# InternoCore: Consolidated Tasks - 2026-05-03

## Backlog Superado (Completado)
- [x] **Unificación de Monolito**: Estabilización de namespaces y ruteo unificado en puerto 8000.
- [x] **Density Guard (Phase 83)**: Implementación de validación de 3 capas (Unidades, Peso, Volumen).
- [x] **Soft-Block Logic**: Configuración de desbordamiento de unidades como alerta (warning) no bloqueante.
- [x] **Unified Industrial Seed**: Creación de orquestador maestro para inicialización de entornos.
- [x] **FIFO & Anexo 24**: Automatización de descarga de saldos aduaneros en movimientos de salida.
- [x] **WMS Layout**: Sembrado de 33 locaciones industriales con direccionamiento jerárquico.
- [x] **Operational Walkthrough**: Validación de flujo completo (Login -> Contexto -> Put-Away Queue).
- [x] **Forensic Audit Engine**: Implementación de `AuditService` con persistencia de snapshots JSONB.
- [x] **SSOT Model Consolidation**: Centralización de `InventoryLocation` en `common` para evitar `DuplicateTableError`.
- [x] **Audit Traceability**: Registro obligatorio de cada acción de inicialización en el Ledger Forense.

## Pendientes (Backlog Próximo)
- [ ] **Handheld UI Implementation**: Finalizar componentes de escaneo para la terminal móvil.
- [ ] **Picking Optimization**: Implementar lógica de sugerencia de rutas (S-Shape vs Largest Gap).
- [ ] **Volumetric Guard Hardening**: Completar dimensiones físicas de todos los productos en el catálogo maestro.
- [ ] **Landed Cost Engine**: Iniciar el motor de costeo para valorización real de inventarios.

## Decisiones Críticas
1. **Unidades vs Peso**: Se decidió que el peso es un factor de seguridad física (Hard Block), mientras que las unidades son un factor de eficiencia (Soft Block con advertencia).
2. **Master Seed**: Se adoptó la estrategia de SSOT (Single Source of Truth) para todos los IDs de catálogos base.
