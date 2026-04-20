
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def inspect_db():
    # 1. Check Master Data for Tijuana Central
    engine_md = create_async_engine("postgresql+asyncpg://user:password@localhost:5433/master_data_db")
    async with engine_md.connect() as conn:
        print("--- Master Data: Warehouses ---")
        res = await conn.execute(text("SELECT id, name, code, company_id FROM warehouses WHERE name ILIKE '%Tijuana%'"))
        tij_warehouses = res.all()
        for row in tij_warehouses:
            print(row)
    await engine_md.dispose()

    if not tij_warehouses:
        print("No Tijuana warehouse found in Master Data.")
        return

    # 2. Check Inventory Documents and Movements for those warehouses
    engine_inv = create_async_engine("postgresql+asyncpg://user:password@localhost:5433/inventory_db")
    async with engine_inv.connect() as conn:
        for wh in tij_warehouses:
            wh_id = wh[0]
            print(f"\n--- Inventory for Warehouse: {wh[1]} ({wh_id}) ---")
            
            # Count movements
            res = await conn.execute(text(f"SELECT count(*) FROM inventory_movements WHERE warehouse_id = '{wh_id}'"))
            print(f"Movements count: {res.scalar()}")
            
            # Show last 5 movements
            res = await conn.execute(text(f"SELECT id, movement_type, quantity, product_id, document_id, created_at FROM inventory_movements WHERE warehouse_id = '{wh_id}' ORDER BY created_at DESC LIMIT 5"))
            movements = res.all()
            for m in movements:
                print(m)
                
            # Show documents linked to these movements
            if movements:
                doc_ids = list(set([str(m[4]) for m in movements]))
                doc_ids_str = ", ".join([f"'{d}'" for d in doc_ids])
                print(f"--- Documents: {doc_ids_str} ---")
                res = await conn.execute(text(f"SELECT id, folio, document_type, origin_name, destination_name, concept_id FROM inventory_documents WHERE id IN ({doc_ids_str})"))
                for doc in res.all():
                    print(doc)

    await engine_inv.dispose()

if __name__ == "__main__":
    asyncio.run(inspect_db())
