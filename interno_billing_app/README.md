# 📱 InternoCore Mobile POS (Industrial Provisioning)

**InternoCore Mobile POS** es una aplicación de terminal de punto de venta (POS) de grado industrial diseñada para el ecosistema InternoCore. Permite a los operadores realizar ventas en tiempo real, gestionar inventarios mediante escaneo de códigos de barras y aprovisionar terminales de forma segura mediante el protocolo **Zero-Trust QR Handshake**.

---

## 🚀 Estado Actual: Fase 91 (Completada)

Actualmente, la aplicación soporta el flujo completo de **Aprovisionamiento Automático** y **Checkout Atómico**:

*   **Zero-Trust Provisioning**: Vinculación instantánea mediante escaneo de QR desde el portal web.
*   **Auto-Login**: Herencia de sesión (JWT) y contexto de empresa (Tenant) desde el administrador.
*   **Escaneo Industrial**: Resolución de SKUs en milisegundos contra el `master_data_service`.
*   **Checkout Atómico**: Registro de ventas como movimientos de salida (`OUT`) en el `inventory_service`.
*   **Setup Mode**: Acceso oculto para re-configuración (Long-press en logo de Login).

---

## 🛠️ Configuración del Entorno de Desarrollo

### 1. Requisitos Previos
*   **Flutter SDK**: `C:\API\Flutter\flutter\bin` (v3.38.5)
*   **Android SDK**: API 34 o superior.
*   **Backend InternoCore**: Corriendo en `localhost:8000` (o `10.0.2.2:8000` para emuladores).

### 2. Emulador Android (AVD)
Para probar el flujo de escaneo y aprovisionamiento en un entorno virtual:

1.  **Crear Dispositivo**: En Android Studio, crea un emulador (ej: `Interno_POS_Emu`) con API 34 (UpsideDownCake).
2.  **Iniciar desde Terminal**:
    ```powershell
    & "C:\Users\$env:USERNAME\AppData\Local\Android\Sdk\emulator\emulator.exe" -avd Interno_POS_Emu
    ```
3.  **Ejecutar App**:
    ```powershell
    cd c:\API\interno\interno_billing_app
    flutter run
    ```

### 3. Simulación de Escaneo (ADB Injection)
Como el emulador no tiene cámara física, puedes simular la lectura de un QR de aprovisionamiento o un producto:
```powershell
adb shell am broadcast -a com.google.zxing.client.android.SCAN --es SCAN_RESULT '{"baseUrl":"http://10.0.2.2:8000/api/v1","accessToken":"...","companyId":"...","warehouseId":"..."}'
```

---

## 🏗️ Arquitectura del Sistema

La aplicación sigue los principios de **Clean Architecture** y **BLoC** para la gestión de estados:

*   **`lib/core`**: Inyección de dependencias (`GetIt`), configuración de red (`Dio`) y temas.
*   **`lib/features/auth`**: Gestión de sesiones, login por PIN y aprovisionamiento QR.
*   **`lib/features/scanner`**: Lógica de cámara, búsqueda de productos y gestión del carrito.
*   **`lib/features/checkout`**: Resumen de venta y confirmación atómica en el backend.

### Protocolo de Vinculación (QR Payload)
El QR generado por el frontend web debe contener el siguiente esquema JSON:
```json
{
  "baseUrl": "URL_DEL_SERVIDOR",
  "accessToken": "JWT_VALIDO",
  "companyId": "UUID_EMPRESA",
  "warehouseId": "UUID_ALMACEN",
  "terminalName": "NOMBRE_IDENTIFICADOR"
}
```

---

## 📋 Plan de Implementación (Próximos Pasos)

1.  **Fase de Impresión**: Implementar la generación de recibos en PDF y soporte para impresoras térmicas Bluetooth (ESC/POS).
2.  **Persistencia Local**: Implementar un buffer offline para el carrito de compras.
3.  **Dashboard de Terminales**: Visualización de ventas por dispositivo en el portal administrativo.

---

## 🔐 Seguridad (Compliance)
*   **Multi-tenancy**: Todas las peticiones inyectan el header `X-Company-ID` y `Authorization`.
*   **Forensic Audit**: Cada venta registra el `terminal_name` en los comentarios de la transacción de inventario.
*   **RTR**: Rotación de tokens de refresco implementada para sesiones móviles persistentes.

---
*InternoCore Mobile POS - Diseñado por Carlos Flores Montoya (Antigravity Architecture).*
