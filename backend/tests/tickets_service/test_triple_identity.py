import pytest
from uuid import uuid4
from tickets_app.schemas.ticket_dto import TicketCreate
from tickets_app.services.ticket_service import TicketService
from tickets_app.models.ticket import TicketType, TicketPriority
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_external_assignment_requires_contact():
    """Validar que is_external=True requiera external_contact_id (Invariante Pydantic)."""
    with pytest.raises(ValueError, match="Se requiere 'external_contact_id'"):
        TicketCreate(
            title="Prueba Externa Industrial",
            description="Descripción larga para pasar validación de longitud",
            ticket_type="Soporte",
            priority="Baja",
            company_id=uuid4(),
            is_external=True,
            external_contact_id=None
        )

@pytest.mark.asyncio
async def test_external_assignment_sets_assigned_to_null():
    """Validar que al asignar un proveedor, assigned_to_id se limpie (Zero-Consumption)."""
    dto = TicketCreate(
        title="Prueba Externa Industrial",
        description="Descripción larga para pasar validación de longitud",
        ticket_type="Soporte",
        priority="Baja",
        company_id=uuid4(),
        is_external=True,
        external_contact_id=uuid4(),
        assigned_to_id=uuid4() # Se intenta asignar, pero el validador debe limpiarlo
    )
    assert dto.assigned_to_id is None

@pytest.mark.asyncio
async def test_industrial_signal_on_collaborator_only():
    """Verificar el flag [INDUSTRIAL_SIGNAL] al asignar solo Identidad Física."""
    repo = AsyncMock()
    
    # Mock del Ticket retornado
    ticket_mock = MagicMock()
    ticket_mock.id = uuid4()
    ticket_mock.company_id = uuid4()
    ticket_mock.collaborator_id = uuid4()
    ticket_mock.assigned_to_id = None
    ticket_mock.external_contact_id = None
    ticket_mock.reference_code = "TKT-2026-0001"
    ticket_mock.title = "Falla Motor Industrial"
    ticket_mock.ticket_type = TicketType.MAINTENANCE
    ticket_mock.priority = TicketPriority.HIGH
    
    repo.create.return_value = ticket_mock
    repo.get_by_id.return_value = ticket_mock
    
    service = TicketService(repo)
    
    dto = TicketCreate(
        title="Falla Motor Industrial",
        description="Descripción larga para pasar validación de longitud",
        ticket_type="Mantenimiento",
        priority="Alta",
        company_id=ticket_mock.company_id,
        collaborator_id=ticket_mock.collaborator_id,
        assigned_to_id=None
    )
    
    await service.create_ticket(dto, uuid4())
    
    # Verificar que se llamó a add_comment con el SIGNAL por falta de usuario digital
    repo.add_comment.assert_called_once()
    _, kwargs = repo.add_comment.call_args
    assert "[INDUSTRIAL_SIGNAL]" in kwargs["content"]
    assert "Gestión vía Quiosco o Supervisor requerida" in kwargs["content"]

@pytest.mark.asyncio
async def test_external_outbox_event_generation():
    """Verificar que se genera el evento de asignación externa en el Outbox."""
    repo = AsyncMock()
    
    ticket_mock = MagicMock()
    ticket_mock.id = uuid4()
    ticket_mock.company_id = uuid4()
    ticket_mock.external_contact_id = uuid4()
    ticket_mock.reference_code = "TKT-EXT-001"
    ticket_mock.title = "Reparación AC Industrial"
    ticket_mock.ticket_type = TicketType.MAINTENANCE
    ticket_mock.priority = TicketPriority.CRITICAL
    
    repo.create.return_value = ticket_mock
    repo.get_by_id.return_value = ticket_mock
    
    service = TicketService(repo)
    
    dto = TicketCreate(
        title="Reparación AC Industrial",
        description="Descripción larga para pasar validación de longitud",
        ticket_type="Mantenimiento",
        priority="Crítica",
        company_id=ticket_mock.company_id,
        external_contact_id=ticket_mock.external_contact_id,
        is_external=True
    )
    
    await service.create_ticket(dto, uuid4())
    
    # Debe haber 2 eventos: TicketCreatedEvent y ExternalAssignmentEvent
    assert repo.add_outbox_event.call_count == 2
    
    # El segundo evento debe ser ExternalAssignmentEvent
    last_call = repo.add_outbox_event.call_args_list[1]
    _, kwargs = last_call
    assert kwargs["event_type"] == "ExternalAssignmentEvent"
    assert "link_token" in kwargs["payload"]
