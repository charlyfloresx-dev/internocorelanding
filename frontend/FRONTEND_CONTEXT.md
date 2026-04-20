# 🌐 Contexto del Agente Frontend: Interno Core (Production Ready)

## 1. Naturaleza del Sistema
- **MES Industrial Multitenant:** Orquestación de procesos de manufactura e inventarios para múltiples plantas de una misma cuenta (Holding).
- **Inmutabilidad SSOT:** El frontend respeta el motor "Append-Only" del backend. No se modifican registros `CONFIRMED`; se generan nuevos movimientos o se anulan los existentes.

## 2. Los Pilares de la Identidad Triple
Todo objeto del dominio (Producto, KPI, Almacén) se identifica bajo tres niveles:
1.  **UUID (Técnico):** Identificador universal para ruteo y API.
2.  **Sequence Number (Forense):** Entero incremental por empresa para auditoría física.
3.  **Folio (Comercial):** Etiqueta legible (ej: `INV-24-001`) que el usuario usa en planta.

## 3. Estrategia de Autenticación (Handshake)
Implementamos el flujo de seguridad en 3 fases:
1.  **T1 (Discovery):** Login de credenciales. Recibe `selection_token` y lista de empresas permitidas.
2.  **T2 (Context):** Selección de empresa enviando `selection_token` como cabecera. Recibe `access_token` (JWT) persistente.
3.  **Restauración:** `APP_INITIALIZER` valida el token contra el backend (`GET /auth/me`) antes de renderizar la UI, garantizando Zero Trust.

## 4. Arquitectura Angular 19 (Zoneless)
- **Rendimiento Industrial:** Corremos sin `zone.js` para optimizar el consumo de batería y CPU en terminales portátiles.
- **Reactividad Fina:** Gestión de estado basada exclusivamente en **Angular Signals**. Queda prohibido el uso de `BehaviorSubject` para estados de UI.
- **Ruteo:** Usamos `HashLocationStrategy` para asegurar que el ruteo funcione correctamente tras recargas (F5) en despliegues sobre Nginx o S3.

## 5. Resiliencia y Telemetría
- **System Health Badge:** Un indicador visual en tiempo real (🟢/🟡/🔴) informa al usuario sobre la salud de los microservicios backend.
- **Write-Lock Automatic:** Si un servicio crítico (WMS o MasterData) cae, el frontend activa el modo `isReadOnly`, bloqueando botones de guardado y permitiendo solo la navegación/lectura de datos en caché.
- **Offline Cache:** Los catálogos de productos y almacenes se hidratan desde el caché local si el backend no responde, minimizando paros en la operación.

## 6. Integración con Planta (Shopfloor)
- **Identidad de Operador:** Soporte para login vía códigos de barras o tags RFID de alta velocidad.
- **Validación de Masa:** El frontend realiza el cálculo forense de peso-cantidad antes del envío (`totalWeight = qty * conversion_factor`) con un umbral de tolerancia de ±0.0001.

## 7. Multidivisa y Valoración
- **Signals Financieros:** Cambio reactivo de moneda (USD/MXN) en toda la UI sin recarga de página.
- **Tasa Real-time:** Descuento automático de la valoración de inventario basado en el tipo de cambio activo del `CurrencyService`.

---

## 🛠 Estructura Documental
- `ENGINEERING_LOG.md`: Bitácora de decisiones arquitectónicas y técnicas.
- `CHANGELOG.md`: Registro de versiones de cara al usuario.
- `docs/legacy_audit.md`: Plan maestro de integración para portar funcionalidades del sistema legado.
