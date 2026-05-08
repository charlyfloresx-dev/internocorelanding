import asyncio
import uuid
import sys
import os
import traceback
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

# Path setup
_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

# Service specific paths for Monolith imports
sys.path.insert(0, os.path.join(_BACKEND, "tickets_service"))
sys.path.insert(0, os.path.join(_BACKEND, "hcm_service"))
sys.path.insert(0, os.path.join(_BACKEND, "master_data_service"))

# Import models
from tickets_app.models.ticket import Ticket, TicketStatus, TicketPriority
from hcm_app.models.collaborator import Collaborator
from common.models.external_contact import ExternalContact

# MONOLITH DB URL (Shared database 'dbname' in Monolith mode)
MONOLITH_DB_URL = "postgresql+asyncpg://user:password@localhost:5433/dbname"

# Fixed IDs from unified seed
COMPANY_ID = uuid.UUID("9cd9986b-89da-48b7-8733-26a2a1225b01")
USER_CHARLY_ID = uuid.UUID("69aa5ddc-bbaa-46e6-a7f0-aeb4b92b6d38")

async def run_triple_identity_flow():
    print("=" * 60)
    print("FLOW: TRIPLE IDENTITY TICKET LIFECYCLE (MONOLITH MODE)")
    print("Validating: Internal, Plant, and External assignments")
    print("=" * 60)

    # 1. Resolve Identities
    engine = create_async_engine(MONOLITH_DB_URL)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    collab_id = None
    contact_id = None

    try:
        async with Session() as session:
            # Resolve a collaborator
            res = await session.execute(select(Collaborator).limit(1))
            c = res.scalars().first()
            if c:
                collab_id = c.id
                print(f"Found Collaborator: {c.full_name} ({collab_id})")
            else:
                print("WARNING: No Collaborator found in DB.")
        
            # Resolve an external contact
            res = await session.execute(select(ExternalContact).limit(1))
            c = res.scalars().first()
            if c:
                contact_id = c.id
                print(f"Found External Contact: {c.full_name} ({contact_id})")
            else:
                print("WARNING: No External Contact found in DB.")

            if not collab_id or not contact_id:
                print("\nERROR: Could not find required test identities. Ensure unified_industrial_seed.py was executed.")
                return

            # 2. Create and Process Tickets
            print("\n[STEP 1] Creating 3 Tickets...")
            
            t1 = Ticket(
                id=uuid.uuid4(),
                company_id=COMPANY_ID,
                tenant_id=COMPANY_ID,
                title="Internal IT Support",
                description="Issue with internal workstation - Unified Flow",
                priority=TicketPriority.MEDIUM,
                status=TicketStatus.NEW,
                created_by=USER_CHARLY_ID,
                reference_code=f"TKT-INT-{uuid.uuid4().hex[:4].upper()}"
            )
            
            t2 = Ticket(
                id=uuid.uuid4(),
                company_id=COMPANY_ID,
                tenant_id=COMPANY_ID,
                title="Plant Maintenance",
                description="Machine #4 failure in Line A - Unified Flow",
                priority=TicketPriority.HIGH,
                status=TicketStatus.NEW,
                created_by=USER_CHARLY_ID,
                reference_code=f"TKT-PLT-{uuid.uuid4().hex[:4].upper()}"
            )

            t3 = Ticket(
                id=uuid.uuid4(),
                company_id=COMPANY_ID,
                tenant_id=COMPANY_ID,
                title="External Vendor Repair",
                description="Cooling system repair needed by provider - Unified Flow",
                priority=TicketPriority.CRITICAL,
                status=TicketStatus.NEW,
                created_by=USER_CHARLY_ID,
                reference_code=f"TKT-EXT-{uuid.uuid4().hex[:4].upper()}"
            )

            session.add_all([t1, t2, t3])
            await session.commit()
            print(f"Tickets created: {t1.reference_code}, {t2.reference_code}, {t3.reference_code}")

            # [STEP 2] Triage / Assignment
            print("\n[STEP 2] Performing Triple Identity Assignment...")
            
            # Ticket 1 -> Internal Technician
            t1.status = TicketStatus.ASSIGNED
            t1.assigned_to_id = USER_CHARLY_ID
            
            # Ticket 2 -> Plant Collaborator
            t2.status = TicketStatus.ASSIGNED
            t2.collaborator_id = collab_id
            
            # Ticket 3 -> External Provider
            t3.status = TicketStatus.ASSIGNED
            t3.external_contact_id = contact_id
            t3.external_assigned_at = datetime.now(timezone.utc)
            
            await session.commit()
            print("OK  Assignments committed.")

            # [STEP 3] Close Tickets
            print("\n[STEP 3] Closing all tickets...")
            for t in [t1, t2, t3]:
                t.status = TicketStatus.RESOLVED
                t.resolved_at = datetime.now(timezone.utc)
            
            await session.commit()
            print("OK  All tickets RESOLVED.")

            print("\n" + "="*60)
            print("SUCCESS: Triple Identity Monolith Flow Completed.")
            print("="*60)

    except Exception:
        print("\nFATAL ERROR during flow execution")
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_triple_identity_flow())
