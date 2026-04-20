import asyncio
import uuid
import os
import random
from decimal import Decimal
from datetime import datetime, timedelta, timezone
import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# --- CONFIGURATION (DOCKER LOCALHOST PORTS) ---
AUTH_DB_URL = "postgresql+asyncpg://user:password@localhost:5433/dbname"
MASTER_DB_URL = "postgresql+asyncpg://user:password@localhost:5433/master_data_db"
INV_DB_URL = "postgresql+asyncpg://user:password@localhost:5433/inventory_db"

GROUP_ID = "eb8f7e2c-3f4a-4b5c-8d7e-1f2a3b4c5d6e"

DISTRIBUIDOR_ID = "11111111-1111-4111-8111-123456789abc"
BAR_TERRAZA_ID = "22222222-2222-4222-8222-123456789abc"
BAR_IRLANDES_ID = "33333333-3333-4333-8333-123456789abc"
BAR_SPEAKEASY_ID = "44444444-4444-4444-8444-123456789abc"

WH_DISTRIBUIDOR = "aa11aaaa-aaaa-4aaa-8aaa-123456789abc"
WH_TRANSIT = "bb11bbbb-bbbb-4bbb-8bbb-123456789abc"
CHARLY_ID = "69aa5ddc-bbaa-46e6-a7f0-aeb4b92b6d38"

UOM_CAJA = "88888888-8888-8888-8888-123456789aaa"
UOM_BOTELLA = "99999999-9999-9999-9999-123456789aaa"

CERVEZAS = [
    ("TKT LIGHT", 250.0), ("TKT ROJA", 260.0), ("INDIO", 280.0),
    ("SOL", 240.0), ("XX LAGUER", 290.0), ("XX AMBAR", 300.0),
    ("BOHEMIA CLARA", 350.0), ("BOHEMIA OSCURA", 350.0),
    ("HEINEKEEN", 380.0), ("COORS LIGHT", 320.0), ("ULTRA AMSTELL", 390.0)
]

BOTELLAS = [
    ("1800 REPOSADO", 750.0), ("TRADICIONAL JOSE CUERVO", 450.0),
    ("HERRADURA REPOSADO", 850.0), ("DON JULIO REPOSADO", 1100.0),
    ("DON JULIO 70", 1600.0), ("BUCHANANS 12", 1200.0),
    ("BUCHANANS 18", 2200.0), ("JHONNY WALKER ETIQUETA ROJA", 750.0),
    ("JHONNY WALKER ETIQUETA NEGRA", 1300.0), ("CHIVAS 12", 1100.0),
    ("JACK DANIELS", 700.0), ("JACK DANIELS HONNEY", 750.0),
    ("SMIRNOFF", 350.0), ("ABSOLUT", 400.0), ("STOLICHNAYA", 450.0),
    ("GREEYGOOSE", 950.0), ("CAPITAN MORGAN", 380.0),
    ("BACARDI BLANCO", 350.0), ("MALIBU", 400.0), ("REMY MARTIN", 1800.0),
    ("MARTELL", 1500.0), ("HENNESY", 1650.0), ("JAGGERMEISTER", 550.0),
    ("HIPNOTIC", 900.0), ("NUVO", 950.0), ("MOET BRUT", 2500.0),
    ("MOET NECTAR", 2800.0), ("MOET ICE", 3200.0), ("DOM PERIGNON", 7500.0),
    ("AS DE ESPADAS", 8000.0), ("CUERVO ESPECIAL", 380.0), ("BAILEYS", 500.0),
    ("AMARETO DISSANORO", 600.0), ("KALHUA", 450.0), ("MIDORI", 550.0),
    ("DON PEDRO", 250.0), ("LA CETTO 237ml", 120.0), ("LA CETTO CABERNET", 350.0),
    ("BACARDI AÑEJO", 400.0), ("CAZADORES", 420.0), ("1800 AÑEJO", 1000.0),
    ("HERRADURA AÑEJO", 1100.0), ("SMIRNOFF TAMARINDO", 380.0),
    ("VINO ZINFANDEL", 280.0), ("PATRON", 900.0), ("MOET CHAMPAGNE", 2600.0),
    ("TORRES 10", 650.0), ("HORNITOS", 500.0), ("LICOR 43", 750.0),
    ("MACALLAN", 2500.0), ("MERLOT", 400.0)
]

def now_minus(days: int, hours=0):
    return datetime.now(timezone.utc) - timedelta(days=days, hours=hours)

async def run_simulation():
    engine_auth = create_async_engine(AUTH_DB_URL)
    engine_master = create_async_engine(MASTER_DB_URL)
    engine_inv = create_async_engine(INV_DB_URL)
    
    print("[LIQUOR DISTRO V2] Construyendo Ecosistema de Licores...")

    # ==========================================
    # 1. AUTH DB (Empresas y Permisos)
    # ==========================================
    async with engine_auth.begin() as conn:
        for cid, nm in [(DISTRIBUIDOR_ID, "Distribuidor Licores Core"), 
                        (BAR_TERRAZA_ID, "Bar La Terraza VIP"), 
                        (BAR_IRLANDES_ID, "El Pub Irlandés"), 
                        (BAR_SPEAKEASY_ID, "Speakeasy 1920 Premium")]:
            await conn.execute(text("""
                INSERT INTO companies (id, name, parent_group_id, country_code, status, is_active, version_id, base_currency)
                VALUES (:id, :n, :gid, 'MX', 'ACTIVE', TRUE, 1, 'MXN') ON CONFLICT (id) DO UPDATE SET name=:n;
            """), {"id": cid, "n": nm, "gid": GROUP_ID})
            
            res = await conn.execute(text("SELECT id FROM roles WHERE company_id = :cid LIMIT 1"), {"cid": cid})
            row = res.fetchone()
            if row:
                dmid = row[0]
            else:
                dmid = str(uuid.uuid4())
                await conn.execute(text("INSERT INTO roles (id, name, company_id, tenant_id, is_active, version_id) VALUES (:id, 'admin', :cid, :cid, true, 1) ON CONFLICT DO NOTHING;"), {"id": dmid, "cid": cid})
            ucr_id = str(uuid.uuid4())
            await conn.execute(text("INSERT INTO user_company_roles (id, user_id, company_id, role_id, tenant_id, scopes, version_id, is_active, is_new) VALUES (:id, :uid, :cid, :rid, :cid, '[\"*\"]', 1, true, false) ON CONFLICT DO NOTHING;"), {"id": ucr_id, "uid": CHARLY_ID, "cid": cid, "rid": dmid})
            
        # Generar hash de password o reciclar el de charly
        charly_hash_row = await conn.execute(text("SELECT hashed_password FROM users WHERE id = :uid"), {"uid": CHARLY_ID})
        charly_hash = charly_hash_row.scalar() or "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"
        
        # Insertar los nuevos usuarios
        users = [
            ("55555555-5555-5555-5555-123456789abc", "tony@interno.com", "Tony", "Stark"),
            ("66666666-6666-6666-6666-123456789abc", "tropy@interno.com", "Tropy", "Operator"),
            ("77777777-7777-7777-7777-123456789abc", "garry@interno.com", "Garry", "Admin"),
            ("88888888-8888-8888-8888-123456789abc", "areli@interno.com", "Areli", "Auditor")
        ]
        
        for uid, email, _, _ in users:
            await conn.execute(text("""
                INSERT INTO users (id, email, hashed_password, company_id, tenant_id, is_active, version_id)
                VALUES (:id, :email, :pw, :cid, :cid, true, 1) ON CONFLICT DO NOTHING;
            """), {"id": uid, "email": email, "pw": charly_hash, "cid": DISTRIBUIDOR_ID})

        # Limpiar roles anteriores de los usuarios de prueba para evitar duplicados (Error 500 select-company)
        test_uids = [u[0] for u in users] + [CHARLY_ID]
        await conn.execute(text("DELETE FROM user_company_roles WHERE user_id = ANY(:uids)"), {"uids": test_uids})

        # Asignar a TONY: Todas las empresas (inv:manage, config:manage)
        tony_scopes = '["inv:movements:manage", "inv:warehouse:manage", "master:catalog:manage"]'
        for cid in [DISTRIBUIDOR_ID, BAR_TERRAZA_ID, BAR_IRLANDES_ID, BAR_SPEAKEASY_ID]:
            await conn.execute(text("INSERT INTO user_company_roles (id, user_id, company_id, role_id, tenant_id, scopes, version_id, is_active, is_new) VALUES (gen_random_uuid(), :uid, :cid, (SELECT id FROM roles WHERE company_id = :cid LIMIT 1), :cid, :scopes, 1, true, false) ON CONFLICT DO NOTHING;"), {"uid": users[0][0], "cid": cid, "scopes": tony_scopes})

        # Asignar a TROPY: Solo un bar operario
        tropy_scopes = '["inv:movements:manage"]'
        await conn.execute(text("INSERT INTO user_company_roles (id, user_id, company_id, role_id, tenant_id, scopes, version_id, is_active, is_new) VALUES (gen_random_uuid(), :uid, :cid, (SELECT id FROM roles WHERE company_id = :cid LIMIT 1), :cid, :scopes, 1, true, false) ON CONFLICT DO NOTHING;"), {"uid": users[1][0], "cid": BAR_TERRAZA_ID, "scopes": tropy_scopes})

        # Asignar a GARRY: Distribuidor Admin de Inventario
        garry_scopes = '["inv:movements:manage", "inv:warehouse:manage"]'
        await conn.execute(text("INSERT INTO user_company_roles (id, user_id, company_id, role_id, tenant_id, scopes, version_id, is_active, is_new) VALUES (gen_random_uuid(), :uid, :cid, (SELECT id FROM roles WHERE company_id = :cid LIMIT 1), :cid, :scopes, 1, true, false) ON CONFLICT DO NOTHING;"), {"uid": users[2][0], "cid": DISTRIBUIDOR_ID, "scopes": garry_scopes})

        # Asignar a ARELI: Auditor Externo (Solo lectura de todas las empresas)
        areli_scopes = '["inv:movements:read", "inv:audit:read"]'
        for cid in [DISTRIBUIDOR_ID, BAR_TERRAZA_ID, BAR_IRLANDES_ID, BAR_SPEAKEASY_ID]:
            await conn.execute(text("INSERT INTO user_company_roles (id, user_id, company_id, role_id, tenant_id, scopes, version_id, is_active, is_new) VALUES (gen_random_uuid(), :uid, :cid, (SELECT id FROM roles WHERE company_id = :cid LIMIT 1), :cid, :scopes, 1, true, false) ON CONFLICT DO NOTHING;"), {"uid": users[3][0], "cid": cid, "scopes": areli_scopes})

        # Asignar a CHARLY: Global Admin
        for cid in [DISTRIBUIDOR_ID, BAR_TERRAZA_ID, BAR_IRLANDES_ID, BAR_SPEAKEASY_ID]:
            await conn.execute(text("INSERT INTO user_company_roles (id, user_id, company_id, role_id, tenant_id, scopes, version_id, is_active, is_new) VALUES (gen_random_uuid(), :uid, :cid, (SELECT id FROM roles WHERE company_id = :cid LIMIT 1), :cid, '[ \"*\" ]', 1, true, false) ON CONFLICT DO NOTHING;"), {"uid": CHARLY_ID, "cid": cid})

    print("  [SUCCESS] Auth DB actualizada con Múltiples Usuarios (Tony, Tropy, Garry, Areli, Charly).")

    # ==========================================
    # 2. MASTER DB (Catálogos y UOMs)
    # ==========================================
    created_products = [] 
    async with engine_master.begin() as conn:
        await conn.execute(text("INSERT INTO uoms (id, name, code, abbreviation, is_active, version_id, company_id, tenant_id) VALUES (:id, 'Caja 24', 'CJ24', 'CJ24', true, 1, :cid, :cid) ON CONFLICT DO NOTHING;"), {"id": UOM_CAJA, "cid": DISTRIBUIDOR_ID})
        await conn.execute(text("INSERT INTO uoms (id, name, code, abbreviation, is_active, version_id, company_id, tenant_id) VALUES (:id, 'Botella 750ml', 'BTL', 'BTL', true, 1, :cid, :cid) ON CONFLICT DO NOTHING;"), {"id": UOM_BOTELLA, "cid": DISTRIBUIDOR_ID})

        async def _insert_cat_master(catalog, prefix, pcat, default_uom):
            for i, (name, root_price) in enumerate(catalog):
                pid = str(uuid.uuid4())
                sku = f"{prefix}-{str(i+1).zfill(3)}"
                await conn.execute(text("""
                    INSERT INTO products (id, sku, name, is_active, version_id, company_id, tenant_id, product_type, base_uom_id, requires_batch, requires_expiration, status)
                    VALUES (:id, :sku, :name, true, 1, :cid, :cid, 'GOODS', :uom, false, false, 'ACTIVE')
                    ON CONFLICT DO NOTHING;
                """), {"id": pid, "sku": sku, "name": name, "cid": DISTRIBUIDOR_ID, "cat": pcat, "uom": default_uom})
                created_products.append((pid, sku, name, pcat, root_price, default_uom))

        await _insert_cat_master(CERVEZAS, "BEER", "CERVEZA", UOM_CAJA)
        await _insert_cat_master(BOTELLAS, "LIQ", "DESTILADOS", UOM_BOTELLA)
    print("  [SUCCESS] Master Data DB actualizada (SKUs insertados).")

    # ==========================================
    # 3. INVENTORY DB (Almacenes, Espejo M.D., y Movimientos)
    # ==========================================
    async with engine_inv.begin() as conn:
        await conn.execute(text("INSERT INTO inventory_warehouses (id, name, code, company_id, type, tenant_id, is_active, version_id, is_transit, country_code) VALUES (:id, 'Centro Distribución Global (WH-01)', 'WH-01', :cid, 'PHYSICAL', :cid, true, 1, false, 'MX') ON CONFLICT DO NOTHING;"), {"id": WH_DISTRIBUIDOR, "cid": DISTRIBUIDOR_ID})
        await conn.execute(text("INSERT INTO inventory_warehouses (id, name, code, company_id, type, tenant_id, is_active, version_id, is_transit, country_code) VALUES (:id, 'Almacén de Tránsito (Limbo)', 'WH-TRANSIT', :cid, 'TRANSIT', :cid, true, 1, true, 'MX') ON CONFLICT DO NOTHING;"), {"id": WH_TRANSIT, "cid": DISTRIBUIDOR_ID})
        


        # Borrar movimientos viejos de Test para limpiar el reporting
        await conn.execute(text("DELETE FROM inventory_movements WHERE company_id = :cid;"), {"cid": DISTRIBUIDOR_ID})

        movements_inserted = 0
        for prod_id, sku, name, pcat, price, uom in created_products:
            # 1. Compra de abastecimiento (Hace 20 días)
            qty_in = random.randint(100, 500) if pcat == "CERVEZA" else random.randint(20, 100)
            in_cost = price * 0.75 # 25% margin
            
            await conn.execute(text("""
                INSERT INTO inventory_movements (id, warehouse_id, product_id, company_id, tenant_id, quantity, uom_id, weight, currency, unit_price, movement_type, document_type, document_id, created_at, created_by, comments, is_active, version_id, available_quantity)
                VALUES (gen_random_uuid(), :wh, :prod, :cid, :cid, :qty, :uom, :qty, 'MXN', :cost, 'IN', 'PO_INBOUND', gen_random_uuid(), :time, :uid, :notes, true, 1, :qty)
            """), {"wh": WH_DISTRIBUIDOR, "prod": prod_id, "cid": DISTRIBUIDOR_ID, "qty": float(qty_in), "uom": uom, "cost": float(in_cost), "time": now_minus(20, 5), "uid": CHARLY_ID, "notes": json.dumps({"proveedor": "Compra Directa Proveedores Mayoreo"})})
            movements_inserted += 1

            # 2. Ventas a los diferentes Bares (Hace 1 a 15 días)
            for _ in range(random.randint(1, 3)):
                qty_out = random.randint(2, 15) if pcat == "CERVEZA" else random.randint(1, 5)
                client = random.choice(["Bar La Terraza VIP", "El Pub Irlandés", "Speakeasy 1920 Premium"])
                
                await conn.execute(text("""
                    INSERT INTO inventory_movements (id, warehouse_id, product_id, company_id, tenant_id, quantity, uom_id, weight, currency, unit_price, movement_type, document_type, document_id, created_at, created_by, comments, is_active, version_id, available_quantity)
                    VALUES (gen_random_uuid(), :wh, :prod, :cid, :cid, :qty, :uom, :weight, 'MXN', :price, 'OUT', 'SALES_ORDER', gen_random_uuid(), :time, :uid, :notes, true, 1, 0)
                """), {"wh": WH_DISTRIBUIDOR, "prod": prod_id, "cid": DISTRIBUIDOR_ID, "qty": float(-qty_out), "weight": float(qty_out), "uom": uom, "price": float(price), "time": now_minus(random.randint(1, 15), random.randint(0, 12)), "uid": CHARLY_ID, "notes": json.dumps({"cliente": client})})
                movements_inserted += 1

        # Casos de merma/forenses con PENDING_FINANCIAL_VALUATION (Precios Volátiles o Nulos)
        moet = next((p for p in created_products if "MOET CHAMPAGNE" in p[2]), None)
        if moet:
            await conn.execute(text("""
                INSERT INTO inventory_movements (id, warehouse_id, product_id, company_id, tenant_id, quantity, uom_id, weight, currency, unit_price, movement_type, document_type, document_id, created_at, created_by, comments, is_active, version_id, available_quantity)
                VALUES (gen_random_uuid(), :wh, :prod, :cid, :cid, :qty, :uom, 1.0, 'MXN', 0.0, 'OUT', 'ADJUSTMENT', gen_random_uuid(), :time, :uid, :notes, true, 1, 0)
            """), {"wh": WH_DISTRIBUIDOR, "prod": moet[0], "cid": DISTRIBUIDOR_ID, "qty": -1.0, "uom": moet[5], "time": now_minus(1, 1), "uid": CHARLY_ID, "notes": json.dumps({"issue": "Merma sin reportar / Botella Rota", "status": "PENDING_FINANCIAL"})})
            movements_inserted += 1

    print(f"  [SUCCESS] Inventory DB completada con {movements_inserted} transacciones masivas.")
    print("[SIMULACIÓN COMPLETADA Y EN LÍNEA!]")
    
    await engine_auth.dispose()
    await engine_master.dispose()
    await engine_inv.dispose()

if __name__ == "__main__":
    asyncio.run(run_simulation())
