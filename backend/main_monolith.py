import os
import sys
import logging

# Configuración básica de logs para visibilidad en Docker
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout
)
import importlib
import uuid
from datetime import datetime
from fastapi import FastAPI, Request, Header, Depends, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.exc import SQLAlchemyError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# 1. Configurar PYTHONPATH para incluir TODAS las carpetas de servicios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
services = [
    "auth_service", 
    "master_data_service", 
    "inventory_service", 
    "notification_service",
    "tickets_service",
    "mes_service",
    "subscription_service"
]
for s in services:
    path = os.path.join(BASE_DIR, s)
    if path not in sys.path:
        sys.path.append(path)

from common.security.cors_setup import setup_cors
from common.middleware import InternoCoreGlobalMiddleware
from common.error_handlers import domain_exception_handler
from common.exceptions import DomainException
from common.security.limiter import limiter
from common.infrastructure.database import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Iniciando InternoCore Monolith (Unified Engine v3.5.0)...")
    print("!!!! MONOLITH STARTING - UNIQUE NAMESPACE MODE !!!!")
    
    # 2. Registro explícito de modelos para asegurar que Base.metadata los conozca
    from common.infrastructure.models.base import Base
    try:
        # Common Models
        import common.models.business_group
        import common.models.company
        import common.models.audit
        import common.models.idempotency_key
        
        # Auth Models
        import auth_app.models.user
        import auth_app.models.role
        import auth_app.models.user_company_role
        import auth_app.models.permission
        
        # Master Data Models
        import master_app.models.product
        import master_app.models.warehouse
        import common.models.location # [Phase 84] SSOT Consolidado
        import master_app.models.product_price
        import master_app.models.movement_concept
        import master_app.models.uom
        import master_app.models.exchange_rate
        import common.models.enumeration
        
        # Inventory Models
        import inventory_app.models.inventory
        # Re-importing common.models.location is fine as it uses the same class
        import inventory_app.models.item_variant
        # import inventory_app.models.warehouse # Consolidado con master_app.models.warehouse
        import inventory_app.models.document
        import inventory_app.models.inter_company_transfer
        
        # Notification Models
        import notification_app.models.notification

        # Tickets Models
        import tickets_app.models.ticket
        import tickets_app.models.escalation_rule
        import tickets_app.models.comments
        
        # MES Models
        import mes_app.models.work_order
        import mes_app.models.downtime
        import mes_app.models.labor
        import mes_app.models.shift
        import mes_app.models.production_run
        import mes_app.models.ledger
        
        # Subscription Models
        import subscription_app.models.subscription
        import subscription_app.models.wallet

    except Exception as e:
        logging.warning(f"Algunos modelos no pudieron ser pre-cargados: {e}")

    # 3. Setup Auditoría (Master Data & Inventory)
    try:
        from master_app.core.events import setup_audit_listeners as setup_master_audit
        from master_app.models.product import Product
        from master_app.models.warehouse import Warehouse
        from master_app.models.location import InventoryLocation
        from master_app.models.product_price import ProductPrice
        
        setup_master_audit(Product)
        setup_master_audit(Warehouse)
        setup_master_audit(InventoryLocation)
        setup_master_audit(ProductPrice)
        
        from inventory_app.core.events import setup_audit_listeners as setup_inv_audit
        setup_inv_audit()
        
        logging.info("Listeners de auditoría registrados.")
    except Exception as e:
        logging.warning(f"No se pudieron registrar todos los listeners de auditoría: {e}")

    # 4. Sincronización de Base de Datos
    async with engine.begin() as conn:
        logging.info("Sincronizando esquema de base de datos unificado (MetaData)...")
        await conn.run_sync(Base.metadata.create_all)
        logging.info("Esquema sincronizado exitosamente.")
        
    # 5. Operación de Rescate (Phase 87: Stripe Sync)
    try:
        from common.infrastructure.database import AsyncSessionLocal
        from subscription_app.services.recovery_service import SubscriptionRecoveryService
        async with AsyncSessionLocal() as session:
            await SubscriptionRecoveryService.sync_from_stripe_if_empty(session)
    except Exception as e:
        logging.error(f"Error durante la recuperación de Stripe Sync: {e}")
        
    yield
    logging.info("🛑 Apagando InternoCore Monolith...")

app = FastAPI(
    title="InternoCore Unified Monolith",
    description="Unified Backend Engine for Auth, Master Data, Inventory, Tickets and MES.",
    version="3.4.0-industrial",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/v1/openapi.json"
)

# ─── MIDDLEWARES ───
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")
app.add_middleware(InternoCoreGlobalMiddleware)
app.state.limiter = limiter
setup_cors(app)

# ─── EXCEPTION HANDLERS ───
@app.exception_handler(DomainException)
async def custom_domain_exception_handler(request: Request, exc: DomainException):
    return await domain_exception_handler(request, exc)

@app.exception_handler(RateLimitExceeded)
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return _rate_limit_exceeded_handler(request, exc)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    from fastapi.encoders import jsonable_encoder
    return JSONResponse(status_code=422, content={"status": "error", "message": "Input validation failed", "meta": {"details": jsonable_encoder(exc.errors()), "path": request.url.path}})

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logging.error(f"DATABASE_ERROR: {str(exc)}")
    return JSONResponse(status_code=500, content={"status": "error", "message": f"DATABASE_ERROR: {str(exc)}", "meta": {"type": "SQLAlchemyError"}})

@app.exception_handler(Exception)
async def global_unexpected_exception_handler(request: Request, exc: Exception):
    logging.error(f"UNEXPECTED_ERROR: {str(exc)}", exc_info=True)
    return JSONResponse(status_code=500, content={"status": "error", "message": "Internal Server Error", "meta": {"type": type(exc).__name__}})

# ─── ROUTER REGISTRATION ───

# 0. Integration Events (Priority)
from common.infrastructure.database import get_db
from notification_app.api.v1.endpoints import events as event_endpoints
from inventory_app.api.v1.endpoints.customs import router as customs_router
app.include_router(event_endpoints.router, prefix="/api/v1")
# Customs will be included below in Section 3 (Inventory) to maintain grouping

@app.get("/api/v1/customs/debug-monolith")
async def debug_customs_monolith():
    return {"status": "ok", "message": "Hardcoded monolith customs path is reachable"}

# 1. Auth
from auth_app.api.v1.endpoints.auth import router as auth_router
from auth_app.api.v1.endpoints.companies import router as companies_router
from auth_app.api.v1.endpoints.users import router as users_router
from auth_app.api.v1.endpoints.collaborator_auth import router as collaborator_auth_router
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(collaborator_auth_router, prefix="/api/v1/auth", tags=["Industrial Auth"])
app.include_router(companies_router, prefix="/api/v1/companies", tags=["Auth: Companies"])
app.include_router(users_router, prefix="/api/v1/users", tags=["Auth: Users"])

# 2. Master Data
from master_app.api.v1.endpoints import (
    products, prices, uom_router, categories, brands, 
    concepts, warehouses, partners, gis_validator, locations, 
    currency, enums as enums_router, enumerations
)
app.include_router(products.router, prefix="/api/v1/products", tags=["Master: Products"])
app.include_router(prices.router, prefix="/api/v1/prices", tags=["Master: Product Prices"])
app.include_router(uom_router.router, prefix="/api/v1/uoms", tags=["Master: UOMs"])
app.include_router(categories.router, prefix="/api/v1/categories", tags=["Master: Categories"])
app.include_router(brands.router, prefix="/api/v1/brands", tags=["Master: Brands"])
app.include_router(concepts.router, prefix="/api/v1/concepts", tags=["Master: Concepts"])
app.include_router(warehouses.router, prefix="/api/v1/warehouses", tags=["Master: Warehouses"])
app.include_router(partners.router, prefix="/api/v1/partners", tags=["Master: Partners"])
app.include_router(gis_validator.router, prefix="/api/v1/gis", tags=["Master: GIS"])
app.include_router(locations.router, prefix="/api/v1/locations", tags=["Master: Locations"])
app.include_router(currency.router, prefix="/api/v1/currencies", tags=["Master: Currency"])
app.include_router(enums_router.router, prefix="/api/v1/enums", tags=["Master: System Enums"])
app.include_router(enumerations.router, prefix="/api/v1/enumerations", tags=["Master: System Enumerations"])

# 3. Inventory
from inventory_app.api.v1.endpoints.transactions import router as transactions_router
from inventory_app.api.v1.endpoints.reconciliation import router as reconciliation_router
from inventory_app.api.v1.endpoints.boms import router as boms_router
from inventory_app.api.v1.endpoints.dashboard import router as inventory_dashboard_router
from inventory_app.api.v1.endpoints.inventory_search import router as inventory_search_router
from inventory_app.api.v1.endpoints.inventory import router as inventory_ops_router
from inventory_app.api.v1.endpoints.customs import router as customs_router
from inventory_app.api.v1.endpoints.variants import router as variants_router
from inventory_app.api.v1.endpoints.inter_company_transfers import router as ict_router
from inventory_app.api.v1.endpoints.demo_reset import router as demo_reset_router
from inventory_app.api.v1.endpoints.locations import router as wms_locations_router  # [Phase 83] P0 Fix
from inventory_app.api.v1.endpoints.audit import router as audit_router
app.include_router(audit_router, prefix="/api/v1/audit", tags=["Global: Forensic Audit"])
app.include_router(transactions_router, prefix="/api/v1/inventory", tags=["Inventory: Transactions"])
app.include_router(reconciliation_router, prefix="/api/v1/inventory", tags=["Inventory: Reconciliation"])
app.include_router(boms_router, prefix="/api/v1/inventory/boms", tags=["Inventory: BOMs"])
app.include_router(inventory_dashboard_router, prefix="/api/v1/dashboard", tags=["Inventory: Dashboard"])
app.include_router(inventory_search_router, prefix="/api/v1/search", tags=["Inventory: Search"])
app.include_router(inventory_ops_router, prefix="/api/v1/inventory", tags=["Inventory: Operations"])
app.include_router(variants_router, prefix="/api/v1/inventory/variants", tags=["Inventory: Variants"])
app.include_router(ict_router, prefix="/api/v1/inventory/transfers/inter-company", tags=["Inventory: ICT"])
app.include_router(customs_router, prefix="/api/v1/reporting/customs", tags=["Inventory: Customs Reporting"])
app.include_router(demo_reset_router, prefix="/api/v1", tags=["Inventory: Admin / Demo"])
app.include_router(wms_locations_router, prefix="/api/v1/inventory", tags=["WMS: Location Management (Density Guard)"])  # [Phase 83] P0 Fix

# 4. Notifications
from notification_app.api.v1.endpoints import notifications as notification_endpoints
app.include_router(notification_endpoints.router, prefix="/api/v1/notifications", tags=["Notifications: Real-Time & History"])

# 5. Tickets
from tickets_app.routers import ticket_routes
app.include_router(ticket_routes.router, prefix="/api/v1/tickets", tags=["Industrial: Tickets"])

# 6. MES
from mes_app.api.v1.endpoints import scan, dashboard as mes_dashboard, labor, downtime, work_order as mes_orders, sync as mes_sync, resource, shift
app.include_router(scan.router, prefix="/api/v1/mes", tags=["MES: Scan"])
app.include_router(mes_dashboard.router, prefix="/api/v1/mes/dashboard", tags=["MES: Dashboard"])
app.include_router(labor.router, prefix="/api/v1/mes/labor", tags=["MES: Labor"])
app.include_router(downtime.router, prefix="/api/v1/mes/downtime", tags=["MES: Downtime"])
app.include_router(mes_orders.router, prefix="/api/v1/mes/orders", tags=["MES: Work Orders"])
app.include_router(mes_sync.router, prefix="/api/v1/mes", tags=["MES: Sync"])
app.include_router(resource.router, prefix="/api/v1/mes/resources", tags=["MES: Resources"])
app.include_router(shift.router, prefix="/api/v1/mes/shifts", tags=["MES: Shifts"])

# 7. Subscriptions & Billing
from subscription_app.api.v1.endpoints import billing, wallet, admin as sub_admin, internal as sub_internal, webhooks
app.include_router(billing.router, prefix="/api/v1/billing", tags=["Billing: Stripe Checkout"])
app.include_router(wallet.router, prefix="/api/v1/wallet", tags=["Billing: Wallet"])
app.include_router(sub_admin.router, prefix="/api/v1/admin/subscription", tags=["Billing: Admin"])
app.include_router(sub_internal.router, prefix="/internal", tags=["Billing: Internal Entitlements"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["Billing: Stripe Webhooks"])

# 8. HCM (Human Capital Management)
from hcm_app.api.v1.endpoints import collaborators, internal as hcm_internal
app.include_router(collaborators.router, prefix="/api/v1/collaborators", tags=["HCM: Collaborators"])
app.include_router(hcm_internal.router, prefix="/api/v1/internal/collaborators", tags=["HCM: Internal"])

@app.get("/")
async def root():
    return {"message": "InternoCore Unified Monolith is running", "services": ["Auth", "Master Data", "Inventory", "Notifications", "Tickets", "MES", "Subscription"], "docs": "/api/docs"}

@app.get("/api/v1/health")
@app.get("/api/v1/readiness")
@app.get("/health")
async def health_check():
    """
    Endpoints de salud consolidados para orquestación (AWS/K8s/Docker).
    """
    return {
        "status": "ready", 
        "online": True,
        "mode": "monolith", 
        "engine": "FastAPI Unified v3.4",
        "timestamp": datetime.utcnow().isoformat()
    }

# ─── WEBSOCKET HUB (Phase 50: Zero Polling) ───
from common.infrastructure.websocket import manager
from fastapi import WebSocketDisconnect

@app.websocket("/ws/{company_id}")
async def websocket_endpoint(websocket: WebSocket, company_id: str):
    await manager.connect(websocket, company_id)
    try:
        while True:
            # Mantener la conexión abierta y escuchar latidos si es necesario
            data = await websocket.receive_text()
            # Opcional: Procesar comandos entrantes del cliente vía WS
    except WebSocketDisconnect:
        manager.disconnect(websocket, company_id)
    except Exception as e:
        logging.error(f"WebSocket error for {company_id}: {e}")
        manager.disconnect(websocket, company_id)
