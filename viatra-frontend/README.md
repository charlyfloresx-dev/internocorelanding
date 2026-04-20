# Viatra Core — Mission Control

Plataforma de logística de viajes grupales, diseñada bajo una arquitectura de microservicios, Clean Architecture y Multitenancy. Centraliza reservas, control de pagos (Stripe), documentación y automatismos financieros.

## Frontend (Mission Control)
Aplicación Angular 19 diseñada con estética **Slate-950 y acentos Neón** para un look "Mission Control", operando con lógica multitenant.

### Flujo de Autenticación
Integra **Google Sign-In (GSI)**. Al autenticar, se interactúa con el `auth_service` del backend de Interno Core:
1. Emisión de `token` (via GSI).
2. Intercambio por `selection_token` y recepción del `CompanyAccessDto` (`/api/v1/auth/social-login`).
3. Selección de Agencia (Handshake) para obtener el JWT final multi-empresa (`/api/v1/auth/select-company`).
