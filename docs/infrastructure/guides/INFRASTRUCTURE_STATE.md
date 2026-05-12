# 🌐 InternoCore: Estado de la Infraestructura Cloud (CUENTA CERRADA)

## 📊 Estatus Actual: **❄️ CRIO-ESTADO (Account Closed / $0.00)**
A partir del **2026-05-12**, la cuenta de AWS `584094645491` ha sido cerrada definitivamente tras una auditoría forense exitosa. El sistema reside ahora exclusivamente en el **Monolito Unificado Local**.

### 🛑 Acción de Cierre (Audit results):
- **Secrets Manager:** Secreto de producción en `us-east-2` eliminado.
- **S3:** Bucket residual `nexosuite-logs-and-backups-3709` borrado.
- **IAM:** Access Key `AKIAYP7WA7TZ4J3VBER4` desactivada.
- **ADN:** Configuración exportada a `backup_configs/`.
- **Registro:** Repositorios ECR purgados.

---

## 🏗️ Guía de Resurrección (Despliegue en Nueva Cuenta)
Cuando se decida volver a la nube, consulte la **[Guía de Resurrección](AWS_RESURRECTION_GUIDE.md)**. Se han actualizado los scripts para soportar cuentas nuevas sin IDs hardcodeados.

### 🚀 Pasos de Emergencia
1. **Fase 0:** Crear nueva cuenta AWS y configurar CLI.
2. **Despliegue:** Ejecutar el script universal parametrizado:
```powershell
.\backend\scripts\deploy_to_new_aws_account.ps1 -AccountId "NUEVO_ID"
```

### 📂 Archivos de Referencia
- **Guía Maestra:** `docs/infraestructura/AWS_RESURRECTION_GUIDE.md`
- **ADN Técnico:** `docs/infraestructura/backup_configs/` (VPC, IAM, CloudFront JSONs)

---

## 🏛️ Referencia de Red (VPC)
- **VPC ID:** `vpc-0be05235bbfedf785` (NexoSuite-Production-VPC)
- **Subredes:** `subnet-04e7fcf2d855dbb96`, `subnet-0611bd3d756934140`, `subnet-0fab7c07f6e31e1c7`
- **Security Groups:** 
  - `sg-0a151d7b5d8e8bcf0` (RDS/App Runner Default)
  - `sg-0ea0c22fd4462c731` (VPC Endpoints SG)

## ⚠️ Lección Aprendida (Fase 65)
**NUNCA** desplegar App Runner en subredes privadas sin **Interface Endpoints** para `secretsmanager`. El freeze del bootstrap se debió al aislamiento del contenedor intentando resolver el API público de AWS sin ruta de salida.
