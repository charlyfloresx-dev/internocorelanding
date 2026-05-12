# Guía de Despliegue Frontend (Low Cost + OAC)

Esta guía detalla el despliegue del frontend de InternoCore en AWS usando S3 y CloudFront con Origin Access Control (OAC), lo que garantiza costo cero de transferencia interna y seguridad total.

## 1. Infraestructura Existente (us-east-2)

- **S3 Bucket**: `interno-core-frontend-prod` (Bloqueo público total activo).
- **CloudFront Distribution**: `E23YTJF59L1IKO`.
- **Domain**: `d3b47jx48onn9j.cloudfront.net`.
- **OAC ID**: `E27N8VA0H5ZXJC`.

## 2. Flujo de Despliegue Manual

### Paso 1: Generar el Build de Angular
Ejecuta el build optimizado para producción:
```bash
npm run build -- --configuration production
```

### Paso 2: Sincronizar con S3
Sube los archivos al bucket privado. **Nota:** No es necesario poner los archivos como públicos, OAC se encarga de la lectura.
```bash
aws s3 sync ./dist/browser s3://interno-core-frontend-prod --delete
```

### Paso 3: Invalidar Cache
Para que los cambios (especialmente en el "God Mode") sean instantáneos, invalida el cache de CloudFront:
```bash
# Vía PowerShell
.\scripts\invalidate_cache.ps1

# Vía Bash
./scripts/invalidate_cache.sh
```

## 3. Manejo de SPA (Single Page Application)
La distribución está configurada con **Custom Error Responses**:
- **404 -> /index.html (200 OK)**
- **403 -> /index.html (200 OK)**

Esto permite que las rutas de Angular (ej. `/dashboard`, `/inventory`) funcionen correctamente al recargar la página.

## 4. Política de Seguridad (OAC)
El bucket `interno-core-frontend-prod` tiene una política que solo permite el acceso si el `SourceArn` coincide con la distribución de CloudFront. Esto evita que los bots escaneen tu contenido directamente desde S3.
