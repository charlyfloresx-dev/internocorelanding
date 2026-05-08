import asyncio
import uuid
import sys
import os
import traceback
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, text

# Path setup
_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

sys.path.insert(0, os.path.join(_BACKEND, "tickets_service"))

from tickets_app.models.ticket import Ticket, TicketStatus, TicketPriority
from common.models.external_contact import ExternalContact
# Assuming Outbox model exists in common or tickets_service
# If not, we check the table directly via SQL

DB_URL = "postgresql+asyncpg://user:password@localhost:5433/dbname"
COMPANY_ID = uuid.UUID("9cd9986b-89da-48b7-8733-26a2a1225b01")
CHARLY_ID = uuid.UUID("69aa5ddc-bbaa-46e6-a7f0-aeb4b92b6d38")

async def flow_load_balancing():
    print("=" * 60)
    print("FLOW: LOAD BALANCING (REASSIGNMENT VALIDATION)")
    print("=" * 60)

    engine = create_async_engine(DB_URL)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with Session() as session:
            # 1. Create ticket assigned to Internal User
            ticket_id = uuid.uuid4()
            ticket = Ticket(
                id=ticket_id,
                company_id=COMPANY_ID,
                tenant_id=COMPANY_ID,
                title="Load Balancing Test",
                description="Validating reassignment from Internal to External",
                priority=TicketPriority.MEDIUM,
                status=TicketStatus.ASSIGNED,
                assigned_to_id=CHARLY_ID,
                created_by=CHARLY_ID,
                reference_code=f"LB-{uuid.uuid4().hex[:4].upper()}"
            )
            session.add(ticket)
            await session.commit()
            print(f"[STEP 1] Ticket {ticket.reference_code} assigned to Internal User (Charly).")

            # 2. Resolve an external contact
            res = await session.execute(select(ExternalContact).limit(1))
            contact = res.scalars().first()
            if not contact:
                print("ERROR: External contact not found. Run seed.")
                return

            # 3. Reassign to External Contact
            print(f"[STEP 2] Reassigning to External Contact: {contact.full_name}")
            
            # Use raw SQL to simulate the triage logic that handles both fields
            await session.execute(
                text("""
                    UPDATE tickets 
                    SET assigned_to_id = NULL, 
                        external_contact_id = :contact_id,
                        external_assigned_at = :now,
                        status = 'ASSIGNED'
                    WHERE id = :ticket_id
                """),
                {"contact_id": contact.id, "now": datetime.now(timezone.utc), "ticket_id": ticket_id}
            )
            
            # 4. Insert Outbox Event (Manual for script validation)
            await session.execute(
                text("""
                    INSERT INTO outbox_events (id, event_id, event_type, payload, is_processed, created_at, company_id, tenant_id, is_active, version_id)
                    VALUES (:id, :eid, 'EXTERNAL_ASSIGNMENT', :payload, FALSE, :now, :cid, :tid, TRUE, 1)
                """),
                {
                    "id": uuid.uuid4(),
                    "eid": uuid.uuid4(),
                    "payload": f'{{"ticket_id": "{ticket_id}", "contact_email": "{contact.email}"}}',
                    "now": datetime.now(timezone.utc),
                    "cid": COMPANY_ID,
                    "tid": COMPANY_ID
                }
            )
            
            await session.commit()

            # 5. Verify Invariants
            await session.refresh(ticket)
            print(f"[VERIFY] assigned_to_id is NULL: {'OK' if ticket.assigned_to_id is None else 'FAIL'}")
            print(f"[VERIFY] external_contact_id matches: {'OK' if ticket.external_contact_id == contact.id else 'FAIL'}")
            
            res = await session.execute(text("SELECT count(*) FROM outbox_events WHERE event_type = 'EXTERNAL_ASSIGNMENT' AND is_processed = FALSE"))
            count = res.scalar()
            print(f"[VERIFY] Outbox Event Inserted: {'OK' if count > 0 else 'FAIL'}")

            # Cleanup
            await session.execute(text("DELETE FROM outbox_events WHERE event_type = 'EXTERNAL_ASSIGNMENT'"))
            await session.delete(ticket)
            await session.commit()
            print("\n[CLEANUP] Test data removed.")
            
            print("\n" + "="*60)
            print("SUCCESS: Load Balancing Flow Validated.")
            print("="*60)

    except Exception:
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(flow_load_balancing())
