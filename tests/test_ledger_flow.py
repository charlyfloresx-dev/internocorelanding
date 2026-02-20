import sys
import os
import pytest
from decimal import Decimal
from sqlalchemy import create_engine, String
from sqlalchemy.orm import sessionmaker, Mapped, mapped_column

# Set PYTHONPATH for local imports
import sys
import os
import pytest
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from wms_service.app.models import InventoryDocument, InventoryMovement, InventorySnapshot, InventoryDocumentStatus, Company, Warehouse
from common.models import BaseEntity, AuditBase, Base
from common.exceptions import BusinessRuleException, NotFoundException

# Clean Architecture: Import Handlers and Commands
from wms_service.app.application.commands import CreateInventoryDocumentCommand, AddMovementCommand, ConfirmDocumentCommand
from wms_service.app.application.handlers import CreateInventoryDocumentHandler, AddMovementHandler, ConfirmDocumentHandler

# 🏛️ Setup Test Infrastructure
# Fixtures handled in conftest.py (Postgres)

# Company model imported from wms_service.app.models

# --- 🧪 Test Scenarios ---

def test_ledger_flow_confirmation(session):
    """
    Escenario A: Confirmación de Documento via HANDLERS.
    Verifica que el Snapshot se actualice con stock y CPP correcto.
    """
    company_id = "tenant-a"
    warehouse_id = "wh-a"

    # Setup Tenant & Warehouse
    # We need to insert Company manually because Auth service is not involved here
    # session.exec(f"INSERT INTO companies (id, name, created_at) VALUES ('{company_id}', 'Company A', NOW()) ON CONFLICT DO NOTHING")
    # session.commit()
    # Actually, using ORM is safer if mapping exists. 
    # But Company model is not in WMS service, it's mocked here or in common?
    # Common has Base classes but not the Company logic (it's in Auth).
    # We defined a dummy Company class above, let's use it.
    
    # Check if company exists (idempotency for test reruns if DB persists)
    if not session.get(Company, company_id):
        session.add(Company(id=company_id, name="Company A"))
    
    if not session.get(Warehouse, warehouse_id):
        session.add(Warehouse(id=warehouse_id, company_id=company_id, code="WH-01", name="Main Warehouse"))
        
    session.commit()

    # Handlers
    create_handler = CreateInventoryDocumentHandler(session)
    add_mov_handler = AddMovementHandler(session)
    confirm_handler = ConfirmDocumentHandler(session)

    # Step 1: Create Document (Command)
    cmd_create = CreateInventoryDocumentCommand(
        folio="ENT-001",
        warehouse_id=warehouse_id,
        concept_id="concept-in"
    )
    doc = create_handler.handle(cmd_create, company_id)
    assert doc.status == InventoryDocumentStatus.DRAFT
    
    # Step 2: Add Movements
    cmd_mov1 = AddMovementCommand(
        document_id=doc.id,
        product_id="prod-1",
        warehouse_id=warehouse_id,
        quantity=Decimal("10.0"),
        unit_cost=Decimal("100.0")
    )
    add_mov_handler.handle(cmd_mov1, company_id)

    cmd_mov2 = AddMovementCommand(
        document_id=doc.id,
        product_id="prod-1",
        warehouse_id=warehouse_id,
        quantity=Decimal("5.0"),
        unit_cost=Decimal("160.0")
    )
    add_mov_handler.handle(cmd_mov2, company_id)
    
    session.commit()

    # Step 3: Transition to CONFIRMED
    cmd_confirm = ConfirmDocumentCommand(document_id=doc.id)
    confirm_handler.handle(cmd_confirm, company_id)
    session.commit()

    # Step 4: Verify Snapshot
    snapshot = session.query(InventorySnapshot).filter_by(product_id="prod-1", company_id=company_id).first()
    assert snapshot is not None
    assert float(snapshot.stock_on_hand) == 15.0
    # Expected CPP: ((10 * 100) + (5 * 160)) / 15 = 1800 / 15 = 120
    assert float(snapshot.average_cost) == 120.0

def test_ledger_immutability_locking(session):
    """
    Escenario B: Inmutabilidad.
    Valida que no se puedan editar movimientos de documentos confirmados.
    """
    company_id = "tenant-imm"
    warehouse_id = "wh-imm"

    if not session.get(Company, company_id):
        session.add(Company(id=company_id, name="Company IMM"))
        
    if not session.get(Warehouse, warehouse_id):
        session.add(Warehouse(id=warehouse_id, company_id=company_id, code="WH-IMM", name="Imm Warehouse"))
        
    session.commit()

    create_handler = CreateInventoryDocumentHandler(session)
    add_mov_handler = AddMovementHandler(session)
    confirm_handler = ConfirmDocumentHandler(session)
    
    # Create & Confirm
    doc = create_handler.handle(CreateInventoryDocumentCommand(folio="FIX-001", warehouse_id=warehouse_id, concept_id="in"), company_id)
    add_mov_handler.handle(AddMovementCommand(document_id=doc.id, product_id="prod-imm", warehouse_id=warehouse_id, quantity=Decimal("10"), unit_cost=Decimal("100")), company_id)
    confirm_handler.handle(ConfirmDocumentCommand(document_id=doc.id), company_id)
    session.commit()

    # Attempt to Add Movement to Confirmed Doc
    with pytest.raises(BusinessRuleException) as excinfo:
        add_mov_handler.handle(AddMovementCommand(document_id=doc.id, product_id="prod-imm", warehouse_id=warehouse_id, quantity=Decimal("5"), unit_cost=Decimal("100")), company_id)
    
    assert "CONFIRMED" in str(excinfo.value)
    session.rollback()

def test_ledger_multi_tenant_isolation(session):
    """
    Escenario C: Aislamiento Multi-tenant via Handlers.
    """
    id_a = "tenant-a-iso"
    wh_a = "wh-a-iso"
    id_b = "tenant-b-iso"
    wh_b = "wh-b-iso"
    
    if not session.get(Company, id_a): session.add(Company(id=id_a, name="Company A"))
    if not session.get(Company, id_b): session.add(Company(id=id_b, name="Company B"))
    
    if not session.get(Warehouse, wh_a): session.add(Warehouse(id=wh_a, company_id=id_a, code="W01", name="Wh A"))
    if not session.get(Warehouse, wh_b): session.add(Warehouse(id=wh_b, company_id=id_b, code="W01", name="Wh B"))
    
    session.commit()

    # Handlers for A
    h_create = CreateInventoryDocumentHandler(session)
    h_add = AddMovementHandler(session)
    h_confirm = ConfirmDocumentHandler(session)

    # Tenant A Action
    doc_a = h_create.handle(CreateInventoryDocumentCommand(folio="E1", warehouse_id=wh_a, concept_id="in"), id_a)
    h_add.handle(AddMovementCommand(document_id=doc_a.id, product_id="P1", warehouse_id=wh_a, quantity=Decimal("50"), unit_cost=Decimal("10")), id_a)
    h_confirm.handle(ConfirmDocumentCommand(document_id=doc_a.id), id_a)
    session.commit()

    # Verify Company B has NO snapshot for P1
    snap_b = session.query(InventorySnapshot).filter_by(product_id="P1", company_id=id_b).first()
    assert snap_b is None

    # Verify Company A has 50 units
    snap_a = session.query(InventorySnapshot).filter_by(product_id="P1", company_id=id_a).first()
    assert float(snap_a.stock_on_hand) == 50.0

def test_ledger_wac_calculation_three_movements(session):
    """
    Escenario D: Cálculo de Costo Promedio Ponderado (3 Movimientos).
    Valida la precisión del cálculo con múltiples entradas.
    """
    company_id = "tenant-wac"
    warehouse_id = "wh-wac"
    product_id = "prod-wac"
    
    # Ensure Tenant Exists
    if not session.get(Company, company_id):
        session.add(Company(id=company_id, name="Company WAC"))
    
    if not session.get(Warehouse, warehouse_id):
        session.add(Warehouse(id=warehouse_id, company_id=company_id, code="WH-WAC", name="WAC Warehouse"))
        
    session.commit()

    # Handlers
    create_handler = CreateInventoryDocumentHandler(session)
    add_mov_handler = AddMovementHandler(session)
    confirm_handler = ConfirmDocumentHandler(session)

    # 1. Create Document
    doc = create_handler.handle(
        CreateInventoryDocumentCommand(folio="WAC-001", warehouse_id=warehouse_id, concept_id="in"), 
        company_id
    )

    # 2. Add 3 Distinct Movements
    # Mov 1: 10 units @ $10.00 = $100.00
    add_mov_handler.handle(
        AddMovementCommand(document_id=doc.id, product_id=product_id, warehouse_id=warehouse_id, quantity=Decimal("10"), unit_cost=Decimal("10.00")), 
        company_id
    )
    # Mov 2: 20 units @ $12.00 = $240.00
    add_mov_handler.handle(
        AddMovementCommand(document_id=doc.id, product_id=product_id, warehouse_id=warehouse_id, quantity=Decimal("20"), unit_cost=Decimal("12.00")), 
        company_id
    )
    # Mov 3: 5 units @ $15.00 = $75.00
    add_mov_handler.handle(
        AddMovementCommand(document_id=doc.id, product_id=product_id, warehouse_id=warehouse_id, quantity=Decimal("5"), unit_cost=Decimal("15.00")), 
        company_id
    )
    session.commit()

    # 3. Confirm Document
    confirm_handler.handle(ConfirmDocumentCommand(document_id=doc.id), company_id)
    session.commit()

    # 4. Validate WAC
    # Total Qty = 10 + 20 + 5 = 35
    # Total Value = 100 + 240 + 75 = 415
    # Expected WAC = 415 / 35 = 11.8571428...
    
    snapshot = session.query(InventorySnapshot).filter_by(product_id=product_id, company_id=company_id).first()
    assert snapshot is not None
    
    stock = float(snapshot.stock_on_hand)
    cost = float(snapshot.average_cost)
    
    assert stock == 35.0
    # Allow small tolerance for floating point comparison if DB returns floats, 
    # but logically it should be very close.
    expected_cost = 415.0 / 35.0
    assert abs(cost - expected_cost) < 0.0001
    
    print(f"WAC Validated: Stock={stock}, CPP={cost} (Expected ~{expected_cost})")
