# KIOSK SYSTEMS - Staff Operations Manual / Documentacion Tecnica
# Interno Core - Event Kiosk V1.0
# Generado: 2026-04-11 | Valle de Guadalupe Edition

---

## Resumen de Arquitectura

El Kiosko Fotografico de Interno Core es una aplicacion PWA de Angular 19
conectada a un backend FastAPI (kiosk-service) desplegado en una Mini PC Linux
con Mini PC ejecutando Docker Compose.

Componentes:
- kiosk-service   (FastAPI / Puerto 8020) - API central
- postgres-db     (Puerto 5433)           - Persistencia de fotos y ordenes
- minio           (Puerto 9000)           - Almacenamiento S3 local para fotos
- subscription-service (Puerto 8008)      - Monedero Paparazzi
- notification-service (Puerto 8009)      - Alertas en tiempo real
- auth-service    (Puerto 8001)           - Sesiones y tokens JWT

---

## MATRIZ DE CASOS DE USO V1.0

### 1. STAFF (El Operador de la Noche)

| Caso de Uso           | Ruta Frontend  | Endpoint Backend                      |
|-----------------------|----------------|---------------------------------------|
| Crear evento + logo   | /setup         | POST /onboarding/setup                |
| Confirmar pago cash   | /staff         | POST /payments/cash/confirm           |
| Ver galeria moderada  | /staff         | GET  /photos/gallery/{event_id}       |
| Eliminar foto urgente | /staff         | (pendiente: DELETE /photos/{id})      |

### 2. LOS NOVIOS (Los Curadores)

| Caso de Uso              | Ruta Frontend | Endpoint Backend                       |
|--------------------------|---------------|----------------------------------------|
| Modo Tinder (aprobacion) | /approval     | POST /photos/{id}/review               |
| Ver pendientes del mate  | /approval     | GET  /photos/pending-approval/{event}  |

### 3. EL INVITADO (El Paparazzi / Comprador)

| Caso de Uso              | Ruta Frontend | Endpoint Backend                       |
|--------------------------|---------------|----------------------------------------|
| Subir foto/video         | /camera       | POST /photos/upload-url                |
| Ver galeria aprobada     | /gallery      | GET  /photos/gallery/{event_id}        |
| Pagar con tarjeta/cash   | /checkout     | POST /payments/checkout                |

---

## FLUJO END-TO-END DE LA NOCHE

```
[STAFF] Setup del Evento
  -> POST /onboarding/setup
  -> Genera 3 QRs + Watermark en MinIO
  -> Imprime QRs y los distribuye

[INVITADO] Sube Foto
  -> POST /photos/upload-url   (obtiene presigned URL de MinIO)
  -> PUT  [MinIO presigned URL] (sube directo, sin pasar por FastAPI)
  -> foto.status = UPLOADED

[NOVIOS] Aprobacion Dual (Tinder Match)
  -> POST /photos/{id}/review  (GROOM)
  -> POST /photos/{id}/review  (BRIDE)
  -> Si ambos = true: foto.status = APPROVED
  -> Frontend lanza confetti

[INVITADO] Checkout
  -> POST /payments/checkout   (con photo_ids[], method=STRIPE|CASH)
  -> Si walletBalance >= total: status=COMPLETED, foto=PURCHASED
  -> Si Stripe: retorna stripe_client_secret para Stripe Elements
  -> Si Cash: retorna cash_qr_token

[STAFF] Confirma Pago Efectivo
  -> POST /payments/cash/confirm (escanea QR del invitado)
  -> foto.status = PURCHASED

[Print Worker - Background Daemon]
  -> Monitorea status=PURCHASED cada 5 segundos
  -> GET MinIO (foto original)
  -> Pillow: recorte 3:2 (formato 4x6 DNP)
  -> Pillow: alpha composite del watermark (esquina inferior derecha, 20% ancho)
  -> Save PDF 300DPI a /app/spool/{photo_id}_4x6.pdf
  -> Si CUPS conectado: enviar a cola de la impresora
  -> foto.status = DONE
```

---

## SISTEMA PAPARAZZI "10 a 1" - Mecanica de Creditos

### Como se ganan:
1. Invitado A sube foto de los novios bailando
2. Novios dan MATCH -> foto pasa a galeria publica
3. Invitado B compra esa foto por $50 MXN
4. Sistema deposita automaticamente $5 MXN (10%) al Monedero de Invitado A
   Endpoint: POST subscription-service/api/v1/wallet/award

### Como se usan:
1. Invitado A va a /checkout con su carrito de 1 foto ($50 MXN)
2. Activa "Usar Monedero" -> backend consulta balance
   Endpoint: GET subscription-service/api/v1/wallet/balance/{guest_session_id}
3. Si balance >= total: pago 100% con creditos, status=COMPLETED inmediato
4. Si balance < total: descuenta el saldo y cobra el diferencial con Stripe

### Puntos clave operativos:
- El guest_session_id es la "identidad" del invitado (asignada al escanear QR)
- El Monedero persiste toda la noche en subscription_db
- El Staff debe anunciar el mecanismo para generar viralidad interna

---

## 🌑 Protocolo de Despliegue en Entornos Sin Señal (Offline)

Si el evento es en un sótano o lugar sin internet, sigue este protocolo estrictamente para garantizar el candado verde SSL y el acceso rápido.

### 1. Preparación del Servidor (PC Core)
*   **Archivo Hosts**: Asegúrate de que `C:\Windows\System32\drivers\etc\hosts` contenga la línea:
    `127.0.0.1 momentos.com`
*   **Certificados**: Si la IP de la PC cambia, regenera los certificados:
    `mkcert momentos.com <NUEVA_IP> localhost`

### 2. Activación del Modo Offline
Ejecuta el script de control en una terminal de administrador:
```powershell
./modo_offline.ps1
```
*Este script liberará el puerto 53 y activará el servidor DNS interno.*

### 3. Configuración del Router (Hardware)
*   Conecta el Router Pro a la PC vía Ethernet.
*   En la configuración del Router, establece la IP de la PC como **DNS Primario** para todos los clientes (DHCP).

### 4. Configuración de Dispositivos (Invitados/Staff)
Si el router no redirige automáticamente, el usuario debe:
1.  Conectarse al Wi-Fi del evento.
2.  Cambiar los ajustes de IP de "DHCP" a **"Estático"**.
3.  Poner la IP de la PC en el campo **DNS 1**.
4.  Acceder a: `https://momentos.com:4200`

---

## 🛠️ Solución de Problemas (Troubleshooting)

| Problema | Solución |
| :--- | :--- |
| **Error SSL Rojo** | La PC y el celular no tienen la misma fecha/hora o los certificados no incluyen el dominio actual. |
| **URL no encontrada** | El puerto 53 está bloqueado. Ejecuta `modo_offline.ps1` como Administrador. |
| **Cámara bloqueada** | Estás entrando por `http` en lugar de `https`. El dominio DEBE ser seguro. |
| **Fotos no cargan** | El `kiosk-service` no está corriendo o el proxy de imágenes falló. Reinicia Docker. |

---

> [!IMPORTANT]
> **SEGURIDAD**: Nunca dejes el `modo_offline.ps1` activo después del evento, ya que bloquea el servicio de internet compartido de Windows. Presiona cualquier tecla en el script para restaurar la normalidad.

---

## RUTAS DE PRUEBA MANUAL (Frontend)

| URL                           | Descripcion                          | Estado    |
|-------------------------------|--------------------------------------|-----------|
| http://localhost:4200/setup   | Configuracion del evento + QRs       | [OK]      |
| http://localhost:4200/approval| Tinder Match (Novios)                | [OK]      |
| http://localhost:4200/checkout| Carrito + Stripe Elements + Wallet   | [OK]      |
| http://localhost:4200/staff   | Dashboard Staff (Bridalova Style)    | [OK]      |
| http://localhost:4200/gallery | Galeria publica (temporal)           | [PENDIENTE]|

## FLUJO DE PRUEBA MANUAL (Secuencia recomendada):

1. Abrir http://localhost:4200/setup
   - Poner nombre: "BodaCarlosYPaulina"
   - Precio: 50 MXN
   - Activar Paparazzi
   - Click "Crear Evento Oficial"
   - Guardar los 3 QRs generados

2. Abrir http://localhost:4200/approval
   - Seleccionar "Novio" y hacer swipe right (APPROVE)
   - Cambiar a "Novia" y hacer swipe right (APPROVE)
   - Validar confetti al completar el MATCH

3. Abrir http://localhost:4200/checkout
   - Validar suma de fotos del carrito
   - Activar/desactivar Monedero
   - Probar pago con tarjeta de prueba Stripe: 4242 4242 4242 4242

4. Abrir http://localhost:4200/staff
   - Validar feed de fotos aprobadas
   - Verificar metricas de ingresos en vivo

---

## PROBLEMAS CONOCIDOS Y SOLUCIONES

### MinIO - URLs internas en el navegador
Problema: Las presigned URLs generadas contienen "minio:9000" que el browser no resuelve.
Solucion: MINIO_PUBLIC_URL=http://localhost:9000 en .env y storage.py reescribe la URL.
Estado: [FIX APLICADO EN ESTA VERSION]

### kiosk_db no existe en postgres
Problema: postgres inicia sin la DB kiosk_db
Solucion: Añadida a init-multiple-databases.sh + create_tables() en @startup de FastAPI
Estado: [FIX APLICADO]

### Print Worker - CUPS en Windows (dev)
Problema: pycups no puede conectar a cups.sock en Windows
Solucion: Mock Mode activo en dev. El PDF se guarda en /app/spool/ automaticamente.
Estado: [MODO SIMULACION - Requiere Linux/Mini PC para produccion]
