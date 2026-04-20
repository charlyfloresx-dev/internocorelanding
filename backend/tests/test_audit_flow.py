import pytest
from sqlalchemy.orm import Session
from sqlalchemy import select

# Asumiendo que tienes modelos y un seeder para tus pruebas
from master_data_service.app.models.product import Product
from common.models.audit import AuditLog, ActionType

@pytest.mark.asyncio
async def test_update_product_creates_audit_log(db_session: Session, test_product: Product):
    """
    Verifica que al actualizar un producto, se crea un registro de auditoría
    con los valores 'old' y 'new' correctos.
    """
    # ARRANGE: Tenemos un producto existente
    original_name = test_product.name
    new_name = f"{original_name} - Updated"
    
    product_to_update = db_session.get(Product, test_product.id)
    assert product_to_update is not None

    # ACT: Actualizamos el nombre del producto
    product_to_update.name = new_name
    db_session.commit()
    db_session.refresh(product_to_update)

    # ASSERT: Verificamos que el producto se actualizó
    assert product_to_update.name == new_name

    # ASSERT: Verificamos que se creó el log de auditoría
    stmt = (
        select(AuditLog)
        .where(AuditLog.table_name == 'products')
        .where(AuditLog.record_id == str(product_to_update.id))
        .where(AuditLog.action == ActionType.UPDATE)
        .order_by(AuditLog.timestamp.desc())
    )
    audit_log_entry = db_session.execute(stmt).scalars().first()

    assert audit_log_entry is not None
    assert audit_log_entry.action == ActionType.UPDATE
    assert audit_log_entry.old_value == {"name": original_name}
    assert audit_log_entry.new_value == {"name": new_name}
    assert audit_log_entry.client_ip is not None # El middleware debería haberlo capturado
    assert audit_log_entry.correlation_id is not None
