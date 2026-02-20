# 🤖 PROTOCOLO PARA AGENTES: MANTENIMIENTO DE CONTEXTO

Este documento define las reglas que debe seguir cualquier agente que trabaje en InternoCore para evitar la degradación de la documentación.

## 📌 Reglas de Oro
1. **SSOT Primero:** Antes de programar, lee `INTERNOCORE_CONTEXTO_UNICO.md`.
2. **Actualización Post-Cambio:** Si cambias un endpoint, un modelo o terminas una tarea, **DEBES** actualizar el Contexto Único inmediatamente.
3. **No Duplicar:** No crees nuevos archivos de LOG o CHECKLIST si la información puede consolidarse en el Contexto Único.

## 🔄 Dónde actualizar según el cambio:

| Si cambias... | Archivo a modificar | Sección específica |
| :--- | :--- | :--- |
| Un Endpoint o JSON | `INTERNOCORE_CONTEXTO_UNICO.md` | Sección 2 (Arquitectura) o Sección 4 (Checklist) |
| Una lógica de Angular | `frontend/ENGINEERING_LOG.md` | Registro de versiones |
| Una decisión técnica | `LOG.md` | Bitácora diaria |
| Una tarea del Checklist | `INTERNOCORE_CONTEXTO_UNICO.md` | Sección 4 (Checklist) |

## 🛠️ Comandos de Verificación
Siempre verifica que el flujo de Tenancy no se rompa:
1. `F12 > Network`: ¿Está el header `X-Company-Id` presente?
2. `F12 > Application`: ¿El `interno_auth_ctx` tiene el ID correcto?

---
*Instrucción final: Al terminar tu turno, resume el progreso y actualiza el Checklist en el documento maestro.*