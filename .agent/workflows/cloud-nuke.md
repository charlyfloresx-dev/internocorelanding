---
description: Cloud Janitor — Kill Switch (Nuke AWS to $0.00)
---

Este workflow ejecuta el **Kill Switch** de infraestructura para desmantelar todos los recursos de AWS y evitar costos inesperados.

> [!CAUTION]
> Esta operación es **IRREVERSIBLE**. Se eliminarán servicios, bases de datos y registros.

### 1. Ejecutar Nuke to Zero // turbo
Ejecuta el script de limpieza profunda para eliminar App Runner, VPC Endpoints, RDS y S3.
```powershell
powershell -ExecutionPolicy Bypass -File backend/scripts/infraestructure_aws/99_nuke_everything.ps1
```

### 2. Verificar Estado de Facturación
- Entrar a la consola de AWS Billing.
- Confirmar que no hay servicios `Running` en **us-east-2**.

### 3. Sincronizar Documentación de Estado
Actualiza el estado de la infraestructura en el log global:
```powershell
# Este comando es manual, actualiza INFRASTRUCTURE_STATE.md a "LOCAL ONLY"
```

Notes:
- Objetivo: Mantener la factura en $0.00 durante periodos de inactividad local.
- Para volver a desplegar, utiliza el workflow de `redeploy`.
