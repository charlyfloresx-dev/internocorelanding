# 🏗️ InternoCore: Infrastructure & Orchestration

Este directorio es el centro neurálgico de la infraestructura de InternoCore. Contiene todas las configuraciones necesarias para desplegar, monitorear y escalar el ecosistema en diferentes entornos (Local, On-Premise, Edge y Cloud).

---

## 📂 Mapa del Centro de Mando

### 1. `docker/` (Desarrollo y Microservicios)
Es el stack preferido para el desarrollo ágil y granular.
- **Propósito**: Aislar servicios (Auth, Inventory, WMS) para trabajar en ellos de forma independiente.
- **Gateway**: Puerto **8000** (Unificador).
- **Workers**: Procesamiento asíncrono (Outbox, SLAs) via `docker-compose.workers.yml`.
- **Guía Detallada**: Ver [docker/README_DEV.md](./docker/README_DEV.md).

### 2. `onprem/` (Monolito Industrial)
Configuración para despliegues en servidores locales de almacenes o centros de distribución.
- **Propósito**: Máximo rendimiento, un solo proceso de Uvicorn orquestando todos los módulos en memoria.
- **Uso**: Simulación de producción y despliegues finales en hardware local.
- **Guía Detallada**: Ver [onprem/README_ONPREM.md](./onprem/README_ONPREM.md).

### 3. `terraform/` (Infraestructura como Código - Cloud)
Contiene los Blueprints para desplegar el stack en **AWS**.
- **Componentes**: VPC, ECS (Fargate), RDS (Postgres), y ALB.
- **Uso**: Despliegues automatizados en la nube.

### 4. `telemetry/` (Observabilidad)
Configuraciones para el monitoreo del sistema.
- **Stack**: Prometheus, Grafana y Loki.
- **Uso**: Visualización de métricas industriales y logs centralizados.

### 5. `aws/` & `localstack/`
Configuraciones para servicios específicos de la nube.
- **`init-aws.sh`**: Scripts para inicializar buckets S3, colas SQS y tablas DynamoDB localmente usando LocalStack.

---

## 🕹️ Matriz de Decisión de Entorno

| Necesidad | Recomendación | Puerto Gateway | Comando de Inicio |
| :--- | :--- | :--- | :--- |
| **Desarrollar Frontend / Móvil** | `docker/` (Core) | `8000` | `docker compose -f ... up -d auth master inventory gateway` |
| **Debuggear un Microservicio** | `docker/` (Full) | `8001 - 8009` | `docker compose -f ... up -d [servicio]` |
| **Pruebas de Carga / Producción** | `onprem/` | `8000` | `docker compose -f ... up -d` |
| **Simular AWS localmente** | `localstack` | `4566` | `docker compose -f docker-compose.localstack.yml up -d` |

---

## 🧼 Mantenimiento y Salud

Para mantener la infraestructura sana, utiliza los workflows del agente en `.agent/workflows/`:
- **`hard-reset.md`**: Limpieza total de imágenes, volúmenes y redes.
- **`initialize-dev.md`**: Arranque rápido de microservicios esenciales.

> [!IMPORTANT]
> Nunca edites los archivos `.yml` directamente en la raíz a menos que sea para orquestación global. Toda la lógica de red debe vivir dentro de sus respectivos subdirectorios para evitar colisiones.
