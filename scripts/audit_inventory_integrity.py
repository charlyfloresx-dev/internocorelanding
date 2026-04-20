import os
import sys
from decimal import Decimal
from typing import Dict, Tuple

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

def run_audit():
    print(">>> Starting InternoCore Inventory Integrity Audit...")
    print(f"Connecting to: {'RDS (Production)' if 'amazonaws.com' in DB_URL else 'Local/Docker Database'}")
    
    try:
        # Use a safe connection with timeout
        conn = psycopg2.connect(DB_URL, connect_timeout=5)
        cur = conn.cursor()
        
        # 1. Aggregate Ledger (Transactions)
        print("[STEP 1] Aggregating Ledger movements (inventory_movements)...")
        cur.execute("""
            SELECT product_id, warehouse_id, SUM(quantity) as ledger_qty
            FROM inventory_movements
            GROUP BY product_id, warehouse_id;
        """)
        ledger_data = {(row[0], row[1]): row[2] for row in cur.fetchall()}
        
        # 2. Get Physical Stock 
        print("[STEP 2] Fetching Current Stock (inventory_levels)...")
        cur.execute("""
            SELECT product_id, warehouse_id, quantity as stock_qty
            FROM inventory_levels;
        """)
        stock_data = {(row[0], row[1]): row[2] for row in cur.fetchall()}
        
        # 3. Comparison
        print("\n[STEP 3] Comparison Results:")
        print("-" * 80)
        
        discrepancies = 0
        all_keys = set(ledger_data.keys()) | set(stock_data.keys())
        
        for key in all_keys:
            pid, wid = key
            l_qty = Decimal(str(ledger_data.get(key, 0)))
            s_qty = Decimal(str(stock_data.get(key, 0)))
            diff = abs(l_qty - s_qty)
            
            if diff > Decimal("0.0001"):
                discrepancies += 1
                print(f"!!! DISCREPANCY: P:{pid} W:{wid} | Ledger:{l_qty:>10} Stock:{s_qty:>10} | Diff:{diff:>10}")
        
        if discrepancies == 0:
            print("OK: AUDIT PASSED: No discrepancies found between Ledger and Stock.")
        else:
            print(f"\nFAIL: AUDIT FAILED: {discrepancies} integrity issues detected.")
            
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"CRITICAL ERROR during audit: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_audit()
