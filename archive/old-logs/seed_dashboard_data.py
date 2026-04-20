import uuid
import random
from datetime import datetime, timedelta, timezone

# Configuration
COMPANY_ID = "9cd9986b-89da-48b7-8733-26a2a1225b01"
WAREHOUSES = [
    "536d182d-3447-5788-87d9-e488ae0af797", # MAIN
    "22222222-2222-2222-2222-222222222222", # TIJ
    "bb18f763-3f93-53af-9fb8-ca1c752f3873", # TRANSIT
    "33333333-3333-3333-3333-333333333333"  # CALIDAD (Hypothetical/Corrected)
]
PRODUCTS = [
    "73acb311-dd79-5f5c-bfe8-dc872aace290", # MAT-001
    "db856803-a63d-5468-9a7c-9039702acca9", # MAT-005
    "83acb311-dd79-5f5c-bfe8-dc872aace290", # Dummy 3
    "93acb311-dd79-5f5c-bfe8-dc872aace290"  # Dummy 4
]
UOM_ID = "550e8400-e29b-41d4-a716-446655440000" # Fixed UOM for consistency

def generate_sql():
    sql_commands = [
        "-- SEED DATA FOR MISSION CONTROL DASHBOARD",
        f"SET search_path TO public;",
        "DELETE FROM inventory_movements WHERE company_id = '{COMPANY_ID}';",
        "DELETE FROM inventory_levels WHERE company_id = '{COMPANY_ID}';"
    ]
    
    # 2. Seed Levels (to show Valuation)
    for wh_id in WAREHOUSES:
        for prod_id in PRODUCTS:
            qty = random.randint(300, 1500)
            cost = random.uniform(15.0, 120.0)
            sql_commands.append(f"""
                INSERT INTO inventory_levels (id, company_id, warehouse_id, product_id, uom_id, quantity, weighted_average_cost, currency_code, is_active, version_id, created_at)
                VALUES ('{uuid.uuid4()}', '{COMPANY_ID}', '{wh_id}', '{prod_id}', '{UOM_ID}', {qty}, {cost}, 'USD', true, 1, now());
            """)

    # 3. Seed Movements (for the 24h Graph)
    now = datetime.now(timezone.utc)
    for wh_id in WAREHOUSES:
        for i in range(24):
            hour_ago = now - timedelta(hours=i)
            # Entries (IN)
            entries = random.randint(10, 60)
            sql_commands.append(f"""
                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('{uuid.uuid4()}', '{COMPANY_ID}', '{wh_id}', '{random.choice(PRODUCTS)}', '{UOM_ID}', {entries}, 1.5, 'IN', 'ENT', '{uuid.uuid4()}', true, 1, '{hour_ago.strftime('%Y-%m-%d %H:%M:%S')}');
            """)
            # Exits (OUT)
            exits = random.randint(5, 50)
            sql_commands.append(f"""
                INSERT INTO inventory_movements (id, company_id, warehouse_id, product_id, uom_id, quantity, weight, movement_type, document_type, document_id, is_active, version_id, created_at)
                VALUES ('{uuid.uuid4()}', '{COMPANY_ID}', '{wh_id}', '{random.choice(PRODUCTS)}', '{UOM_ID}', {exits}, 1.2, 'OUT', 'SAL', '{uuid.uuid4()}', true, 1, '{hour_ago.strftime('%Y-%m-%d %H:%M:%S')}');
            """)

    # 4. Critical Levels (to trigger alerts)
    for wh_id in WAREHOUSES:
        target_prod = random.choice(PRODUCTS)
        sql_commands.append(f"UPDATE inventory_levels SET quantity = {random.randint(1, 10)} WHERE warehouse_id = '{wh_id}' AND product_id = '{target_prod}';")

    return "\n".join(sql_commands)

if __name__ == "__main__":
    sql = generate_sql()
    with open("seed_dashboard.sql", "w") as f:
        f.write(sql)
    print("Generated seed_dashboard.sql with multi-warehouse coverage.")
