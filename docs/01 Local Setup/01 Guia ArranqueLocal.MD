# 🛠️ Guía de Arranque Local - InternoCore

Esta guía detalla los pasos para poner en marcha el ecosistema de InternoCore en sus diferentes modalidades. Dependiendo de tu objetivo (Desarrollo ERP o Eventos en Sitio), deberás elegir un modo de ejecución.

---

## 🏛️ 1. Modo InternoCore (ERP Industrial / Full Stack)
Este es el modo principal que levanta toda la infraestructura de microservicios para la gestión empresarial, inventarios, RH y logística.

### Servicios Incluidos:
- **Auth Service** (8001)
- **Inventory & WMS** (8006, 8007)
- **Master Data** (8003)
- **HR & Tickets** (8009, 8004)
- **MES & Currency** (8005, 8008)
- **Frontend Angular** (8080)

### Comando de Arranque:
Desde la raíz del proyecto, ejecuta:
```powershell
docker compose up -d
```

### Acceso:
- **Frontend:** [http://localhost:8080](http://localhost:8080)
- **API Docs:** [http://localhost:8001/docs](http://localhost:8001/docs) (Auth)

---

## 📸 2. Modo Kiosco (Event Management - eventKiosk)
Este modo está optimizado para dispositivos locales (Mini-PCs) en eventos físicos. Es un ecosistema ligero que prioriza la velocidad de captura, aprobación y procesamiento de imágenes.

### Servicios Incluidos:
- **Kiosk Service** (8020) - Motor principal de eventos y procesamiento de fotos.
- **MinIO** (9000/9001) - Almacenamiento local de ultra-alta velocidad (S3 compatible).
- **Kiosk DB** (5433) - Base de datos aislada para eventos.
- **Print Daemon** - Conectividad nativa con impresoras DNP/Hiti vía CUPS.

### Comando de Arranque:
Utiliza el script automatizado que detecta tu IP de red para permitir la conexión de dispositivos móviles:
```powershell
.\scripts\run_kiosk.ps1
```

---

## 📡 3. Modo Offline (Pruebas en Sitio)
Si estás en un entorno sin internet y necesitas que los celulares se conecten al servidor local mediante el dominio `momentos.com`, utiliza este modo.

### Requisitos:
1. Ejecutar PowerShell como **Administrador**.
2. Haber configurado el DNS del dispositivo móvil a la IP de la PC host.

### Comando de Arranque:
```powershell
.\scripts\modo_offline.ps1
```
*Este script liberará el puerto 53 de Windows y activará un servidor DNS interno que redirige todo el tráfico de `momentos.com` a tu máquina local.*

---

## 🏢 4. Consideraciones On-Premise (Instalación en Sitio)
Para instalaciones físicas en bodegas o locaciones de eventos, se deben seguir estos criterios de industrialización:

### 🌐 Red y Conectividad
- **IP Estática:** Se recomienda configurar una IP estática en el host (ej. `192.168.1.100`) para evitar que los dispositivos pierdan conexión al reiniciar el router.
- **Firewall:** Asegúrate de permitir el tráfico entrante en los puertos:
    - `53` (DNS - Solo para Modo Offline)
    - `80`, `443` (HTTP/S)
    - `8080` (Frontend)
    - `9000`, `9001` (MinIO API/Console)

### 🔐 Seguridad y Certificados (SSL Local)
InternoCore utiliza HTTPS incluso en modo local para garantizar el funcionamiento de PWA y Service Workers.
- El sistema busca certificados en `c:\API\interno\certs`.
- Usamos el dominio local `momentos.com` mediante el script de DNS interno.

### 🖨️ Integración de Hardware (Impresoras/Lectores)
- **CUPS (Linux/Mini-PC):** El `kiosk-service` se comunica con el socket de CUPS para lanzar impresiones directas a equipos DNP o Hiti.
- **Lectores RFID/Scanner:** Se integran vía emulación de teclado o por el puerto serie mapeado en Docker.

### 💾 Persistencia de Datos
Los datos se almacenan en volúmenes de Docker. Para respaldos preventivos en sitio:
```powershell
# Ejemplo de backup rápido de la DB de Kiosko
docker exec kiosk-postgres pg_dump -U user dbname > setup_backup.sql
```

---

## ⚠️ Solución de Problemas (Troubleshooting)

### Conflicto de Puertos
Si recibes errores de "Port already in use":
1. Verifica que no tengas otra instancia de Postgres corriendo en el puerto `5433`.
2. Detén servicios de IIS o Apache que puedan estar usando el puerto `80`.

### Re-generar Base de Datos
Si necesitas limpiar los datos y empezar de cero:
```powershell
docker compose down -v
docker compose up -d
```

### Ver Logs de un Servicio
```powershell
docker logs -f kiosk-image-service
```

---
> **Nota de Gobernanza:** Prohibido crear archivos en la raíz. Toda herramienta nueva debe alojarse en `scripts/` y documentarse aquí.
