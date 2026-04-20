# Lecciones Aprendidas - Despliegue AWS Auth Service
**Fecha**: 2026-04-17  
**Fase**: Industrializacion AWS - Despliegue ECS Fargate + RDS Ohio  
**Autor**: Carlos Flores (con asistencia de Antigravity AI)

---

## Resumen Ejecutivo

Durante la sesion de industrializacion del `auth_service` en AWS (us-east-2), se identificaron y resolvieron una cadena de 5 bloqueos criticos que impidieron la conectividad entre el contenedor ECS Fargate y la base de datos RDS PostgreSQL. Este documento captura cada leccion para que no se repita en futuros microservicios.

---

## Leccion 1: El Formato del Secreto en Secrets Manager es Critico

**Problema**: Al crear el secreto inicial con `aws secretsmanager create-secret`, el `--secret-string` fue ingresado desde PowerShell sin comillas dobles alrededor de las llaves JSON. Resultado: el valor almacenado era un diccionario Python-like, no un JSON valido.

**Sintoma**: `json.loads()` fallaba silenciosamente al parsear el secreto.

**Solucion**: Siempre crear secretos desde un **archivo JSON externo** con `--secret-string file://payload.json`. Nunca ingresar JSON complejo directamente en la CLI de PowerShell.

```powershell
# MAL - PowerShell rompe las comillas y el &
aws secretsmanager put-secret-value --secret-string '{"key": "val&ue"}'

# BIEN - Siempre usar un archivo
aws secretsmanager put-secret-value --secret-string file://payload.json
```

**Archivos afectados**: `backend/auth_service/secret_payload.json`

---

## Leccion 2: Pydantic BaseSettings es Inmutable Post-Instanciacion

**Problema**: La arquitectura inicial intentaba cargar los secretos de AWS DESPUES de que `InternoSettings()` habia sido instanciada, luego usaba `setattr()` para actualizar los campos. 

**Sintoma**: `setattr()` parecia funcionar (no lanzaba error), pero SQLAlchemy/Alembic usaban el motor de base de datos construido en tiempo de import con los valores default (`db:5432`). El campo Pydantic no propagaba el cambio al motor ya construido.

**Raiz Tecnica**: En Pydantic v2, aunque `model_config` no tenga `frozen=True`, las dependencias que ya fueron calculadas a partir de un campo (como un `create_engine()` llamado durante la instanciacion del modulo) no se recalculan cuando el campo cambia posteriormente.

**Solucion**: Inyectar las variables de entorno ANTES de que Python arranque. El `entrypoint.sh` ahora extrae los secretos de AWS con `aws cli` y los exporta como variables de entorno del shell. Cuando Python arranca, Pydantic los lee directamente desde el ambiente del proceso.

```sh
# entrypoint.sh - CORRECTO
export DATABASE_URL=$(aws secretsmanager get-secret-value ... | python3 -c "...")
export CORE_DATABASE_URL="$DATABASE_URL"
python -m alembic upgrade head  # Ahora Pydantic lee el env var correcto
```

**Archivos afectados**: `backend/auth_service/entrypoint.sh`

---

## Leccion 3: El Entorno `aws` vs `production` - Inconsistencia de Nomenclatura

**Problema**: El codigo de `common/config.py` verificaba `if self.int_environment.lower() != "production"` para decidir si cargar secretos de AWS. La Task Definition de ECS estaba configurada con `CORE_ENV_MODE=aws` (no `production`).

**Sintoma**: Los secretos nunca se cargaban porque `"aws" != "production"`.

**Solucion**: Expandir la validacion para aceptar multiples valores equivalentes:
```python
env = self.int_environment.lower()
if env not in ["production", "prod", "aws"]:
    return  # skip
```

**Leccion General**: Definir un vocabulario controlado de entornos ANTES de comenzar el despliegue y documentarlo en el `README.md` de cada servicio. Para InternoCore: `development | staging | aws | production`.

**Archivos afectados**: `backend/common/config.py`

---

## Leccion 4: El NAT Gateway en Estado `blackhole` Bloquea la Resolucion DNS

**Problema**: Las subredes privadas de la VPC tenian rutas hacia un NAT Gateway en estado `blackhole` (el NAT fue destruido, pero las rutas persistieron). Cualquier trafico de salida desde subredes privadas era descartado silenciosamente.

**Diagnostico**:
```
"DestinationCidrBlock": "0.0.0.0/0",
"NatGatewayId": "nat-13d4e32b310c81988",
"State": "blackhole"  // <- ESTE ES EL PROBLEMA
```

**Impacto**: Los contenedores ECS ubicados en subredes privadas no podian resolver DNS externo ni conectarse a Secrets Manager o RDS por nombre de host.

**Solucion Inmediata**: Mover los contenedores ECS a subredes **publicas** (con `assignPublicIp: ENABLED`) hasta que el NAT Gateway sea reemplazado.

**Solucion Permanente**: Recrear el NAT Gateway y actualizar las tablas de rutas de las subredes privadas, O usar VPC Endpoints para Secrets Manager y ECR (mas seguro y sin costo de NAT).

---

## Leccion 5: Verificar el ID de VPC antes de Diagnosticar

**Problema**: Al auditar los atributos DNS de la VPC, se uso un VPC ID de una sesion anterior que no existia en la region `us-east-2`. El error `InvalidVpcID.NotFound` se confundio inicialmente con un problema de permisos.

**Sintoma**:
```
An error occurred (InvalidVpcID.NotFound) when calling the DescribeVpcs operation
```

**Solucion**: Siempre obtener el VPC ID dinamicamente antes de cualquier auditoria:
```powershell
aws ec2 describe-vpcs --region us-east-2 --query "Vpcs[?Tags[?Key=='Name']].VpcId" --output text
```

---

## Leccion 6: El `socket.gaierror` Puede Mentir Sobre la Causa Real

**Problema**: El error `socket.gaierror: [Errno -2] Name or service not known` fue interpretado inicialmente como un problema de DNS de la VPC. En realidad, el problema era que el hostname en la URL era `db` (el valor default de Docker Compose), no el endpoint real del RDS.

**Investigacion que revelo la verdad**: Agregar un `print` del hostname antes del crash:
```python
print(f"INFO: Database Hostname to resolve: '{parsed.hostname}'", flush=True)
```
Output: `INFO: Database Hostname to resolve: 'db'` — ¡la URL nunca habia cambiado!

**Leccion**: Ante cualquier error de red, lo PRIMERO es verificar que el valor que se esta usando sea el correcto, no asumir que la infraestructura tiene el problema.

---

## Flujo de Diagnostico Recomendado para Futuros Microservicios

```
1. Verificar que el secreto en Secrets Manager es JSON valido
   -> aws secretsmanager get-secret-value --secret-id ... | python3 -c "import json,sys; print(json.load(sys.stdin))"

2. Verificar que el env CORE_ENV_MODE coincide con la logica de carga
   -> aws ecs describe-task-definition --task-definition ... | grep ENV_MODE

3. Agregar print del hostname ANTES de cualquier conexion de DB
   -> print(f"Connecting to: {parsed.hostname}", flush=True)

4. Verificar el estado de las rutas de la VPC
   -> aws ec2 describe-route-tables --filters "Name=vpc-id,Values=VPC_ID"

5. La solucion definitiva: inyectar secretos en el shell, no en Python
   -> entrypoint.sh: export DATABASE_URL=$(aws secretsmanager ...)
```

---

## Estado Final de la Sesion

| Componente | Estado |
|---|---|
| Secreto en AWS Secrets Manager | JSON valido con DNS correcto del RDS |
| common/config.py | Acepta entornos `aws`, `prod`, `production` |
| auth_service/entrypoint.sh | Inyeccion shell pre-boot implementada |
| ECS Task IAM Role | `secretsmanager:GetSecretValue` verificado |
| VPC DNS | `enableDnsHostnames` y `enableDnsSupport` = true |
| **Pendiente** | Validar que el nuevo entrypoint conecta exitosamente con RDS |

---

## Leccion 7: El Costo del ALB es Incompatible con Startups en Fase Semilla

**Problema**: El Application Load Balancer (ALB) tiene un costo base de ~$16.20 USD/mes + ~$3.60 USD por cada IPv4 publica que utiliza (minimo 2 para HA). Esto suma ~$23.40 USD/mes antes de procesar un solo request.

**Sintoma**: El presupuesto de $5.00 USD de "Interno Core" se vio superado en la primera semana de pruebas, con un forecast de $6.64 USD proyectado para el dia 20.

**Solucion**: Pivotar hacia **AWS App Runner**. 
- App Runner incluye su propio balanceador y gestion de certificados SSL sin costo base adicional.
- Permite escalar a casi cero (solo pagas por memoria cuando no hay trafico) o usar instancias de 0.25 vCPU / 0.5 GB.
- **Accion Realizada**: Eliminacion inmediata del ALB y Target Groups el 2026-04-20.

**Leccion General**: En etapas de desarrollo pre-semilla, el ALB es un lujo innecesario. Los servicios totalmente gestionados (PaaS) como App Runner son mas "bolsillo-friendly" y reducen la complejidad de la red (VPC).

---

*Documento actualizado el 2026-04-20 tras la crisis del presupuesto de $5 USD.*
