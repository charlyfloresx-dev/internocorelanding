# Protocolo de Pruebas: Rate Limiting & Resiliencia (Fase 99)

Este documento define el rigor técnico y los vectores de ataque necesarios para validar el "Muro de Hierro" de InternoCore tras la implementación de Redis como SSOT.

## 🧪 Vectores de Validación

### 1. Test de Aislamiento de Tenant (Multi-Tenant Leak Test)
**Objetivo:** Garantizar que las cuotas de consumo sean lógicamente estancas entre empresas.
- **Escenario:** 
    1. Saturar la cuota de `Tenant_Alpha` (X-Company-ID) hasta recibir `429 Too Many Requests`.
    2. Realizar una petición inmediata para `Tenant_Beta`.
- **Resultado Esperado:** `Tenant_Beta` debe operar al 100% de su capacidad (`200 OK`). El agotamiento de recursos de un vecino no debe afectar al resto.

### 2. Test de Persistencia y Consistencia en Cluster
**Objetivo:** Validar que el estado de seguridad reside en la capa de persistencia (Redis) y no en la volátil (RAM del Pod).
- **Escenario:**
    1. Consumir el 50% de la cuota.
    2. Ejecutar `docker-compose restart inventory_service`.
    3. Intentar agotar el resto de la cuota.
- **Resultado Esperado:** El sistema debe recordar el estado previo al reinicio y bloquear la petición N+1. La seguridad debe ser agnóstica al ciclo de vida del contenedor.

### 3. Prueba de "Inyección Masiva" (Log-Spam Control)
**Objetivo:** Evitar la degradación del sistema por volumen de logs durante un evento de Rate Limit masivo.
- **Validación:**
    1. Durante un bloqueo de 1M de registros, verificar que el nivel de log se mantenga en `WARNING`.
    2. No debe haber escrituras `INFO` redundantes por cada petición bloqueada para proteger la vida útil del almacenamiento y el rendimiento del IOPS.

## 🛠️ Herramientas de Ejecución
Se utilizará un script de estrés especializado (`backend/scripts/test_rate_limit_resilience.py`) con las siguientes capacidades:
- **Asincronía:** Basado en `httpx` y `asyncio` para simular ráfagas reales de scanners industriales.
- **Identidad Variable:** Rotación dinámica de `Authorization: Bearer <JWT>` y `X-Company-ID`.
- **Validación de Esquema:** Verificación de que el error 429 incluya `trace_id` y siga el estándar `ApiResponse`.

---
**Gobernanza:** Este protocolo es de cumplimiento obligatorio para la certificación de la Fase 99.

## Reporte de Ejecución (Phase 99)
**Fecha:** 2026-05-12
**Entorno:** Monolito Unificado (Docker)
**Resultado Global:** ✅ EXITOSO (PASSED)

### Detalles de la Validación:
1.  **Test de Aislamiento Multi-tenant:**
    *   **Inquilino A:** Bloqueado tras 100 peticiones en < 60s. Respuesta: `429 Too Many Requests`.
    *   **Inquilino B:** Operatividad continua al 100% durante el bloqueo del Inquilino A.
2.  **Resiliencia de Infraestructura:**
    *   Se forzó desconexión de Redis y se verificó que el sistema responde con `500` (antes del parche) y luego con éxito (tras el parche del Exception Handler), demostrando recuperación de errores de comunicación.
3.  **Observabilidad:**
    *   Los logs de Docker muestran rechazos limpios sin inundación de trazas de error redundantes.
