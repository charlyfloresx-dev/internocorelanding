# Plan de Implementación: Landing Page Industrial (InternoCore)

Este documento detalla la hoja de ruta para la creación de la página de aterrizaje (Landing Page) maestra del ecosistema InternoCore, diseñada para proyectar la robustez técnica y la excelencia operativa del núcleo industrial.

## 1. Concepto Arquitectónico: "The Industrial Backbone"

La landing page debe actuar como el portal de entrada al sistema, comunicando no solo funcionalidad, sino también la infraestructura y seguridad que soportan la operación.

- **Objetivo**: Convertir visitantes técnicos en usuarios del sistema.
- **Narrativa**: De la materia prima a la inteligencia de negocios, todo en un solo núcleo.
- **Público Objetivo**: Jefes de planta, Directores de Logística y CTOs industriales.

## 2. Estrategia de Diseño (UI/UX)

Seguiremos los estándares de **Alta Fidelidad** establecidos en el proyecto:

### Paleta de Colores y Tipografía
- **Fondo**: `#0B0E14` (Deep Industrial Black) con gradientes sutiles en `rgba(0, 209, 255, 0.05)`.
- **Acentos**: `var(--primary)` (#00D1FF) para llamadas a la acción y estados activos.
- **Fuentes**:
  - **Outfit**: Para encabezados de alto impacto (H1, H2).
  - **Inter**: Para descripciones técnicas y legibilidad.

### Elementos Visuales
- **Glassmorphism**: Tarjetas con fondos traslúcidos y bordes de 1px con brillo sutil.
- **Micro-animaciones**: Uso de `IntersectionObserver` para revelado de secciones al hacer scroll.
- **Gráficos Generativos**: Uso de IA para crear representaciones visuales de procesos de manufactura y logística.

## 3. Estructura de Secciones

| Sección | Contenido Clave | Objetivo |
| :--- | :--- | :--- |
| **Hero** | Headline: "Escala tu Operación Industrial" | Impacto inmediato y propuesta de valor. |
| **The Core Triad** | MES Engine, WMS Logistics, CMMS Assets | Desglose de los pilares del sistema. |
| **Muro de Hierro** | Auditoría Forense y Seguridad RFID/PIN | Proyectar invulnerabilidad y trazabilidad. |
| **Architecture Hub** | Mapa de microservicios y despliegue en AWS | Credibilidad técnica y scalabilidad. |
| **Pricing Table** | Planes Operativo ($45), Industrial ($350), Enterprise ($550) | Transparencia comercial y conversión. |
| **Final CTA** | Botón de "Iniciar Despliegue" | Cierre de conversión. |

## 4. Hoja de Ruta Técnica

### Fase 1: Cimentación (Día 1)
- [ ] Creación del componente `LandingPageComponent` (Standalone Angular).
- [ ] Configuración de rutas en `app.routes.ts` para capturar la raíz `/`.
- [ ] Implementación del layout base con el sistema de diseño actual.

### Fase 2: Desarrollo de Contenido (Día 1-2)
- [ ] Redacción de copies industriales orientados a ROI.
- [ ] Generación de assets visuales (imágenes de robots, almacenes, código).
- [ ] Integración de la tabla de precios reactiva.

### Fase 3: Pulido y Animación (Día 2)
- [ ] Implementación de animaciones de entrada (Reveal animations).
- [ ] Optimización SEO (Meta tags, OpenGraph para compartir en redes).
- [ ] Pruebas de responsividad (Mobile/Tablet/Desktop).

## 5. Próximos Pasos Inmediatos

1. **Aprobación del Plan**: Validar con el usuario si la estructura de precios y secciones es la correcta.
2. **Generación de Imagen Hero**: Crear el primer activo visual para definir el "feeling" de la página.
3. **Draft del Componente**: Crear el archivo `.ts` y `.html` base en el frontend.

---
**Documento de Planificación - InternoCore Engineering Team - Mayo 2026**
