# Checklist Paso a Paso
## Configuración Segura de Visual Studio Code y API Key (Gemini / Google Cloud)

> **Objetivo:**
> Permitir el uso de agentes de IA en Visual Studio Code para desarrollo de **InternoCore**, manteniendo el consumo **bajo, controlado y auditable**, evitando ejecuciones automáticas o costos inesperados.

---

## 1. Principios de arquitectura (regla base)

- Los **agentes de IA** se utilizan **solo para escribir código y documentación**.
- La **lógica productiva** (IA usada por el sistema) **nunca** se ejecuta desde VS Code.
- Todo consumo de IA debe ser:
  - Explícito
  - Limitado
  - Medible

---

## 2. Google Cloud – Configuración del proyecto (DEV)

### 2.1 Crear proyecto exclusivo para desarrollo

- Proyecto: `internocore-dev-ai`
- Uso exclusivo: agentes y pruebas locales
- Nunca compartir con producción

---

### 2.2 Habilitar únicamente la API necesaria

Ruta:
```
Google Cloud Console
→ APIs & Services
→ Library
```

- Habilitar:
  - ✅ Generative Language API
- No habilitar otros servicios

---

### 2.3 Crear API Key

Ruta:
```
APIs & Services
→ Credentials
→ Create Credentials
→ API Key
```

Guardar temporalmente la key.

---

### 2.4 Restringir la API Key (CRÍTICO)

**Application restrictions**
- Tipo: IP addresses
- Permitidas:
  ```
  127.0.0.1
  ```

**API restrictions**
- Restrict key
- APIs permitidas:
  - Generative Language API

///AIzaSyCffAEuzlj7_mzBQY1mxi0NHCI9uNqQ0KY///
---

### 2.5 Configurar Billing seguro

Ruta:
```
Billing
→ Budgets & alerts
```

- Budget máximo: **$5 USD**
- Alertas:
  - 50%
  - 90%
- (Si está disponible) deshabilitar servicios al 100%

---

## 3. Visual Studio Code – Configuración segura

### 3.1 Abrir panel de extensiones (sin atajos)

En VS Code:
- Menú ☰
- View → Extensions

---

### 3.2 Desactivar extensiones de IA por defecto

Desactivar (no desinstalar):
- Gemini
- Google AI Studio
- AI Code Assistant
- Cualquier agente automático

> Las extensiones solo se activan cuando se van a usar.

---

### 3.3 Desactivar autocompletado automático

Ruta:
```
☰ → File → Preferences → Settings
```

Buscar `inline` y desactivar:
- Editor: Inline Suggest
- Editor: Suggest On Trigger Characters

Buscar `AI` y desactivar todas las opciones relacionadas.

---

## 4. Variables de entorno (.env)

### 4.1 Uso controlado de API Key

Ejemplo:
```env
GOOGLE_API_KEY=AIzaSyXXXX
AI_DEV_ENABLED=true
```

Reglas:
- La key **solo existe mientras se usan agentes**
- Al terminar:
  - Eliminar la key
  - O establecer `AI_DEV_ENABLED=false`

Nunca definir la key como variable global del sistema.

---

## 5. Configuración de límites del agente

### 5.1 Parámetros recomendados por request

```json
{
  "temperature": 0.2,
  "maxOutputTokens": 256,
  "topP": 0.8
}
```

Restricciones:
- Sin contexto ilimitado
- Sin historial automático
- Sin reintentos silenciosos

---

## 6. Procedimiento operativo seguro (uso diario)

### Antes de usar agentes

- Activar extensión necesaria
- Colocar API Key en `.env`
- Verificar billing activo

### Durante el uso

- Una tarea a la vez
- Un agente activo
- Prompts cortos y específicos

### Al terminar

- Desactivar extensión
- Borrar API Key del `.env`
- Confirmar requests en GCP = 0

---

## 7. Monitoreo y verificación

### Google Cloud

- Billing → Reports
- APIs & Services → Metrics

Verificar:
- Requests solo cuando el agente está activo
- Sin consumo en background

---

## 8. Checklist final de seguridad

### Google Cloud
- [ ] Proyecto DEV separado
- [ ] API Key restringida
- [ ] Budget configurado

### VS Code
- [ ] Autocomplete desactivado
- [ ] Agentes apagados por defecto

### Uso
- [ ] Activación manual
- [ ] Kill switch activo
- [ ] Límites por request

---

## 9. Nota para documentación académica (tesis)

> *El incidente de consumo inesperado permitió establecer un modelo de gobernanza de uso de IA en entornos de desarrollo, demostrando que la seguridad en sistemas modernos no solo abarca datos y accesos, sino también la gestión consciente de costos y automatizaciones.*

---

**Documento en formato Markdown para uso técnico y académico.**

