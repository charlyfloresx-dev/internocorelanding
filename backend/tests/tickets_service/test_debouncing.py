import pytest
import json
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from tickets_app.infrastructure.repositories.ticket_repository import SQLAlchemyTicketRepository
from tickets_app.models.outbox import OutboxEvent

@pytest.mark.asyncio
async def test_outbox_event_debouncing():
    """
    Verifica que eventos de outbox idénticos en rápida sucesión 
    (tormentas de eventos) sean ignorados para el mismo ticket.
    """
    mock_session = AsyncMock(spec=AsyncSession)
    repo = SQLAlchemyTicketRepository(mock_session)
    
    company_id = uuid4()
    ticket_id = str(uuid4())
    event_type = "TicketStatusChangedEvent"
    payload = json.dumps({
        "ticket_id": ticket_id,
        "new_status": "in_progress"
    })
    
    # 1. Configuramos el mock para que `execute` devuelva un evento reciente en la primera llamada 
    # simulando que ya se insertó un evento igual hace 1 segundo.
    recent_event = OutboxEvent(
        event_id=uuid4(),
        event_type=event_type,
        payload=payload,
        company_id=company_id,
        created_at=datetime.now(timezone.utc) - timedelta(seconds=1)
    )
    
    # Mocking the select result for the debounce check
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = recent_event
    mock_session.execute.return_value = mock_result
    
    # Intentamos agregar el evento
    await repo.add_outbox_event(
        company_id=company_id,
        event_type=event_type,
        payload=payload
    )
    
    # El repositorio NO debería haber llamado a session.add porque el evento fue debounced
    mock_session.add.assert_not_called()
    mock_session.commit.assert_not_called()

@pytest.mark.asyncio
async def test_outbox_event_no_debouncing_after_window():
    """
    Verifica que después de la ventana de debounce (ej. 10 segundos),
    sí se permita insertar un nuevo evento aunque sea idéntico.
    """
    mock_session = AsyncMock(spec=AsyncSession)
    repo = SQLAlchemyTicketRepository(mock_session)
    
    company_id = uuid4()
    ticket_id = str(uuid4())
    event_type = "TicketStatusChangedEvent"
    payload = json.dumps({
        "ticket_id": ticket_id,
        "new_status": "in_progress"
    })
    
    # Simular que el último evento idéntico fue hace 15 segundos (fuera de ventana).
    # Como la query tiene `WHERE created_at >= debounce_window`, la base de datos no retornaría nada.
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    await repo.add_outbox_event(
        company_id=company_id,
        event_type=event_type,
        payload=payload
    )
    
    # El repositorio SÍ debería haber llamado a session.add
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_outbox_event_different_payload():
    """
    Verifica que eventos con payloads diferentes no sean debounced
    aunque ocurran en el mismo segundo.
    """
    mock_session = AsyncMock(spec=AsyncSession)
    repo = SQLAlchemyTicketRepository(mock_session)
    
    company_id = uuid4()
    event_type = "TicketStatusChangedEvent"
    
    # No hay eventos previos idénticos
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    await repo.add_outbox_event(
        company_id=company_id,
        event_type=event_type,
        payload='{"status": "resolved"}'
    )
    
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
