# InternoCore: Plan de Implementación Fase 4 (Consolidación AWS y Producción)
**Fecha:** 2026-05-12
**Status:** DRAFT

## 1. Visión General
Tras alcanzar el estado de madurez arquitectónica con un Muro de Hierro infranqueable (RLS), segregación CQRS, e inmutabilidad financiera (100% CLEAN en Code Graph Auditor), el sistema transiciona a la Fase 4. El objetivo fundamental es preparar y desplegar la infraestructura para un entorno de Alta Disponibilidad (HA) nativo en AWS, asegurando latencia mínima, escalamiento dinámico y seguridad Zero-Trust en la nube.

## 2. Hallazgos de la Auditoría Inicial (Deployment Readiness)
Tras revisar `docker-compose.yml`, `backend/docker/Monolith.Dockerfile` y los Dockerfiles de los microservicios (ej. `backend/auth_service/Dockerfile`):

- **Usuario No-Root:** ✅ **CUMPLIDO.** Los contenedores ya están configurados para correr bajo el usuario restringido `app`.
- **Contexto de Construcción (Shared Kernel):** ✅ **CUMPLIDO.** Copian correctamente `/common` garantizando disponibilidad de Value Objects.
- **Docker Multi-Stage Builds:** ❌ **DEUDA TÉCNICA.** Actualmente los Dockerfiles usan un solo "stage". Dejan librerías de compilación de SO (`build-essential`, `gcc`) en la imagen final, comprometiendo tamaño y superficie de ataque.
- **Healthchecks para ALB:** ❌ **DEUDA TÉCNICA.** Falta instrucción `HEALTHCHECK` nativa y/o rutas robustas de `/health` alineadas con los Target Groups del AWS ALB.

## 3. Plan de Ejecución AWS

### Fase 4.1: Fortalecimiento de la Containerización (Docker Hardening)
1. **Migración a Multi-Stage Builds:** Refactorizar todos los Dockerfiles de los microservicios y el monolito para separar la etapa de `builder` (donde se instalan dependencias y librerías C) de la etapa `runner` (imagen final ultraligera de distroless o alpine).
2. **Inyección de Healthchecks:** Proveer un endpoint unificado `/health` que no solo devuelva HTTP 200, sino que valide de forma asíncrona la conectividad con la DB Postgres y Redis. Integrar `HEALTHCHECK CMD curl --fail http://localhost:8000/health || exit 1` en el Dockerfile.
3. **Optimización de Entrypoint:** Garantizar que los scripts efímeros (`entrypoint.sh`) soporten interrupción SIGTERM (Graceful Shutdown) crucial para el reciclaje de instancias ECS Fargate.

### Fase 4.2: La Fortaleza VPC (Topología de Red de 3 Capas)
La arquitectura de red aplica Defensa en Profundidad estricta para confinar el radio de exposición.
1. **Capa Pública (DMZ):**
   - Único punto de entrada desde Internet vía puerto 443 (HTTPS).
   - Contiene el **Application Load Balancer (ALB)** (con WAF habilitado) y **NAT Gateways**.
   - **SG-ALB:** Acepta tráfico 0.0.0.0/0 al puerto 443.
2. **Capa Privada (Application Tier):**
   - Subredes sin IP pública, donde corren los contenedores **ECS Fargate**.
   - Acceso a internet controlado vía NAT Gateway (para descargas y APIs externas como Stripe).
   - **VPC Endpoints (Privatelink):** Enrutamiento directo a Secrets Manager y ECR sin atravesar internet pública (ni siquiera el NAT), reduciendo latencia y vectores de exfiltración.
   - **SG-ECS:** Solo admite tráfico proveniente del SG-ALB (Healthchecks y peticiones de la API) en el puerto de la aplicación (8000).
3. **Capa de Datos (Isolated Tier):**
   - Aislamiento absoluto. Contiene **Amazon RDS (Postgres)** y **ElastiCache (Redis)**. Sin enrutamiento hacia NAT ni IGW.
   - **SG-RDS:** Rechaza cualquier conexión directa, aceptando única y exclusivamente tráfico (puertos 5432 y 6379) cuyo origen sea el SG-ECS. Administradores solo pueden acceder vía Bastion Host o Session Manager.

### Fase 4.3: Orquestación Serverless, CI/CD y Estrategia de Persistencia
1. **Amazon ECR:** Repositorios de imágenes con `ScanOnPush` para interceptar vulnerabilidades.
2. **Amazon ECS Fargate:** Escalabilidad nativa sin gestión de servidores subyacentes.
3. **Estrategia de Persistencia (Alembic):** 
   - Las migraciones no correrán en el contenedor de la API principal ni en la máquina del desarrollador.
   - Se levantará una **ECS Task Efímera** pre-despliegue dentro de la Capa Privada. Esta Task inyecta las migraciones SQL a través del entorno aislado y se apaga sola. Si la tarea falla, el pipeline aborta el despliegue de las nuevas APIs.
4. **Inyección de Secretos:** Integración dinámica con **AWS Secrets Manager** vía VPC Endpoint, inyectando credenciales como variables de entorno ocultas sin tocar archivos `.env`.

## 4. Criterios de Aceptación (Definición de "Terminado")
- [ ] AWS VPC configurada con 6 subredes en 2 Zonas de Disponibilidad (AZs).
- [ ] Security Groups entrelazados (ALB -> ECS -> RDS).
- [ ] Dockerfiles transformados a arquitectura Multi-Stage, reduciendo al menos 40% del peso de las imágenes y blindando la seguridad.
- [ ] ECS Fargate ejecutando y manteniendo vivo el backend mediante el `/health` del Application Load Balancer.

## 5. Próximos Pasos (Inmediatos)
- **Aprobar y Ejecutar 4.1:** Procederé a reescribir los Dockerfiles para implementar Multi-Stage Builds y agregar el estándar de Healthcheck. ✅ (COMPLETADO)

## 6. Tareas Pendientes (Hold por Cuenta AWS)
Las siguientes tareas quedan en espera de la activación de la cuenta AWS y se ejecutarán mediante Infraestructura como Código (Terraform/CloudFormation):
- **Creación de VPC y Subredes:** Desplegar DMZ, App Tier, y Data Tier.
- **Configuración de VPC Endpoints:** Crear endpoints para ECR y Secrets Manager.
- **Creación de Security Groups:** SG-ALB, SG-ECS y SG-RDS.
- **Aprovisionamiento de Servicios Base:** Amazon RDS (PostgreSQL) y ElastiCache (Redis).
- **Setup de Application Load Balancer (ALB):** Con su respectivo Target Group, Healthchecks (`/health`) y WAF.
- **Despliegue ECR y ECS:** Creación de repositorios de imágenes y Task Definitions efímeras (Alembic) y permanentes (APIs).
