# 📱 InternoCore Sentinel Mobile — Industrial POS & Warehouse Terminal

**InternoCore Sentinel Mobile** es una aplicación industrial de grado operacional diseñada para el ecosistema InternoCore. Combina funcionalidad de terminal de punto de venta (POS), gestión de inventarios mediante escaneo de códigos de barras, y una interfaz estilo Uber para operadores de almacén. El aprovisionamiento seguro se realiza mediante el protocolo **Zero-Trust QR Handshake**.

---

## 🚀 Estado Actual: Fase 115 — POS Payment Confirmation & Simulated Ticketing

La aplicación soporta el flujo completo de **Aprovisionamiento Automático**, **Checkout Atómico**, **Navegación Industrial Uber-Style**, **Resolución de Variantes en Tiempo Real** y **Confirmación de Pago (Tickets)**:

*   **Zero-Trust Provisioning**: Vinculación instantánea mediante escaneo de QR desde el portal web. Botón de estado "Dispositivo Vinculado" visible tras configuración exitosa.
*   **Auto-Login + Company/Warehouse Selection**: Flujo completo de Handshake → Selección de Empresa → Selección de Almacén → Dashboard.
*   **Uber-Style Navigation**: 5 tabs principales: Inicio, Descubrir, Ganancias, Buzón (Notificaciones), Menú (Tickets de Soporte).
*   **Escaneo Industrial**: Resolución de SKUs en milisegundos contra el `inventory_service` (variantes incluidas) localmente vía SQLite Drift.
*   **Checkout Atómico y Pagos**: Pantalla dedicada de confirmación de pagos con métodos (Efectivo/Tarjeta/Transferencia), referenciación a App/Terminal, y simulación de impresión térmica.
*   **Resilience Interceptor**: Reintentos exponenciales con idempotency keys bajo redes inestables.
*   **Setup Mode**: Acceso oculto para re-configuración (Long-press en logo de Login).

---

## 🛠️ Configuración del Entorno de Desarrollo

### 1. Requisitos Previos
*   **Flutter SDK**: `C:\API\Flutter\flutter\bin` (v3.38.5)
*   **Android SDK**: API 34 o superior.
*   **Backend InternoCore**: Corriendo en `localhost:8000` (monolito unificado).

### 2. Dispositivo Físico (Recomendado)
Para probar el flujo completo con cámara real:

```powershell
cd c:\API\interno\src\interno_billing_app
flutter pub get
flutter run -d <device-id>
```

### 3. Emulador Android (AVD)
Para probar el flujo de escaneo y aprovisionamiento en un entorno virtual:

1.  **Crear Dispositivo**: En Android Studio, crea un emulador (ej: `Interno_POS_Emu`) con API 34 (UpsideDownCake).
2.  **Iniciar desde Terminal**:
    ```powershell
    & "C:\Users\$env:USERNAME\AppData\Local\Android\Sdk\emulator\emulator.exe" -avd Interno_POS_Emu
    ```
3.  **Ejecutar App**:
    ```powershell
    cd c:\API\interno\src\interno_billing_app
    flutter run
    ```

### 4. Simulación de Escaneo (ADB Injection)
Como el emulador no tiene cámara física, puedes simular la lectura de un QR de aprovisionamiento:
```powershell
adb shell am broadcast -a com.google.zxing.client.android.SCAN --es SCAN_RESULT '{"baseUrl":"http://10.0.2.2:8000/api/v1","selectionToken":"...","companyId":"...","companyName":"..."}'
```

---

## 🏗️ Arquitectura del Sistema

La aplicación sigue los principios de **Clean Architecture** y **BLoC** para la gestión de estados:

```
lib/
├── core/
│   ├── di/injection.dart          # GetIt DI (Singleton chain)
│   ├── network/
│   │   ├── multi_tenant_interceptor.dart   # X-Company-ID, X-Warehouse-ID, Authorization
│   │   ├── resilience_interceptor.dart     # Exponential backoff + Idempotency
│   │   └── connection_status_provider.dart # connectivity_plus sensor
│   └── theme/app_theme.dart       # InternoColors, industrial palette
├── features/
│   ├── auth/
│   │   ├── data/auth_repository.dart       # Login, getCompanies, selectCompany
│   │   └── presentation/
│   │       ├── login_screen.dart           # Email/QR dual-mode login
│   │       ├── company_selection_screen.dart # Multi-tenant company picker
│   │       └── warehouse_selection_screen.dart # Warehouse context binding
│   ├── home/
│   │   └── presentation/
│   │       ├── home_screen.dart            # Uber-style dashboard (Inicio tab)
│   │       ├── inbox_screen.dart           # Notifications (Buzón tab)
│   │       └── tickets_screen.dart         # Support tickets (Menú tab)
│   ├── navigation/
│   │   └── main_navigation_screen.dart     # 5-tab IndexedStack controller
│   └── scanner/
│       ├── data/
│       │   ├── models/                     # Product, SaleRequest DTOs
│       │   └── repositories/              # ProductRepository, SaleRepository, PartnerRepository
│       └── presentation/
│           ├── scanner_screen.dart         # Camera + manual input
│           ├── checkout_screen.dart        # Cart summary + atomic commit
│           └── inventory_stock_screen.dart # Receipts/documents history
```

### Interceptor Chain (Orden Obligatorio)
```
MultiTenantInterceptor → ResilienceInterceptor → LogInterceptor
```

### Protocolo de Vinculación (QR Payload)
El QR generado por el frontend web debe contener el siguiente esquema JSON:
```json
{
  "baseUrl": "URL_DEL_SERVIDOR",
  "apiPrefix": "/api/v1",
  "selectionToken": "JWT_DE_SELECCION",
  "companyId": "UUID_EMPRESA",
  "companyName": "NOMBRE_EMPRESA"
}
```

### Flujo de Navegación
```
LoginScreen → CompanySelectionScreen → WarehouseSelectionScreen → MainNavigationScreen
                                                                       ├── HomeScreen (Inicio)
                                                                       ├── Descubrir (placeholder)
                                                                       ├── Ganancias (placeholder)
                                                                       ├── InboxScreen (Buzón)
                                                                       └── TicketsScreen (Menú)
```

---

## 📋 Plan de Implementación (Próximos Pasos)

1.  **Fase de Impresión**: Implementar la generación de recibos en PDF y soporte para impresoras térmicas Bluetooth (ESC/POS).
2.  **Persistencia Local**: Implementar un buffer offline para el carrito de compras.
3.  **Dashboard de Terminales**: Visualización de ventas por dispositivo en el portal administrativo.
4.  **Descubrir / Ganancias**: Completar módulos placeholder con catálogo de productos y reportería de ingresos.

## 🎨 Diseño y Experiencia de Usuario (Uber-Style Minimalist)

El módulo de **Ventas (Point of Sale - POS)** de InternoCore Sentinel Mobile ha sido rediseñado bajo un esquema visual de **altísimo contraste y minimalismo absoluto (monocromático blanco y negro puro)**, inspirado 1:1 en la interfaz de conductor de Uber:

*   **Fondo de Cámara Fluido:** El fondo muestra el scanner en tiempo real, desplazando el listado hacia arriba y hacia abajo programáticamente al pulsar el botón de viñetas en el extremo derecho del panel negro.
*   **Controles Táctiles Industriales:** Botones circulares de `30px` con un touch-target de `44x44px` aptos para guantes de seguridad gruesos.
*   **Especificación Detallada:** Consulta la documentación de congelación de diseño y experiencia de usuario en:
    *   [Especificación de Interfaz Uber POS](../../docs/design_system/uber_pos_layout.md)

---

## 🔐 Seguridad (Compliance)
*   **Multi-tenancy**: Todas las peticiones inyectan `X-Company-ID`, `X-Warehouse-ID`, `X-User-ID` y `Authorization` via `MultiTenantInterceptor`.
*   **Resilience**: `ResilienceInterceptor` con reintentos exponenciales y `X-Idempotency-Key` por request.
*   **Wakelock**: `wakelock_plus` previene suspensión durante sincronización crítica.
*   **Forensic Audit**: Cada venta registra el `terminal_name` en los comentarios de la transacción de inventario.
*   **RTR**: Rotación de tokens de refresco implementada para sesiones móviles persistentes.

---
*InternoCore Sentinel Mobile — Diseñado por Carlos Flores Montoya (Antigravity Architecture).*
