from sqlalchemy import event, text
from sqlalchemy.orm.attributes import get_history
import json

def get_current_values(target):
    """Extrae los valores actuales de la instancia de SQLAlchemy."""
    result = {}
    for column in target.__table__.columns:
        val = getattr(target, column.key)
        # Convert non-serializable objects (like UUID or Decimal) to string
        if val is not None:
            result[column.key] = str(val)
    return result

def setup_audit_listeners(target_class):
    @event.listens_for(target_class, "after_insert")
    def receive_after_insert(mapper, connection, target):
        _log_audit(connection, "INSERT", target, None, get_current_values(target))

    @event.listens_for(target_class, "after_update")
    def receive_after_update(mapper, connection, target):
        old_values = {}
        new_values = {}
        
        for attr in mapper.column_attrs:
            hist = get_history(target, attr.key)
            if hist.has_changes():
                # Extract old and new values, serialize them
                old_val = hist.deleted[0] if hist.deleted else None
                new_val = hist.added[0] if hist.added else None
                
                if old_val is not None:
                    old_values[attr.key] = str(old_val)
                if new_val is not None:
                    new_values[attr.key] = str(new_val)
        
        if old_values or new_values:
            _log_audit(connection, "UPDATE", target, old_values, new_values)

    @event.listens_for(target_class, "after_delete")
    def receive_after_delete(mapper, connection, target):
        _log_audit(connection, "DELETE", target, get_current_values(target), None)

def _log_audit(connection, action, target, old_val, new_val):
    """Helper para registrar la auditoría insertando directamente en la BD síncronamente."""
    table_name = target.__tablename__
    record_id = str(getattr(target, "id", ""))
    user_id = str(getattr(target, "updated_by", getattr(target, "created_by", "")))

    old_json = json.dumps(old_val) if old_val else None
    new_json = json.dumps(new_val) if new_val else None

    # Insert log directly into audit_logs table
    stmt = text("""
        INSERT INTO audit_logs (id, table_name, record_id, action, old_value, new_value, user_id, timestamp)
        VALUES (gen_random_uuid(), :table_name, :record_id, :action, :old_value, :new_value, :user_id, NOW())
    """)
    
    connection.execute(
        stmt,
        {
            "table_name": table_name,
            "record_id": record_id,
            "action": action,
            "old_value": old_json,
            "new_value": new_json,
            "user_id": user_id if user_id else None
        }
    )
