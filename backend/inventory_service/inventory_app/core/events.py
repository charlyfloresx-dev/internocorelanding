from sqlalchemy import event, text
from fastapi import HTTPException
import json
import logging

from common.context import request_context
from inventory_app.models.movement import Movement

logger = logging.getLogger(__name__)

def get_current_values(target):
    """Extrae los valores actuales de la instancia de SQLAlchemy."""
    result = {}
    for column in target.__table__.columns:
        val = getattr(target, column.key)
        if val is not None:
            result[column.key] = str(val)
    return result

class ForensicImmutabilityError(Exception):
    """Excepción lanzada cuando se intenta modificar un registro inmutable."""
    pass

def setup_audit_listeners():
    @event.listens_for(Movement, "after_insert")
    def receive_after_insert(mapper, connection, target):
        try:
            _log_audit(connection, "INSERT", target, None, get_current_values(target))
        except Exception as e:
            logger.error(f"Audit failed in after_insert: {e}")

    @event.listens_for(Movement, "before_update")
    def receive_before_update(mapper, connection, target):
        # Allow updating 'available_quantity' for FIFO consumption tracking.
        # Any other column modifications are strictly blocked.
        from sqlalchemy.orm.attributes import get_history
        # Mutable fields during FIFO discharge:
        # - available_quantity: decremented on IN movements consumed by OUT
        # - source_movement_id: linked on OUT movement for audit traceability
        _MUTABLE_FIELDS = {"available_quantity", "source_movement_id"}
        state = target._sa_instance_state
        for attr in state.mapper.column_attrs:
            if attr.key not in _MUTABLE_FIELDS:
                history = get_history(target, attr.key)
                if history.has_changes():
                    raise ForensicImmutabilityError(
                        f"IMMUTABLE_ERROR: Updates on '{attr.key}' are strictly prohibited on inventory movements."
                    )

    @event.listens_for(Movement, "before_delete")
    def receive_before_delete(mapper, connection, target):
        raise ForensicImmutabilityError(
            "IMMUTABLE_ERROR: Deletions are strictly prohibited on inventory movements."
        )

import uuid
from datetime import datetime
from common.models import AuditLog

def _log_audit(connection, action, target, old_val, new_val):
    """Helper para registrar la auditoria insertando directamente en la BD sincronamente."""
    try:
        table_name = target.__tablename__
        record_id = str(getattr(target, "id", ""))
        
        ctx = request_context.get()
        user_id = ctx.user_id if ctx and getattr(ctx, "user_id", None) else None
        correlation_id = ctx.trace_id if ctx and getattr(ctx, "trace_id", None) else None
        company_id = ctx.company_id if ctx and getattr(ctx, "company_id", None) else getattr(target, "company_id", None)

        if not user_id:
            user_id = str(getattr(target, "created_by", ""))

        old_json = old_val if old_val else None
        new_json = new_val if new_val else None

        # Context IDs as UUID objects if possible
        def to_uuid_str(val):
            if not val: return None
            return str(val)

        # Insert log directly into audit_logs table (Using Table object for better compatibility)
        connection.execute(
            AuditLog.__table__.insert().values(
                id=str(uuid.uuid4()),
                table_name=table_name,
                record_id=record_id,
                action=action,
                old_value=old_json,
                new_value=new_json,
                user_id=to_uuid_str(user_id),
                trace_id=to_uuid_str(correlation_id),
                company_id=to_uuid_str(company_id),
                timestamp=datetime.now()
            )
        )
    except Exception as e:
        logger.error(f"[AUDIT_ERROR] Failed to log {action} on {target.__tablename__}: {str(e)}")
