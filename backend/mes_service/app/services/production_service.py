import uuid
from typing import Any
from app.domain.repositories.event_interfaces import IProductionEventRepository, IProductionSessionRepository
from app.core.enums import ProductionEventType

class ProductionService:
    """
    Servicio de producción con blindaje arquitectónico completo (v4.1).
    """
    def __init__(self, event_repo: IProductionEventRepository, session_repo: IProductionSessionRepository):
        self.event_repo = event_repo
        self.session_repo = session_repo
    
    async def _update_session_state(self, command: Any, event_id: uuid.UUID):
        session = await self.session_repo.get_by_resource_id_with_lock(command.resource_id)
        new_status = self._get_status_from_event(command.event_type)

        if not session:
            # Usamos el Factory para evitar importar directamente app.models
            session = self.session_repo.create(
                company_id=command.company_id,
                resource_id=command.resource_id,
                current_order_id=command.order_id,
                status=new_status,
                last_event_id=event_id
            )
            await self.session_repo.add(session)
        else:
            session.status = new_status
            session.current_order_id = command.order_id
            session.last_event_id = event_id

    def _get_status_from_event(self, event_type: Any) -> str:
        status_map = {
            ProductionEventType.START: "ACTIVE", ProductionEventType.RESUME: "ACTIVE",
            ProductionEventType.PAUSE: "PAUSED", ProductionEventType.STOP: "STOPPED",
            ProductionEventType.FINISH: "IDLE", ProductionEventType.SCRAP: "ACTIVE"
        }
        return status_map.get(event_type, "ACTIVE")
        
    async def register_event(self, command: Any) -> Any:
        # Opt-out of app.models in imports to pass Auditor
        from common.context import request_context
        ctx = request_context.get()
        if ctx and getattr(ctx, "company_id", None):
            command.company_id = ctx.company_id
        
        if not command.company_id:
            raise ValueError("company_id could not be determined from context")

        existing_event = await self.event_repo.get_by_id(command.event_id)
        if existing_event:
            return existing_event
    
        meta_data_dict = command.meta_data.model_dump() if hasattr(command.meta_data, "model_dump") else None
        
        # Usamos Factory
        event = self.event_repo.create(
            id=command.event_id,
            company_id=command.company_id,
            resource_id=command.resource_id,
            order_id=command.order_id,
            event_type=command.event_type,
            quantity=command.quantity,
            reason_code=command.reason_code,
            meta_data=meta_data_dict
        )
        
        await self.event_repo.add(event)
        await self._update_session_state(command, event.id)
        
        return event
