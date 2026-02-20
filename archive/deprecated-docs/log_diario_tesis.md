# Log Diario de Tesis - Proyecto InternoCore

---

### **Fecha:** 2026-01-06

#### Tareas Realizadas:
- Se migró el sitio estático de un endpoint HTTP (S3) a un endpoint **HTTPS** utilizando una distribución de **AWS CloudFront**.
- Se configuró el **Origin Access Control (OAC)** con ID `E2BIZMIE1-0VI63` para securizar el acceso al bucket S3.
- Se corrigieron errores en el archivo de configuración de la distribución (`distribution.json`) para asegurar el despliegue.
- Se validó el acceso correcto al sitio a través de la URL `https://d2m14uxf7tlfyw.cloudfront.net`, confirmando la visibilidad en dispositivos móviles.

#### Tareas Pendientes:
1.  **(Prioridad Alta)** Iniciar la creación del esquema y las tablas en la base de datos RDS `internocore-auth-db`.
2.  **(Prioridad Media)** Desarrollar la lógica de negocio para la autenticación de usuarios en Python, conectando con la nueva base de datos.

#### Comandos Críticos para Referencia Futura:

**1. Actualizar Frontend en S3:**
```bash
aws s3 cp c:\API\interno\index.html s3://internocore-static-files-3709/
```

**2. Invalidar Caché de CloudFront:**
```bash
aws cloudfront create-invalidation --distribution-id d2m14uxf7tlfyw --paths "/index.html"
```

---
*Este log se actualizará automáticamente al final de cada sesión para mantener un historial de auditoría de la infraestructura de AWS.*
