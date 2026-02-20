"""create_billing_initial_tables

Revision ID: b001_billing_init
Revises:
Create Date: 2026-02-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'b001_billing_init'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enum Types
    invoice_status = postgresql.ENUM(
        'DRAFT', 'ISSUED', 'SENT', 'PAID', 'PARTIALLY_PAID', 'OVERDUE', 'CANCELLED', 'VOIDED',
        name='invoicestatus'
    )
    invoice_status.create(op.get_bind(), checkfirst=True)

    credit_note_type = postgresql.ENUM(
        'RETURN', 'DISCOUNT', 'ERROR_CORRECTION',
        name='creditnotetype'
    )
    credit_note_type.create(op.get_bind(), checkfirst=True)

    payment_method = postgresql.ENUM(
        'CASH', 'BANK_TRANSFER', 'CHECK', 'CREDIT_CARD', 'OTHER',
        name='paymentmethod'
    )
    payment_method.create(op.get_bind(), checkfirst=True)

    # payment_terms
    op.create_table(
        'payment_terms',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(150), nullable=False),
        sa.Column('translation_key', sa.String(100), nullable=True),
        sa.Column('days_due', sa.Integer, nullable=False, default=30),
        sa.Column('discount_days', sa.Integer, nullable=True),
        sa.Column('discount_percent', sa.Numeric(5, 2), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # invoices
    op.create_table(
        'invoices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('folio', sa.String(50), nullable=False),
        sa.Column('series', sa.String(20), nullable=True),
        sa.Column('sequence_number', sa.Integer, nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_name', sa.String(255), nullable=False),
        sa.Column('customer_tax_id', sa.String(50), nullable=True),
        sa.Column('status', sa.Enum('DRAFT', 'ISSUED', 'SENT', 'PAID', 'PARTIALLY_PAID',
                                     'OVERDUE', 'CANCELLED', 'VOIDED', name='invoicestatus'),
                  nullable=False, server_default='DRAFT'),
        sa.Column('payment_term_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('payment_terms.id'), nullable=True),
        sa.Column('issue_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('subtotal', sa.Numeric(18, 4), nullable=False, default=0),
        sa.Column('tax_amount', sa.Numeric(18, 4), nullable=False, default=0),
        sa.Column('discount_amount', sa.Numeric(18, 4), nullable=False, default=0),
        sa.Column('total', sa.Numeric(18, 4), nullable=False, default=0),
        sa.Column('currency', sa.String(3), nullable=False, server_default='MXN'),
        sa.Column('exchange_rate', sa.Numeric(10, 6), nullable=False, default=1),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('wms_document_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('folio', 'company_id', name='_company_folio_uc'),
        sa.UniqueConstraint('series', 'sequence_number', 'company_id', name='_company_series_seq_uc'),
    )

    # invoice_items
    op.create_table(
        'invoice_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('sku', sa.String(100), nullable=False),
        sa.Column('description', sa.String(500), nullable=False),
        sa.Column('quantity', sa.Numeric(14, 4), nullable=False),
        sa.Column('unit_price', sa.Numeric(18, 4), nullable=False),
        sa.Column('discount_percent', sa.Numeric(5, 2), nullable=False, default=0),
        sa.Column('tax_rate', sa.Numeric(5, 2), nullable=False, default=16),
        sa.Column('subtotal', sa.Numeric(18, 4), nullable=False),
        sa.Column('tax_amount', sa.Numeric(18, 4), nullable=False),
        sa.Column('total', sa.Numeric(18, 4), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # credit_notes
    op.create_table(
        'credit_notes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('folio', sa.String(50), nullable=False),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('invoices.id'), nullable=False),
        sa.Column('note_type', sa.Enum('RETURN', 'DISCOUNT', 'ERROR_CORRECTION',
                                        name='creditnotetype'), nullable=False),
        sa.Column('amount', sa.Numeric(18, 4), nullable=False),
        sa.Column('reason', sa.Text, nullable=True),
        sa.Column('issue_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('folio', 'company_id', name='_cn_company_folio_uc'),
    )

    # payments
    op.create_table(
        'payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('invoices.id'), nullable=False),
        sa.Column('amount', sa.Numeric(18, 4), nullable=False),
        sa.Column('payment_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('method', sa.Enum('CASH', 'BANK_TRANSFER', 'CHECK', 'CREDIT_CARD', 'OTHER',
                                     name='paymentmethod'), nullable=False),
        sa.Column('reference', sa.String(255), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('payments')
    op.drop_table('credit_notes')
    op.drop_table('invoice_items')
    op.drop_table('invoices')
    op.drop_table('payment_terms')
