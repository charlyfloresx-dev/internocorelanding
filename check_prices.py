import json
from sqlalchemy import create_engine, text

def check():
    url_inv = "postgresql://user:internocore_db_pass_2026@localhost:5433/inventory_db"
    url_md = "postgresql://user:internocore_db_pass_2026@localhost:5433/master_data_db"
    
    print("=== INVENTORY VARIANTS ===")
    try:
        engine = create_engine(url_inv)
        with engine.connect() as conn:
            res = conn.execute(text("SELECT id, internal_sku, brand, mfg_part_number, unit_price FROM inventory_item_variants"))
            for r in res.fetchall():
                print(r)
    except Exception as e:
        print("Error:", e)
        
    print("\n=== MASTER DATA PRODUCTS WITH COMPANY ===")
    try:
        engine = create_engine(url_md)
        with engine.connect() as conn:
            res = conn.execute(text("SELECT id, name, sku, company_id FROM products WHERE sku IN ('ECM-600', 'TRB-700')"))
            for r in res.fetchall():
                print(r)
    except Exception as e:
        print("Error:", e)
        
    print("\n=== MASTER DATA PRODUCT PRICES ===")
    try:
        engine = create_engine(url_md)
        with engine.connect() as conn:
            res = conn.execute(text("""
                SELECT p.sku, pp.amount, pp.currency, pp.company_id 
                FROM product_prices pp 
                JOIN products p ON pp.product_id = p.id
                WHERE p.sku IN ('ECM-600', 'TRB-700')
            """))
            for r in res.fetchall():
                print(r)
    except Exception as e:
        print("Error:", e)

    print("\n=== MASTER DATA PRICE AGREEMENTS ===")
    try:
        engine = create_engine(url_md)
        with engine.connect() as conn:
            res = conn.execute(text("""
                SELECT p.sku, pa.amount, pa.currency, pa.company_id, pa.partner_id
                FROM price_agreements pa
                JOIN products p ON pa.product_id = p.id
                WHERE p.sku IN ('ECM-600', 'TRB-700')
            """))
            for r in res.fetchall():
                print(r)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    check()
