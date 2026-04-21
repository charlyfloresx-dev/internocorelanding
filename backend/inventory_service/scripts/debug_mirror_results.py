import asyncio
import uuid
from inventory_app.db.session import AsyncSessionLocal
from inventory_app.models.inter_company_transfer import InterCompanyTransfer
from inventory_app.models.document import InventoryDocument
from sqlalchemy import select

async def check():
    async with AsyncSessionLocal() as session:
        # Check ICTs
        res = await session.execute(select(InterCompanyTransfer))
        icts = res.scalars().all()
        print(f"Total InterCompanyTransfers: {len(icts)}")
        for ict in icts:
            print(f" - Folio: {ict.folio}, Status: {ict.status}, Mirror ID: {ict.mirror_document_id}")
            
        # Check Mirror Documents (Entry Drafts in B)
        res_docs = await session.execute(select(InventoryDocument).where(InventoryDocument.document_type == "ICT_IN"))
        mirror_docs = res_docs.scalars().all()
        print(f"Total Mirror Documents (ICT_IN): {len(mirror_docs)}")
        for doc in mirror_docs:
            print(f" - Folio: {doc.folio}, Status: {doc.status}, Company: {doc.company_id}")

if __name__ == "__main__":
    asyncio.run(check())
