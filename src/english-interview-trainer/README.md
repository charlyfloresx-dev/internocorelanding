# English Interview Trainer (Industrial Edition) 🎙️🏭🚀

Un entrenador personal de entrevistas en inglés diseñado específicamente para **Ingenieros MES y Consultores de Transformación Digital**. Enfocado en la precisión técnica y la confianza profesional.

## 🌟 Características Principales

- **Personalización Senior MES**: Banco de preguntas diseñado dinámicamente basado en la experiencia con Tulip, Safran Aerospace, y reducción de WIP.
- **Mapa de Calor de Pronunciación**: Análisis palabra por palabra usando la Web Speech API para detectar puntos de mejora con colores reactivos.
- **Motor de Normalización Inteligente**: Entiende términos técnicos aunque el motor de voz los confunda (ej. Detecta "MES" aunque escuche "mess").
- **Modo Entrenamiento (Master Scripts)**: Guiones de respuesta pre-formulados para practicar la fluidez y estructura de nivel directivo.
- **Entrenamiento de Oído**: Narración auditiva de las preguntas a velocidad ajustable (1.1x) para mejorar la comprensión.
- **Feedback Técnico**: Seguimiento de palabras clave ("Keywords Mastered") para asegurar que vendes tus logros técnicos correctamente.

## 🛠️ Stack Tecnológico

- **Frontend**: Angular 18 (Zoneless Architecture)
- **Styling**: Tailwind CSS (Premium Dark Theme)
- **Audio Engine**: Web Audio API (MediaRecorder, AnalyserNode, GainNode x2.0)
- **Speech Engine**: Web Speech API (Recognition & Synthesis)
- **Performance**: PWA Ready & Mobile Responsive

## 📂 Estructura del Proyecto

- `src/app/core/audio.service.ts`: El corazón del sistema. Maneja la captura, amplificación y análisis de voz.
- `src/app/core/interview.service.ts`: Gestiona el banco de preguntas técnicas y el estado de la entrevista.
- `src/app/components/feedback-panel/`: Interfaz de análisis post-grabación con mapas de calor.

## 🚀 Instalación y Desarrollo

1. Clonar el repositorio.
2. Ejecutar `npm install`.
3. Iniciar con `npm run start`.
4. Abrir en `localhost:4200`.

---
*Desarrollado como parte del ecosistema Interno Core para el perfil de Carlos Flores.*
