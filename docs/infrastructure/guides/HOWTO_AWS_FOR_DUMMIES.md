# 🎓 Guía AWS para Humanos (InternoCore Edition)

Esta guía explica cómo funciona nuestra infraestructura en la nube y cómo manejarla sin ser un experto en DevSecOps.

## 🧱 Las 3 Piezas del Puzzle
Nuestra aplicación vive en AWS Ohio (`us-east-2`) y se divide en 3 partes:
1.  **RDS (La Memoria):** Una base de datos PostgreSQL privada. No se puede acceder desde internet, solo desde nuestros servicios.
2.  **App Runner (El Motor):** Donde corre el código de Python (FastAPI). Se apaga solo si no hay tráfico (ahorro) y se escala si hay mucho.
3.  **CloudFront + S3 (El Escaparate):** Donde vive el Angular (Frontend). Es lo que el usuario ve primero.

---

## 🚀 Cómo "Levantar" el Sistema (De 0 a Pro)

### 1. Preparar la red (El túnel)
InternoCore usa una **VPC Privada**. Imaginalo como una red Wi-Fi de oficina muy segura. Para que el motor (App Runner) pueda leer la base de datos, necesita "túneles" llamados **VPC Endpoints**.
- **Script para usar:** `01_deploy_full_stack.ps1`
- **Qué hace:** Crea la red, los túneles y lanza el primer microservicio.

### 2. El Ciclo de Vida de Docker
Cuando cambias código en el backend:
1.  **Build:** Creas una "caja" (Imagen) con tu código.
2.  **Push:** Subes esa caja a **ECR** (el almacén de AWS).
3.  **Redeploy:** Le dices a App Runner: "Oye, usa la nueva caja que acabo de subir".

### 3. La "Mentalidad $0" (Hibernación)
Si vas a estar días sin trabajar en la nube, **NO DEJES NADA PRENDIDO**. RDS cobra por segundo.
- **Script para usar:** `99_nuke_everything.ps1`
- **Resultado:** Borra todo lo que genera gasto. Te deja en $0.00.

---

## 🛠️ FAQ (Preguntas Frecuentes)

**¿Por qué mi App Runner dice `CREATE_FAILED`?**
Casi siempre es porque no puede llegar a la base de datos o al Secreto. Revisa que los **VPC Endpoints** estén activos.

**¿Cómo accedo a la base de datos desde mi PC (DBeaver)?**
Como está en una subred privada, no puedes directamente. Necesitarías un "Bastion" o un túnel VPN. Por ahora, confía en los tests automatizados.

**¿Cuesta dinero tener el Frontend en S3?**
Casi nada. Solo pagas por los megas que los usuarios descargan. Lo que de verdad cuesta es RDS y App Runner cuando están "provisionales".

---

## 📜 Directorio de Poder
Todos tus comandos están en:
`backend/scripts/infraestructure_aws/`

1.  `01_deploy_full_stack.ps1`: Despliegue total.
2.  `99_nuke_everything.ps1`: Limpieza total.
3.  `service_config.json`: El "ADN" de tu configuración.
