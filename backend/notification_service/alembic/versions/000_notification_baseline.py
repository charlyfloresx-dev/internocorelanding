"""notification_baseline

Revision ID: 000_notification_baseline
Revises: None
Create Date: 2026-05-16 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '000_notification_baseline'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=True),
        sa.Column('group_id', sa.UUID(), nullable=True),
        sa.Column('type', sa.String(length=50), nullable=True),
        sa.Column('category', sa.Enum('INFO', 'INVENTORY', 'COMPLIANCE', 'SYSTEM', 'SECURITY', name='notificationcategory'), nullable=True),
        sa.Column('event_id', sa.UUID(), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('priority', sa.Enum('CRITICAL', 'HIGH', 'MEDIUM', 'LOW', name='notificationpriority'), nullable=True),
        sa.Column('channel', sa.Enum('IN_APP', 'EMAIL', 'PUSH', 'WEBHOOK', 'WHATSAPP', name='notificationchannel'), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'SENT', 'FAILED', 'DELIVERED', name='notificationstatus'), nullable=True),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', sa.String(length=100), nullable=True),
        sa.Column('version_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_company_id'), 'notifications', ['company_id'], unique=False)
    op.create_index(op.f('ix_notifications_event_id'), 'notifications', ['event_id'], unique=False)
    op.create_index(op.f('ix_notifications_type'), 'notifications', ['type'], unique=False)

    # 2. Notification Recipients
    op.create_table(
        'notification_recipients',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=True),
        sa.Column('notification_id', sa.UUID(), nullable=True),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('is_read', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['notification_id'], ['notifications.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_recipients_notification_id'), 'notification_recipients', ['notification_id'], unique=False)
    op.create_index(op.f('ix_notification_recipients_user_id'), 'notification_recipients', ['user_id'], unique=False)

    # 3. WhatsApp Mappings
    op.create_table(
        'whatsapp_group_mappings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('group_name', sa.String(length=100), nullable=False),
        sa.Column('whatsapp_group_id', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=200), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_whatsapp_group_mappings_company_id'), 'whatsapp_group_mappings', ['company_id'], unique=False)
    op.create_index(op.f('ix_whatsapp_group_mappings_group_name'), 'whatsapp_group_mappings', ['group_name'], unique=False)

    # 4. Company Configs
    op.create_table(
        'company_notification_configs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('provider', sa.String(length=50), server_default='twilio', nullable=False),
        sa.Column('account_sid', sa.String(length=255), nullable=False),
        sa.Column('auth_token', sa.String(length=255), nullable=False),
        sa.Column('sender_number', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=200), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 5. User Preferences
    op.create_table(
        'user_notification_preferences',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=True),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('receive_in_app', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('receive_email', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('receive_push', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('webhook_url', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_notification_preferences_user_id'), 'user_notification_preferences', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('user_notification_preferences')
    op.drop_table('company_notification_configs')
    op.drop_table('whatsapp_group_mappings')
    op.drop_table('notification_recipients')
    op.drop_table('notifications')
    # Types
    op.execute('DROP TYPE notificationcategory')
    op.execute('DROP TYPE notificationpriority')
    op.execute('DROP TYPE notificationchannel')
    op.execute('DROP TYPE notificationstatus')
