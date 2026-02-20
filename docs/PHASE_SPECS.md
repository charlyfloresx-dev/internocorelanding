# 📋 Especificaciones Técnicas de Fases (Interno Core)

Detalle de ejecución para las fases de arquitectura pendientes.

## 🛑 Fase 19: Antigravity Auditor Mode
**Estado:** 🔄 En Ejecución
**Objetivo:** Verificar la integridad de los datos maestros tras el Seed.

### Acciones
1. Ejecutar `python -m app.scripts.integrity_scan`.
2. Generar reporte `integrity_scan_report.md`.

### Validación (Criterios de Éxito)
- ✅ Ningún `company_id` es NULL en tablas heredadas de `MultiTenantBase`.
- ✅ Todos los campos `status` coinciden con los enums en `common/enums.py`.

---

## 🌐 Fase 20: Sincronización On-Premise (Edge Buffer)
**Estado:** ⏳ Pendiente
**Objetivo:** Permitir que el sistema funcione On-Premise y se sincronice con AWS.

### Acciones
1. **Endpoint de Sincronización:** Crear `POST /api/v1/sync` en los microservicios.
2. **Idempotencia:** Implementar lógica para evitar duplicados si se reintenta la sincronización (Batch Idempotency).

### Validación
- ✅ Los datos creados en el ambiente On-Premise aparecen en AWS tras la ejecución del script de sync.

---

## 🔒 Fase 21: Final Security Audit
**Estado:** ⏳ Pendiente
**Objetivo:** Garantizar que un inquilino (Tenant) no vea datos de otro.

### Acciones
1. **Auditoría de Repositorios:** Revisar `common/repository.py` para asegurar que todo query incluya automáticamente el filtro `.filter(Model.company_id == current_company_id)`.
2. **Aislamiento de DTOs:** Validar que los esquemas de respuesta no expongan campos sensibles o de otros tenants.