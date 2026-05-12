# 🧩 Ecosistema de Aplicaciones Satélite (src/)

Este directorio contiene las aplicaciones frontend, móviles y herramientas auxiliares que orbitan el núcleo de **InternoCore**. A diferencia del `frontend/` y `backend/` principales, estos proyectos son módulos especializados para casos de uso específicos.

## 📱 Aplicaciones Móviles e Industriales
- **`interno_billing_app/`**: Aplicación móvil (Flutter) para Punto de Venta (POS) industrial. Soporta escaneo de códigos de barras, gestión de carrito y checkout Zero-Trust mediante QR.
- **`eventKiosk/`**: Interfaz táctil optimizada para el registro y gestión de asistentes en eventos masivos.

## 💻 Frontends Especializados
- **`viatra-frontend/`**: Portal para la gestión de logística y viajeros (Viatra). Implementa flujos de check-in y visualización de itinerarios.
- **`english-interview-trainer/`**: Herramienta basada en IA (Gemini) para la práctica de entrevistas en inglés.
- **`landing/`**: Sitio web informativo y de captación para el ecosistema InternoCore.

## 🛠️ Directrices de Desarrollo en `src/`
1.  **Independencia de Git:** Estos proyectos no deben contener sus propias carpetas `.git`. Se gestionan como parte del Monolito Unificado para asegurar la sincronización de versiones.
2.  **Consumo de API:** Todas las aplicaciones en esta carpeta deben consumir los servicios expuestos por el `backend/` (Puertos `8000`-`8008`).
3.  **Aislamiento de Configuración:** Cada proyecto mantiene su propio `package.json` o `pubspec.yaml`, pero las variables de entorno sensibles deben ser gestionadas a través del sistema de `vault/` del proyecto raíz.

---
**Nota:** Para el motor principal del sistema, consulte las carpetas `/backend` y `/frontend` en la raíz del repositorio.
