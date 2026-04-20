# Liquor Distro Simulator Script (`simulate_liquor_distro.py`)

## ⚠️ IMPORTANTE: Propósito y Limitaciones
Este script **NO ES UN SCRIPT DE ONBOARDING** para la configuración regular de nuevas empresas en el módulo de inventarios.
Su único propósito es la **simulación técnica en masa (Stress Testing & UI Demo)**. Manipula directamente las tablas crudas de PostgreSQL utilizando SQLAlchemy, esquivando por completo las capas de negocio (Interfaces API), restricciones de la Domain-Driven Design y los validadores formales de InternoCore.

**No usar** para dar de alta clientes reales o configurar entornos productivos.

## Contexto
Para finalizar la industrialización del ecosistema de logística (Phase 53), fue necesario probar el comportamiento real de los frontends en un ambiente multicliente con alto volumen de transacciones de inventario. El script genera un modelo de negocio completo del giro de licores:

1. **Jerarquías Multi-Empresa (Multitenancy)**:
   - 1 Empresa Distribuidora (Matriz).
   - 3 Empresas Minoristas (Bares/Pubs).

2. **Perfiles de Seguridad (SSOT: `user_company_roles`)**:
   - `tony@interno.com` (Admin de Catálogo e Inventario) -> Acceso a todas las sucursales.
   - `garry@interno.com` (Admin de Almacenes) -> Acceso exclusivo a la Matriz Distribuidora.
   - `tropy@interno.com` (Operador) -> Acceso único a una sucursal (ej: Bar La Terraza VIP).
   - Password global: `charly123`.

3. **Master Data Injection**:
   - Más de 60 SKUs entre Cervezas, Vinos y Destilados de alto valor.

4. **Kardex y Valoración Financiera (WAC / FIFO)**:
   - Inyección matemática de entradas pasadas (`IN`), salidas orgánicas (`OUT`) y ajustes por mermas (`ADJUSTMENT`).
   - Genera transacciones con el tag `PENDING_FINANCIAL_VALUATION` para poder ejercer validación forense desde los dashboards de auditoría.

## Uso Técnico Recomendado
- Comando de ejecución: `python backend/scripts/simulate_liquor_distro.py`
- Requisito: Las bases de datos deben estar creadas, sin esquemas corrompidos. Puede reescribir y actualizar registros ya que implementa la táctica `ON CONFLICT DO NOTHING / KEY UPDATE`.
