import sys
import os
from decimal import Decimal
import unittest
from sqlalchemy import create_engine, String
from sqlalchemy.orm import sessionmaker, Mapped, mapped_column

# Set PYTHONPATH for local imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from wms_service.app.models import (
    Base, Warehouse, InventoryDocument, InventoryMovement, 
    InventorySnapshot, InventoryDocumentStatus
)
from common.models import BaseEntity, AuditBase
from common.exceptions import BusinessRuleException

# Dummy Company to satisfy MultiTenantBase Foreign Key
class Company(Base, BaseEntity, AuditBase):
    __tablename__ = "companies"
    name: Mapped[str] = mapped_column(String(100))

class TestReactiveLedger(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Use in-memory SQLite
        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)
        
        # Create persistent test data
        session = cls.Session()
        cls.company_id = "tenant-1"
        company = Company(id=cls.company_id, name="Test Tenant")
        session.add(company)
        
        cls.warehouse = Warehouse(
            id="wh-1", company_id=cls.company_id, code="ALM-01", name="Almacén Central"
        )
        session.add(cls.warehouse)
        session.commit()
        session.close()

    def setUp(self):
        self.session = self.Session()

    def tearDown(self):
        self.session.close()

    def test_stock_update_on_confirmation(self):
        """Verify that status DRAFT -> CONFIRMED updates stock."""
        doc = InventoryDocument(
            id="doc-1", company_id=self.company_id, folio="ENT-001", 
            warehouse_id="wh-1", concept_id="concept-in", status=InventoryDocumentStatus.DRAFT
        )
        mov = InventoryMovement(
            id="mov-1", company_id=self.company_id, document_id="doc-1",
            product_id="prod-1", warehouse_id="wh-1", quantity=10.0, unit_cost=100.0
        )
        self.session.add(doc)
        self.session.add(mov)
        self.session.commit()

        # Trigger update
        doc.status = InventoryDocumentStatus.CONFIRMED
        self.session.commit()

        # Check snapshot
        snapshot = self.session.query(InventorySnapshot).filter_by(product_id="prod-1").first()
        self.assertIsNotNone(snapshot)
        self.assertEqual(float(snapshot.stock_on_hand), 10.0)
        self.assertEqual(float(snapshot.average_cost), 100.0)

    def test_weighted_average_cost(self):
        """Verify WAC calculation."""
        # Initial state (10 units @ 100)
        snapshot = InventorySnapshot(
            company_id=self.company_id, product_id="prod-wac", warehouse_id="wh-1",
            stock_on_hand=10.0, average_cost=100.0
        )
        self.session.add(snapshot)
        self.session.commit()

        # New Inbound (5 units @ 160)
        # Expected new WAC: ((10 * 100) + (5 * 160)) / 15 = 120
        doc = InventoryDocument(
            company_id=self.company_id, folio="ENT-002", 
            warehouse_id="wh-1", concept_id="concept-in", status=InventoryDocumentStatus.DRAFT
        )
        mov = InventoryMovement(
            document=doc, company_id=self.company_id,
            product_id="prod-wac", warehouse_id="wh-1", quantity=5.0, unit_cost=160.0
        )
        self.session.add(doc)
        self.session.commit()

        doc.status = InventoryDocumentStatus.CONFIRMED
        self.session.commit()

        snapshot = self.session.query(InventorySnapshot).filter_by(product_id="prod-wac").first()
        self.assertEqual(float(snapshot.average_cost), 120.0)
        self.assertEqual(float(snapshot.stock_on_hand), 15.0)

    def test_immutability_enforcement(self):
        """Verify that confirmed docs cannot be edited."""
        doc = InventoryDocument(
            company_id=self.company_id, folio="FIXED-001", 
            warehouse_id="wh-1", concept_id="concept-in", status=InventoryDocumentStatus.CONFIRMED
        )
        self.session.add(doc)
        self.session.commit()

        # Try to modify
        doc.folio = "CHANGED"
        with self.assertRaises(BusinessRuleException):
            self.session.commit()
        
        self.session.rollback()

if __name__ == "__main__":
    unittest.main()
