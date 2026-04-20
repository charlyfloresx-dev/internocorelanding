import os
import sys
from decimal import Decimal

# Path injection to access common settings
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    import psycopg2
    from common.config import settings
except ImportError:
    print("CRITICAL: Dependencies or common.config not found. Run from project root.")
    sys.exit(1)

# Database configuration - use unified settings
DB_URL = settings.DATABASE_URL
# Handle asyncpg -> psycopg2 conversion
DB_URL = DB_URL.replace("postgresql+asyncpg://", "postgresql://")

def rebuild_levels():
    print(">>> Starting InternoCore Inventory Level Rebuild (Standardized)...")
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # 1. Clear existing levels
        print("[STEP 1] Truncating inventory_levels...")
        cur.execute("TRUNCATE TABLE inventory_levels CASCADE;")
        
        # 2. Recalculate from Ledger
        print("[STEP 2] Recalculating balances from inventory_movements...")
        cur.execute("""
            SELECT 
                company_id, 
                warehouse_id, 
                product_id, 
                MAX(uom_id::text) as uom_id_str,
                SUM(quantity) as net_qty
            FROM inventory_movements
            GROUP BY company_id, warehouse_id, product_id
            HAVING SUM(quantity) != 0;
        """)
        
        rows = cur.fetchall()
        print(f"[STEP 3] Re-inserting {len(rows)} level records...")
        
        for row in rows:
            company_id, warehouse_id, product_id, uom_id_str, qty = row
            final_uom_id = uom_id_str if uom_id_str else '00000000-0000-0000-0000-000000000001'

            cur.execute("""
                INSERT INTO inventory_levels (
                    id, company_id, tenant_id, warehouse_id, product_id, uom_id, 
                    quantity, reserved_quantity, 
                    wac_amount, wac_currency, 
                    last_price_amount, last_price_currency,
                    replacement_price_amount, replacement_price_currency,
                    is_active, version_id,
                    created_at, updated_at
                )
                VALUES (
                    gen_random_uuid(), %s, %s, %s, %s, %s, 
                    %s, 0, 
                    0, 'USD', 
                    0, 'USD',
                    0, 'USD',
                    True, 1,
                    NOW(), NOW()
                );
            """, (company_id, company_id, warehouse_id, product_id, final_uom_id, qty))
            
        conn.commit()
        print("SUCCESS: Inventory levels consistent with Ledger.")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"CRITICAL ERROR during rebuild: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    rebuild_levels()
