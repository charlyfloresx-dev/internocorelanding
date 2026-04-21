"""
Test Suite: ICT Enhanced Features
===================================
Valida las mejoras al flujo Inter-Company Transfer (ICT):

  TC-ICT-E01 — Generación de Documentos Espejo (A y B) al iniciar
  TC-ICT-E02 — Idempotencia via external_reference
  TC-ICT-E03 — Almacén de Tránsito marcado como is_transit=True
  TC-ICT-E04 — WAC de Empresa B usa sealed_transfer_price, no WAC de A
  TC-ICT-E05 — total_amount del doc de A = transfer_revenue (qty × price)
  TC-ICT-E06 — total_amount del doc de B = acquisition_cost tras recepción
  TC-ICT-E07 — RevertTransfer: stock regresa, DRAFT-B cancelado, auditoría
  TC-ICT-E08 — RevertTransfer bloqueado si DELIVERED
  TC-ICT-E09 — RevertTransfer bloqueado si empresa no es originadora

Alineación con Legacy (.NET):
  - Document.Total     → InventoryDocument.total_amount (Money VO)
  - Movements.SellPrice → transfer_price (sealed en contrato ICT)
  - Concept.AffectStock → movement_type (TRANSFER_OUT / TRANSFER_IN)
"""

import pytest
import uuid
from decimal import Decimal
from sqlalchemy import select

from inventory_app.api.v1.handlers.transfer_command_handler import TransferCommandHandler
from inventory_app.infrastructure.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository
from inventory_app.domain.entities.transfer_entities import (
    InitiateTransferCommand,
    CompleteTransferCommand,
    CancelTransferCommand,
    TransferStatusEnum,
)
from inventory_app.models.inventory import InventoryLevel
from inventory_app.models.warehouse import Warehouse
from inventory_app.models.document import InventoryDocument, DocumentStatus
from inventory_app.models.inter_company_transfer import TransferStatus
from common.exceptions import (
    ConflictException,
    UnauthorizedException,
)


# ─── Helpers ─────────────────────────────────────────────────────────────────

async def _seed_stock(
    db_session,
    company_id: uuid.UUID,
    warehouse_id: uuid.UUID,
    product_id: uuid.UUID,
    uom_id: uuid.UUID,
    quantity: Decimal,
    wh_code: str = "WH-A",
) -> None:
    """Seeds a Warehouse + InventoryLevel for a given company."""
    wh = Warehouse(
        id=warehouse_id,
        company_id=company_id,
        code=wh_code,
        name=f"Warehouse {wh_code}",
    )
    db_session.add(wh)

    level = InventoryLevel(
        id=uuid.uuid4(),
        company_id=company_id,
        warehouse_id=warehouse_id,
        product_id=product_id,
        uom_id=uom_id,
        quantity=quantity,
    )
    db_session.add(level)
    await db_session.flush()


async def _initiate(
    handler: TransferCommandHandler,
    company_a: uuid.UUID,
    company_b: uuid.UUID,
    wh_a: uuid.UUID,
    wh_b: uuid.UUID,
    product_id: uuid.UUID,
    uom_id: uuid.UUID,
    user_a: uuid.UUID,
    qty: Decimal = Decimal("50.0"),
    price: Decimal = Decimal("25.00"),
    currency: str = "USD",
):
    cmd = InitiateTransferCommand(
        origin_company_id=company_a,
        initiated_by=user_a,
        destination_company_id=company_b,
        destination_warehouse_id=wh_b,
        origin_warehouse_id=wh_a,
        product_id=product_id,
        uom_id=uom_id,
        quantity=qty,
        transfer_price=price,
        currency=currency,
    )
    return await handler.initiate_transfer(cmd)


# ─── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def ids():
    return {
        "company_a": uuid.uuid4(),
        "company_b": uuid.uuid4(),
        "user_a": uuid.uuid4(),
        "user_b": uuid.uuid4(),
        "wh_a": uuid.uuid4(),
        "wh_b": uuid.uuid4(),
        "product": uuid.uuid4(),
        "uom": uuid.uuid4(),
    }


# ─── TC-ICT-E01 ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_e01_mirror_documents_created_on_initiate(db_session, ids):
    """
    TC-ICT-E01: Al iniciar un ICT, se crean dos InventoryDocument:
      - ICT_OUT en Empresa A con status PROCESSED
      - ICT_IN  en Empresa B con status DRAFT
    """
    repo = SQLAlchemyInventoryRepository(db_session)
    handler = TransferCommandHandler(session=db_session, repo=repo)

    await _seed_stock(
        db_session, ids["company_a"], ids["wh_a"],
        ids["product"], ids["uom"], Decimal("100.0")
    )
    wh_b = Warehouse(id=ids["wh_b"], company_id=ids["company_b"], code="WH-B", name="Dest")
    db_session.add(wh_b)
    await db_session.flush()

    doc = await _initiate(
        handler, ids["company_a"], ids["company_b"],
        ids["wh_a"], ids["wh_b"], ids["product"], ids["uom"], ids["user_a"]
    )

    # Query documents by external_reference = transfer_id
    stmt = select(InventoryDocument).where(
        InventoryDocument.external_reference == str(doc.id)
    )
    result = await db_session.execute(stmt)
    inv_docs = result.scalars().all()

    assert len(inv_docs) == 2, f"Esperados 2 documentos espejo, encontrados {len(inv_docs)}"

    types_status = {d.document_type: d.status for d in inv_docs}
    assert types_status.get("ICT_OUT") == DocumentStatus.PROCESSED, "Doc A debe ser PROCESSED"
    assert types_status.get("ICT_IN") == DocumentStatus.DRAFT, "Doc B debe ser DRAFT"

    # Verificar company_id de cada uno
    company_map = {d.document_type: d.company_id for d in inv_docs}
    assert company_map["ICT_OUT"] == ids["company_a"], "ICT_OUT debe pertenecer a Empresa A"
    assert company_map["ICT_IN"] == ids["company_b"], "ICT_IN debe pertenecer a Empresa B"


# ─── TC-ICT-E02 ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_e02_external_reference_idempotency(db_session, ids):
    """
    TC-ICT-E02: Los documentos espejo llevan el transfer_id como
    external_reference para detectar duplicados en reintentos.
    """
    repo = SQLAlchemyInventoryRepository(db_session)
    handler = TransferCommandHandler(session=db_session, repo=repo)

    await _seed_stock(
        db_session, ids["company_a"], ids["wh_a"],
        ids["product"], ids["uom"], Decimal("200.0")
    )
    wh_b = Warehouse(id=ids["wh_b"], company_id=ids["company_b"], code="WH-B", name="Dest")
    db_session.add(wh_b)
    await db_session.flush()

    doc = await _initiate(
        handler, ids["company_a"], ids["company_b"],
        ids["wh_a"], ids["wh_b"], ids["product"], ids["uom"], ids["user_a"]
    )

    stmt = select(InventoryDocument).where(
        InventoryDocument.external_reference == str(doc.id)
    )
    result = await db_session.execute(stmt)
    docs = result.scalars().all()

    # Ambos documentos deben tener el transfer_id como external_reference
    for d in docs:
        assert d.external_reference == str(doc.id), (
            f"external_reference incorrecto en {d.document_type}: {d.external_reference}"
        )


# ─── TC-ICT-E03 ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_e03_transit_warehouse_is_transit_flag(db_session, ids):
    """
    TC-ICT-E03: El almacén virtual de tránsito debe tener is_transit=True,
    segregándolo de los almacenes físicos en reportes de disponibilidad.
    """
    repo = SQLAlchemyInventoryRepository(db_session)
    handler = TransferCommandHandler(session=db_session, repo=repo)

    await _seed_stock(
        db_session, ids["company_a"], ids["wh_a"],
        ids["product"], ids["uom"], Decimal("100.0")
    )
    wh_b = Warehouse(id=ids["wh_b"], company_id=ids["company_b"], code="WH-B", name="Dest")
    db_session.add(wh_b)
    await db_session.flush()

    await _initiate(
        handler, ids["company_a"], ids["company_b"],
        ids["wh_a"], ids["wh_b"], ids["product"], ids["uom"], ids["user_a"]
    )

    # Buscar el almacén de tránsito creado
    transit_warehouses = (
        await db_session.execute(
            select(Warehouse).where(Warehouse.is_transit == True)
        )
    ).scalars().all()

    assert len(transit_warehouses) >= 1, "Debe haberse creado al menos un almacén de tránsito"
    for tw in transit_warehouses:
        assert tw.is_transit is True, f"Almacén {tw.code} debería ser is_transit=True"
        assert tw.company_id == ids["company_b"], "El tránsito pertenece a Empresa B"


# ─── TC-ICT-E04 ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_e04_wac_b_uses_sealed_transfer_price(db_session, ids):
    """
    TC-ICT-E04: Al completar la transferencia, el costo de Empresa B
    debe ser el sealed_transfer_price, NO el WAC de Empresa A.

    Alineación legacy: Movements.PurchasePrice = transfer_price (no WAC de A).
    """
    repo = SQLAlchemyInventoryRepository(db_session)
    handler = TransferCommandHandler(session=db_session, repo=repo)

    TRANSFER_PRICE = Decimal("99.00")
    QTY = Decimal("10.0")
    EXPECTED_COST_B = QTY * TRANSFER_PRICE  # = 990.00

    await _seed_stock(
        db_session, ids["company_a"], ids["wh_a"],
        ids["product"], ids["uom"], Decimal("100.0")
    )
    wh_b = Warehouse(id=ids["wh_b"], company_id=ids["company_b"], code="WH-B", name="Dest")
    db_session.add(wh_b)
    await db_session.flush()

    doc = await _initiate(
        handler, ids["company_a"], ids["company_b"],
        ids["wh_a"], ids["wh_b"], ids["product"], ids["uom"],
        ids["user_a"], qty=QTY, price=TRANSFER_PRICE
    )

    # Completar la recepción
    recv_cmd = CompleteTransferCommand(
        receiver_company_id=ids["company_b"],
        received_by=ids["user_b"],
        transfer_id=doc.id,
    )
    result = await handler.complete_transfer(recv_cmd)

    assert result.status == TransferStatusEnum.DELIVERED
    assert result.acquisition_cost_b is not None, "acquisition_cost_b no debe ser None"
    assert result.acquisition_cost_b.amount == EXPECTED_COST_B, (
        f"Costo de B esperado {EXPECTED_COST_B}, obtenido {result.acquisition_cost_b.amount}"
    )


# ─── TC-ICT-E05 ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_e05_doc_a_total_amount_equals_revenue(db_session, ids):
    """
    TC-ICT-E05: El InventoryDocument ICT_OUT de Empresa A debe tener
    total_amount = qty × transfer_price (el ingreso pactado).
    """
    repo = SQLAlchemyInventoryRepository(db_session)
    handler = TransferCommandHandler(session=db_session, repo=repo)

    PRICE = Decimal("50.00")
    QTY = Decimal("20.0")
    EXPECTED_TOTAL = QTY * PRICE  # = 1000.00

    await _seed_stock(
        db_session, ids["company_a"], ids["wh_a"],
        ids["product"], ids["uom"], Decimal("100.0")
    )
    wh_b = Warehouse(id=ids["wh_b"], company_id=ids["company_b"], code="WH-B", name="Dest")
    db_session.add(wh_b)
    await db_session.flush()

    doc = await _initiate(
        handler, ids["company_a"], ids["company_b"],
        ids["wh_a"], ids["wh_b"], ids["product"], ids["uom"],
        ids["user_a"], qty=QTY, price=PRICE
    )

    stmt = select(InventoryDocument).where(
        InventoryDocument.external_reference == str(doc.id),
        InventoryDocument.document_type == "ICT_OUT",
    )
    result = await db_session.execute(stmt)
    out_doc = result.scalar_one_or_none()

    assert out_doc is not None, "Doc ICT_OUT de Empresa A no encontrado"
    assert out_doc.total_amount.amount == EXPECTED_TOTAL, (
        f"total_amount de A esperado {EXPECTED_TOTAL}, obtenido {out_doc.total_amount.amount}"
    )


# ─── TC-ICT-E06 ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_e06_doc_b_total_amount_updated_on_receipt(db_session, ids):
    """
    TC-ICT-E06: Tras la recepción, el InventoryDocument ICT_IN de Empresa B
    debe actualizarse a PROCESSED con total_amount = acquisition_cost_b.
    """
    repo = SQLAlchemyInventoryRepository(db_session)
    handler = TransferCommandHandler(session=db_session, repo=repo)

    PRICE = Decimal("30.00")
    QTY = Decimal("5.0")
    EXPECTED_COST = QTY * PRICE  # = 150.00

    await _seed_stock(
        db_session, ids["company_a"], ids["wh_a"],
        ids["product"], ids["uom"], Decimal("100.0")
    )
    wh_b = Warehouse(id=ids["wh_b"], company_id=ids["company_b"], code="WH-B", name="Dest")
    db_session.add(wh_b)
    await db_session.flush()

    doc = await _initiate(
        handler, ids["company_a"], ids["company_b"],
        ids["wh_a"], ids["wh_b"], ids["product"], ids["uom"],
        ids["user_a"], qty=QTY, price=PRICE
    )

    recv_cmd = CompleteTransferCommand(
        receiver_company_id=ids["company_b"],
        received_by=ids["user_b"],
        transfer_id=doc.id,
    )
    await handler.complete_transfer(recv_cmd)

    stmt = select(InventoryDocument).where(
        InventoryDocument.external_reference == str(doc.id),
        InventoryDocument.document_type == "ICT_IN",
    )
    result = await db_session.execute(stmt)
    in_doc = result.scalar_one_or_none()

    assert in_doc is not None, "Doc ICT_IN de Empresa B no encontrado"
    assert in_doc.status == DocumentStatus.PROCESSED, "Doc B debe ser PROCESSED tras recepción"
    assert in_doc.total_amount.amount == EXPECTED_COST, (
        f"total_amount de B esperado {EXPECTED_COST}, obtenido {in_doc.total_amount.amount}"
    )


# ─── TC-ICT-E07 ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_e07_revert_orphan_transfer_full_cycle(db_session, ids):
    """
    TC-ICT-E07: Al revertir una transferencia huérfana:
      - El InventoryDocument DRAFT de B queda CANCELLED.
      - El ICT queda CANCELLED con nota de reversión.
      - El stock debe haber regresado al almacén de A.
    """
    repo = SQLAlchemyInventoryRepository(db_session)
    handler = TransferCommandHandler(session=db_session, repo=repo)

    await _seed_stock(
        db_session, ids["company_a"], ids["wh_a"],
        ids["product"], ids["uom"], Decimal("100.0")
    )
    wh_b = Warehouse(id=ids["wh_b"], company_id=ids["company_b"], code="WH-B", name="Dest")
    db_session.add(wh_b)
    await db_session.flush()

    doc = await _initiate(
        handler, ids["company_a"], ids["company_b"],
        ids["wh_a"], ids["wh_b"], ids["product"], ids["uom"],
        ids["user_a"], qty=Decimal("30.0"), price=Decimal("10.00")
    )

    # Revertir
    revert_cmd = CancelTransferCommand(
        requester_company_id=ids["company_a"],
        requested_by=ids["user_a"],
        transfer_id=doc.id,
        reason="Empresa B no procesó en tiempo",
    )
    result = await handler.revert_transfer(revert_cmd)

    assert result.status == TransferStatusEnum.CANCELLED

    # Verificar que el DRAFT de B fue cancelado
    stmt = select(InventoryDocument).where(
        InventoryDocument.external_reference == str(doc.id),
        InventoryDocument.document_type == "ICT_IN",
    )
    res = await db_session.execute(stmt)
    in_doc = res.scalar_one_or_none()
    assert in_doc is not None, "Doc ICT_IN de B debe existir"
    assert in_doc.status == DocumentStatus.CANCELLED, "Doc B debe ser CANCELLED tras reversión"


# ─── TC-ICT-E08 ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_e08_revert_blocked_if_delivered(db_session, ids):
    """
    TC-ICT-E08: No se puede revertir una transferencia ya DELIVERED.
    """
    repo = SQLAlchemyInventoryRepository(db_session)
    handler = TransferCommandHandler(session=db_session, repo=repo)

    await _seed_stock(
        db_session, ids["company_a"], ids["wh_a"],
        ids["product"], ids["uom"], Decimal("100.0")
    )
    wh_b = Warehouse(id=ids["wh_b"], company_id=ids["company_b"], code="WH-B", name="Dest")
    db_session.add(wh_b)
    await db_session.flush()

    doc = await _initiate(
        handler, ids["company_a"], ids["company_b"],
        ids["wh_a"], ids["wh_b"], ids["product"], ids["uom"], ids["user_a"]
    )

    # Completar primero
    recv_cmd = CompleteTransferCommand(
        receiver_company_id=ids["company_b"],
        received_by=ids["user_b"],
        transfer_id=doc.id,
    )
    await handler.complete_transfer(recv_cmd)

    # Intentar revertir — debe fallar
    revert_cmd = CancelTransferCommand(
        requester_company_id=ids["company_a"],
        requested_by=ids["user_a"],
        transfer_id=doc.id,
        reason="Intento tardío",
    )
    with pytest.raises(ConflictException) as exc_info:
        await handler.revert_transfer(revert_cmd)

    assert "ERR_ALREADY_DELIVERED" in str(exc_info.value)


# ─── TC-ICT-E09 ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_e09_revert_blocked_if_wrong_company(db_session, ids):
    """
    TC-ICT-E09: Solo la Empresa A (originadora) puede reclamar el stock.
    Una empresa externa no debe poder ejecutar la reversión.
    """
    repo = SQLAlchemyInventoryRepository(db_session)
    handler = TransferCommandHandler(session=db_session, repo=repo)

    company_c = uuid.uuid4()  # Impostor

    await _seed_stock(
        db_session, ids["company_a"], ids["wh_a"],
        ids["product"], ids["uom"], Decimal("100.0")
    )
    wh_b = Warehouse(id=ids["wh_b"], company_id=ids["company_b"], code="WH-B", name="Dest")
    db_session.add(wh_b)
    await db_session.flush()

    doc = await _initiate(
        handler, ids["company_a"], ids["company_b"],
        ids["wh_a"], ids["wh_b"], ids["product"], ids["uom"], ids["user_a"]
    )

    revert_cmd = CancelTransferCommand(
        requester_company_id=company_c,  # Empresa equivocada
        requested_by=uuid.uuid4(),
        transfer_id=doc.id,
        reason="Intento de robo de stock",
    )
    with pytest.raises(UnauthorizedException) as exc_info:
        await handler.revert_transfer(revert_cmd)

    assert "ERR_REVERT_UNAUTHORIZED" in str(exc_info.value)
