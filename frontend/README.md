<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# 🌐 Interno Core - Frontend (MES Industrial)

Frontend de alto rendimiento para el Sistema de Ejecución de Manufactura (MES) de Interno Core, construido con **Angular 19 (Zoneless)** y diseñado para resiliencia en entornos industriales.

## 🚀 Estado del Proyecto (Audit Integrated)
Este frontend ha sido migrado desde el prototipo `temp_future` y enriquecido con la lógica crítica del sistema legado (`frontend_legacy`).

- **Zoneless Performance:** Máxima eficiencia de CPU/Batería para tablets industriales.
- **Microservices Ready:** Conexión nativa con Auth, Inventory, Master Data, MES (Production) y Currency services.
- **Multidivisa Reactiva:** Conversión dinámica USD/MXN con persistencia.
- **System Health Monitor:** Vigilancia en tiempo real del clúster de microservicios.

## 📚 Documentación Técnica (Recomendada)
Para entender la arquitectura y las reglas de negocio, consulte:
- [**Contexto del Frontend**](./FRONTEND_CONTEXT.md): Pilares de identidad, Handshake de 3 pasos y reglas industriales.
- [**Log de Ingeniería**](./ENGINEERING_LOG.md): Bitácora de decisiones técnicas y arquitectura Zoneless.
- [**Auditoría del Legado**](./docs/legacy_audit.md): Plan de migración y estatus de módulos portados.

## 🛠 Ejecución Local (Docker Orchestration)

**Prerrequisitos:** Node.js 20+, Docker Desktop.

1. **Instalar dependencias:**
   ```bash
   npm install
   ```
2. **Levantar el ecosistema (Docker):**
   ```bash
   docker-compose up -d --build
   ```
   *El frontend estará disponible en `http://localhost:8080`*

3. **Modo Desarrollo (Vite):**
   ```bash
   npm run dev
   ```

## 🧪 Testing (Playwright)
Contamos con una suite de pruebas E2E estabilizada con mocks híbridos:
```bash
npx playwright test
```

---
*Interno Core - Ingeniería de Resiliencia Industrial @ 2026*
