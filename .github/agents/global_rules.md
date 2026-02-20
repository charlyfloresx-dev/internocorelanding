---
# 🤖 Reglas de Ejecución NexoSuite
Cada vez que un agente (Auth, Migration, Orquestador) inicie una tarea, DEBE:
1. Leer el `Protocolo.md` para asegurar compatibilidad On-Premise.
2. Antes de responder, generar un LOG DE ESTADO (Tareas de hoy, archivos afectados, bloqueos).
3. Actualizar el archivo `nexosuite_base/PROJECT_STATUS.md` al finalizar la tarea.