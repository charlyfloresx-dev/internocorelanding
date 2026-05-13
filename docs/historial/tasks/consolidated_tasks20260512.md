# InternoCore: Consolidated Tasks - 2026-05-12

## Contexto
Phase 99: Muro de Hierro (Rate Limiting) — COMPLETADA.
Phase 100: Big Bang (1M Records Stress Test) — COMPLETADA.
Phase 101: Resilience Stress-Test & Kill Switch Certification — COMPLETADA.

## Tareas Completadas ✅
1.  **Inyección Global de pre_ping**: Se inyectó `pool_pre_ping=True` en todas las instancias de `create_async_engine` (14 servicios).
2.  **Idempotencia en Bulk-Load**: Se implementó soporte para `X-Idempotency-Key` en el backend.
3.  **Test de Caos V4 (Kill Switch)**: Resiliencia validada con caída de DB de 10s.
4.  **Frontend Sentinel (Phase 4.1.2)**: Implementado `resilience.interceptor.ts` con Backoff Exponencial y mapeo semántico de `DATABASE_RECONNECTING`.
5.  **Bypass Administrativo**: Validado bypass de rate limit mediante secreto interno.
6.  **Integración de Redis**: Migrada dependencia a la infraestructura monolítica.
7.  **Sync Docs Protocol**: Archivos de historial y REPO_LOG.md actualizados al 12 de Mayo.

## Pendientes ⏳
1.  **[Frontend] Idempotency Persistence**: Asegurar que la UI mantenga el estado de "Procesando" durante los reintentos automáticos para evitar clics dobles.
2.  **[Backend] Robustez de Enums**: Implementar `IF NOT EXISTS` en scripts de inicio para evitar `UniqueViolationError`.
3.  **[Fase 5: IaC] Diseño de Red (VPC)**: Subredes Públicas (ALB), Privadas (Servicios) y Aisladas (DB).
4.  **[Fase 5: IaC] Amazon RDS Multi-AZ**: Configurar failover nativo y evaluar RDS Proxy para optimización de ráfagas.
5.  **[Fase 5: IaC] ALB Healthcheck Semántico**: Configuración agresiva (10s, 2 Fallos) apuntando a `/health`.
6.  **[Fase 5: IaC] ECS Fargate Scaling**: Políticas de escalado basadas en CPU (>70%) para picos de tráfico industrial.
