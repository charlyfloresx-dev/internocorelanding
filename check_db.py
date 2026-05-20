import asyncio
from sqlalchemy import create_engine, text

def check():
    urls = [
        "postgresql://user:internocore_db_pass_2026@localhost:5433/dbname",
        "postgresql://user:internocore_db_pass_2026@localhost:5433/master_data_db",
        "postgresql://user:internocore_db_pass_2026@localhost:5433/inventory_db",
        "postgresql://user:internocore_db_pass_2026@localhost:5433/hcm_db"
    ]
    for url in urls:
        db_name = url.split("/")[-1]
        print(f"\n=== DATABASE: {db_name} ===")
        try:
            engine = create_engine(url)
            with engine.connect() as conn:
                # Get table names
                res = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
                tables = [r[0] for r in res.fetchall()]
                print("Tables:", tables)
                
                if "products" in tables:
                    print("\n--- PRODUCTS ---")
                    p_res = conn.execute(text("SELECT id, name, sku, is_active FROM products LIMIT 10"))
                    for row in p_res.fetchall():
                        print(row)
                
                if "inventory_item_variants" in tables:
                    print("\n--- INVENTORY ITEM VARIANTS ---")
                    v_res = conn.execute(text("SELECT id, internal_sku, brand, mfg_part_number, unit_price FROM inventory_item_variants LIMIT 10"))
                    for row in v_res.fetchall():
                        print(row)
        except Exception as e:
            print(f"Error querying {db_name}: {e}")

if __name__ == "__main__":
    check()
