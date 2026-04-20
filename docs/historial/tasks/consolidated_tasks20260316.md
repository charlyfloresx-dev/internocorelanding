# 📋 Consolidated Tasks (Daily Snapshot: 2026-03-16)

---

### ✅ Completed Today
- **[x] Value Object Consolidation**: 
  - Integrado el Value Object `Money` al servicio de Inventarios.
  - Generadas las migraciones de Alembic para el Value Object `Money` (`scripts/migrate_schema.py`).
  - Refactorizado `TransferCommandHandler` para acceder correctamente a `transfer.unit_price.amount` en reemplazo de los accesos planos al ORM.
- **[x] Seguridad y Multitenancy**:
  - Implementado Blindaje Zero-Trust usando solo los claims de los JWT para filtar `company_id`.
  - Corregidos roles de acceso público (`/api/v1/admin/demo-reset`).
- **[x] Flujo de Inter-Company Transfer (ICT)**:
  - Validado y pulido el flujo end-to-end de los 4 pasos (Despacho físico, Almacén Lógico en Tránsito, Recepción Física, y Cancelación).
  - Integridad matemática calculada y testeada con éxito en `test_intercompany_flow.py` (Adquisición Destino = Qty * Precio Pactado Sellado).
- **[x] Debugging de Docker/Microservicios**:
  - Unificados imports intra-capa agregando archivos `__init__.py` recursivamente en `inventory_service` para subsanar los `ModuleNotFoundError` bajo el entorno `PYTHONPATH` de Docker.

---

### ⏳ Pendientes / Próximos Pasos (Backlog)

#### Frontend (Angular)
- **[ ] Gatekeeper de Preparación (APP_INITIALIZER / Guard)**: El frontend debe consumir la información de Setup Mínimo (Empresa, Moneda, Warehouses) antes de pintar el Dashboard de Inventarios. Si no, debería inyectar un Stepper Opcional o mostrar Skeleton.
- **[ ] Manejo Dinámico de Almacenes In-Transit**: Asegurar que la pantalla de inventarios no mezcle almacenes físicos con almacenes de tránsito lógicos (uuid5).
- **[ ] Visualización de la Vista "Documento Espejo"**: Presentar el borrador entrante (`IN-ICT-20260316-...`) para que Empresa B apruebe y dispare la "Recepción".

#### Deployment / SRE (AWS)
- **[ ] Subir Imágenes ECR**: Empaquetar y versionar `auth-service`, `inventory-service` y `master-data-service`.
- **[ ] Desplegar Frontend SPA en AWS S3 & CloudFront**: Configurar las rules 403/404 -> `index.html` para enrutamiento Angular, habilitar TLS 1.2/1.3.
- **[ ] Secret Manager**: Validar the `config.py` en AWS ECS para leer llaves `aws_secret_access_key` en producción.
