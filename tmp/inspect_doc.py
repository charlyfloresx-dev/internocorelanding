
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def inspect_doc(doc_id):
    try:
        engine_inv = create_async_engine("postgresql+asyncpg://user:password@localhost:5433/inventory_db")
        async with engine_inv.connect() as conn:
            print(f"--- Checking Document: {doc_id} ---")
            
            # Check inventory_documents
            res = await conn.execute(text(f"SELECT * FROM inventory_documents WHERE id = '{doc_id}'"))
            doc = res.fetchone()
            if doc:
                print("Document metadata found:")
                print(doc._mapping)
            else:
                print("Document metadata NOT found in inventory_documents.")
                
            # Check inventory_movements
            res = await conn.execute(text(f"SELECT * FROM inventory_movements WHERE document_id = '{doc_id}'"))
            movements = res.all()
            print(f"\nMovements found ({len(movements)}):")
            for m in movements:
                print(m._mapping)
                
            # Check if warehouse and concept exist in master data (via IDs from movements/doc)
            if doc:
                wh_id = doc.origin_name # actually let's use the field name from the mapping
                # wait, let me use the actual column names from mapping
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await engine_inv.dispose()

if __name__ == "__main__":
    asyncio.run(inspect_doc('12783701-a84a-4c9c-9253-2e326e884e3f'))
