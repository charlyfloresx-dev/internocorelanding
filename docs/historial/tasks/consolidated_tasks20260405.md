# Consolidated Tasks - 2026-04-05

## Backend - Governanza Cloud Global
- [x] Convertir todos los config directos que usan `os.getenv` a Pydantic `BaseSettings`
- [x] Preparar inyección transparente desde AWS Secrets Manager
- [x] Corregir Hardcodes Legacy (`localhost` -> `db`) en config base
- [x] Reparar falsos positivos y anidamiento en el agente auditor (`generate_code_graph.py`)
- [x] **MES Service**: Refactorizar 100% de `app/infrastructure/repositories/*` para forzar la inyección explícita del parámetro `company_id`.

## Backend - Inventory Service (🔥 FOCO ACTUAL)
- [ ] Refactor de Repositorios de Inventario (`sqlalchemy_inventory_repository.py`) para filtrar consultas obligatoriamente por `company_id`.
- [ ] Refactorización de scripts de mantenimiento manuales (`force_companies.py`, `migrate_schema.py`) para consumir las variables de entorno inyectadas correctamente.

## Backend - Resto del Sistema
- [ ] Currency Service: Aplicación de Filtro Zero-Trust
- [ ] Subscription Service: Aplicación de Filtro Zero-Trust
- [ ] Viatra Service: Aplicación de Filtro Zero-Trust
