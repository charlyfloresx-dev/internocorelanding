# Plan de Implementación Maestro - 2026-05-12

## Objetivo: Cloud Decommissioning & Infrastructure Serialization
Asegurar el cierre definitivo de la cuenta de AWS minimizando el riesgo de costos residuales y preservando la capacidad de redespacho.

## Arquitectura Ejecutada
### 1. Fase de Extracción (ADN)
- Se utilizó `aws ec2 describe-vpcs` y `describe-subnets` para capturar la topología de la VPC `NexoSuite-Production-VPC`.
- Se capturaron los permisos del "Muro de Hierro" mediante `aws iam list-policies`.

### 2. Fase de Neutralización (Audit)
- **Causa del Goteo de Costos**: Se identificó que Secrets Manager seguía cobrando por el secreto de producción a pesar de no haber instancias activas.
- **Acción**: Borrado forzado (`--force-delete-without-recovery`) para detener el cargo inmediatamente.

### 3. Fase de Desacoplamiento (Account Agnostic)
- Se rediseñó el script de despliegue para eliminar la dependencia de IDs estáticos. El nuevo script `deploy_to_new_aws_account.ps1` utiliza parámetros dinámicos, permitiendo que InternoCore sea portable entre diferentes cuentas de AWS.

### 4. Fase de Higiene (Zero-Trust)
- Implementación de un `vault/` local ignorado por Git. Esto permite que el desarrollador conserve las llaves maestras en su máquina local para emergencias sin riesgo de exposición en el repositorio central.

## Decisiones Técnicas Clave
- **Local-First SSOT**: Se determinó que el entorno local es ahora la única fuente de verdad, suspendiendo cualquier sincronización automática con la nube hasta nuevo aviso.
- **Parametrización Estricta**: Se prohibió el uso de ARNs con IDs de cuenta fijos en los nuevos scripts de infraestructura.

---
**Firmado:** Antigravity AI Systems Architect
