# Service Log — Interno POS Mobile App

## 🕒 Última Actividad (2026-05-08)

**Fase 92: Global State Persistence & Industrial UI Feedback**
- **Architecture Refactor (LazySingleton)**: Migrated `ScannerBloc` to a global singleton in `injection.dart` and wrapped `MaterialApp` in `main.dart`. This ensures the shopping cart persists across all navigation events, solving the `ProviderNotFoundException` during checkout.
- **Reactive Industrial Feedback**: Integrated `BlocListener` with glassmorphic SnackBar (Toastr) system for high-fidelity success/error notifications during scanning.
- **Navigation Safety**: Removed manual Bloc passing in favor of the global provider, simplifying the transition between `ScannerScreen` and `CheckoutScreen`.
- **Debug Traceability**: Injected tactical debug prints in the scanner flow for real-time monitoring via VS Code Debug Console.
- **Status**: ✅ COMPLETED - Mobile State Management Hardened & Production Ready.

**Fase 91: Industrial Provisioning & Checkout Integration**
- **Zero-Trust Provisioning (QR Handshake)**: Implementada pantalla `SetupScreen` que permite configurar la app escaneando un QR desde el portal web. El proceso inyecta `baseUrl`, `accessToken`, `companyId` y `warehouseId` automáticamente.
- **Auto-Login Sequence**: El sistema detecta tokens en el QR y realiza un bypass de login directo hacia el escáner de productos.
- **Dynamic Networking**: Refactorizado `Dio` en `injection.dart` para reconstruirse dinámicamente al cambiar la `base_url` mediante SharedPreferences.
- **Atomic Checkout**: Integrado `SaleRepository` con el endpoint de backend `pos/checkout`, permitiendo confirmar ventas de múltiples artículos con un solo commit.
- **Hidden Setup Entry**: Añadido activador por *Long Press* en el logo de la pantalla de login para re-configurar terminales en campo.
- **Status**: ✅ COMPLETED - Mobile POS ready for Industrial Deployment.
