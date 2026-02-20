# 📑 InternoCore: Master Protocol (v3.0 - Hybrid Edition)

## 🎯 1. Resumen de Funcionamiento (The Vision)
InternoCore es una plataforma **Multi-tenant** diseñada para operar en dos modalidades:
1.  **Cloud SaaS:** Operada por nosotros en AWS para múltiples empresas.
2.  **Corporate On-Premise:** Instalada en servidores privados del cliente para una sola empresa o grupo corporativo.

* **Frontera de Datos:** En cualquier modalidad, el `company_id` sigue siendo obligatorio para permitir futuras migraciones de datos entre local y nube.

---

## 🤝 2. Roles y Directivas de Despliegue

1.  **Agente de Autenticación:** Debe permitir configuraciones de "Single Tenant" donde solo exista una empresa maestra, pero manteniendo la estructura de roles y permisos.
2.  **Orquestador:** Responsable de mantener dos "recetas":
    * **Receta AWS:** Terraform/CloudFormation + RDS + S3.
    * **Receta Local:** Docker Compose + MySQL Local + MinIO (S3 Local).
3.  **Migrador:** El código generado en `internocore_base/` debe ser **"Provider Agnostic"**. No puede usar librerías exclusivas de AWS que no tengan un equivalente local.

---

## 📂 3. Contexto de Rutas y Estructura
**Raíz del Proyecto:** `INTERNO/`

* **Configuración:** `./config/` (Contendrá `production.env` y `local.env`).
* **Despliegue:** `./docker/compose-corporate.yml` (Para clientes locales).

---

## 🛠️ 4. Estándares para Clientes Corporativos (On-Premise)

* **Stateless Obligatorio:** Nada se guarda en el disco local del contenedor. Todo va a la DB o al almacenamiento de objetos (S3/MinIO).
* **Abstracción de Almacenamiento:** Se usará el protocolo S3. En la nube apuntamos a AWS; en local, el Orquestador levantará un contenedor de **MinIO**.
* **Base de Datos:** Los microservicios deben soportar cualquier instancia de **MySQL 8.0+**, ya sea administrada (RDS) o en contenedor.

---

## 🚦 5. Flujo de Trabajo (Híbrido)

1.  **Prioridad:** El **Auth Architect** debe crear un "Flag" de configuración: `MULTI_TENANT_MODE=True/False`.
2.  **Validación:** Cada microservicio en `internocore_base` debe pasar una prueba de "Local-Only" (correr sin internet) antes de ser aprobado para clientes corporativos.

---

## 🏛️ 6. Gobernanza y Supervisión (The Supervisor)

Para asegurar la coherencia del proyecto, se establece la figura del **Supervisor Agent** [.github/agents/Supervisor.agent.md]. Sus directivas son:

1.  **Auditoría de Cumplimiento:** Antes de dar por terminada una tarea de cualquier agente, el Supervisor debe validar que se respetó la Clean Architecture y el Multi-tenancy.
2.  **Sincronización de Dependencias:** El Supervisor bloqueará al **Migrador** si detecta que intenta avanzar en un módulo sin que el **Auth Architect** haya definido primero los permisos y roles correspondientes.
3.  **Validación Híbrida:** El Supervisor rechazará cualquier propuesta técnica que sea exclusiva de la nube y que no tenga una alternativa funcional para despliegues **On-Premise** (Corporativos).
4.  **Reporte de Verdad Única:** En caso de conflicto entre lo que propone el Orquestador y el Migrador, el Supervisor decidirá basándose estrictamente en este Protocolo.

---

## 📅 7. Ritual de Inicio (Daily Sync)

Cada sesión de trabajo debe iniciar consultando al **Supervisor** con el siguiente comando:
> "Dame el estado de sincronización actual. ¿Hay algún agente desviándose del protocolo o bloqueando el progreso de los demás?"