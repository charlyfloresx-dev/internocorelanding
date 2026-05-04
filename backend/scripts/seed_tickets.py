
import asyncio
import uuid
import sys
import os
from datetime import datetime, timezone

# Add tickets_app to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tickets_service'))

from common.infrastructure.database import AsyncSessionLocal
from tickets_app.models.ticket import Ticket
from tickets_app.core.constants import TicketStatus, TicketPriority, TicketType

async def seed_tickets():
    async with AsyncSessionLocal() as session:
        ENTERPRISE_ID = "9cd9986b-89da-48b7-8733-26a2a1225b01"
        CHARLY_ID = "69aa5ddc-bbaa-46e6-a7f0-aeb4b92b6d38"
        
        tickets = []
        
        # 5 Tickets for IT (unassigned, but area="IT")
        for i in range(1, 6):
            tickets.append(Ticket(
                id=uuid.uuid4(),
                reference_code=f"IT-2026-{str(i).zfill(3)}",
                title=f"Mantenimiento de Servidor {i}",
                description=f"Revisión rutinaria de logs y actualizaciones de seguridad en el servidor de aplicación {i}.",
                ticket_type=TicketType.MAINTENANCE,
                priority=TicketPriority.MEDIUM,
                status=TicketStatus.NEW,
                area="Sistemas (IT)",
                company_id=ENTERPRISE_ID,
                tenant_id=ENTERPRISE_ID,
                is_active=True,
                version_id=1
            ))
            
        # 1 Ticket assigned to Charly directly
        tickets.append(Ticket(
            id=uuid.uuid4(),
            reference_code="SEC-2026-001",
            title="Auditoría de Roles y Permisos (Urgente)",
            description="Revisar que los accesos al entorno de producción de NexoSuite estén restringidos solo al personal autorizado.",
            ticket_type=TicketType.SUPPORT,
            priority=TicketPriority.CRITICAL,
            status=TicketStatus.IN_PROGRESS,
            area="Seguridad de la Información",
            assigned_to_id=CHARLY_ID,
            company_id=ENTERPRISE_ID,
            tenant_id=ENTERPRISE_ID,
            is_active=True,
            version_id=1
        ))
        
        session.add_all(tickets)
        await session.commit()
        print("Successfully seeded 6 tickets (5 for IT, 1 for Charly).")

if __name__ == "__main__":
    asyncio.run(seed_tickets())
