# Plan de Implementación: Resiliencia Móvil (Sentinel Port)

Este documento detalla la estrategia para portar los protocolos de resiliencia del frontend Angular a la aplicación Flutter (`interno_billing_app`), transformándola en un **Sentinel Móvil**.

## 🎯 Objetivos
1.  **Idempotencia Garantizada**: Asegurar que las ventas o transferencias desde el dispositivo no se dupliquen ante micro-cortes de señal (3G/4G/WiFi).
2.  **Auto-Recuperación Silenciosa**: Implementar reintentos con backoff exponencial para manejar el "Kill Switch" del backend.
3.  **Mapeo de Estados de Recuperación**: Reconocer el código `DATABASE_RECONNECTING` para informar al operador de almacén.

---

## 🏗️ Desarrollo por Fases

### 🟢 Fase A: Implementación Técnica (COMPLETADA)
- **MultiTenantInterceptor**: Aislamiento de la lógica de identidad y trazabilidad.
- **ResilienceInterceptor**: Lógica de inyección de `X-Idempotency-Key` y reintentos con Backoff Exponencial (2s, 4s, 8s).
- **Inyección de Dependencias**: Refactorización de `injection.dart` para soportar la nueva cadena de interceptores.

### 🟢 Fase B: Mocks y Simulación de Caos (COMPLETADA)
- **ResilienceMocks**: Definición de respuestas 503 con código `DATABASE_RECONNECTING`.
- **ChaosTestingInterceptor**: Herramienta para simular fallos controlados.

### 🟢 Fase C: UX & Feedback Visual (COMPLETADA)
- **ConnectionStatusProvider**: Gestor de estado de conectividad global reactivo.
- **SentinelStatusBanner**: Widget global inyectado vía `MaterialApp.builder` para feedback persistente.

### 🟡 Fase D: Validación Industrial (EN CURSO - CAOS ACTIVO)
- **Activación de Caos**: `ChaosTestingInterceptor` configurado para 2 fallos intermitentes en `sale/checkout`.
- **Protocolo de Prueba**: Ejecutar venta en Handheld y observar el ciclo: Fallo -> Banner -> Retry -> Éxito -> Ocultar Banner.
- **Verificación de Idempotencia**: Confirmar registro único en backend.

---

## 🛠️ Arquitectura Técnica Final

### Interceptor de Resiliencia (`lib/core/network/resilience_interceptor.dart`)
Implementado con soporte nativo para `DioException` y actualización de estado vía `sl<ConnectionStatusProvider>()`.

### Cadena de Inyección Activa
```dart
dio.interceptors.addAll([
  MultiTenantInterceptor(prefs: prefs),
  ChaosTestingInterceptor(maxFailures: 2, targetPath: 'sale'), // Muro de Caos
  ResilienceInterceptor(dio: dio),                             // Escudo de Resiliencia
  LogInterceptor(...),                                         // Trazabilidad
]);
```

## 📈 Criterios de Éxito
- RTO (Recovery Time Objective) en móvil alineado con backend (< 1s tras delay).
- 0 duplicados en transacciones de POS interrumpidas.
- El usuario es informado visualmente mientras el sistema se auto-repara.
