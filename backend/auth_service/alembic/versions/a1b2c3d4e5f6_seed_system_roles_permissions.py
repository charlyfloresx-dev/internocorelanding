"""Seed system roles and permissions (RBAC bootstrap)

Revision ID: a1b2c3d4e5f6
Revises: 90a121e69a2e
Create Date: 2026-05-18

Seeds the four system roles (admin, manager, warehouse_operator, collaborator)
and their 23 Permission slugs into the auth DB.

Admin role intentionally has NO role_permissions rows — the wildcard ["*"]
is detected by select_company_command._build_scopes() from ucr.scopes or role name.
"""
from alembic import op
import sqlalchemy as sa
import uuid

revision = 'a1b2c3d4e5f6'
down_revision = '90a121e69a2e'
branch_labels = None
depends_on = None

# Sentinel for NOT-NULL system-level records (no real tenant or company)
SENTINEL = '00000000-0000-0000-0000-000000000001'

# Stable, deterministic UUIDs for the 4 system roles
ROLE_IDS = {
    'admin':              '10000000-0000-0000-0000-000000000001',
    'manager':            '10000000-0000-0000-0000-000000000002',
    'warehouse_operator': '10000000-0000-0000-0000-000000000003',
    'collaborator':       '10000000-0000-0000-0000-000000000004',
}

# Stable UUIDs for the 23 system permissions
PERM_IDS = {
    'inventory.stock.read':           '20000000-0000-0000-0000-000000000001',
    'inventory.document.create':      '20000000-0000-0000-0000-000000000002',
    'inventory.document.approve':     '20000000-0000-0000-0000-000000000003',
    'inventory.document.cancel':      '20000000-0000-0000-0000-000000000004',
    'inventory.transfer.inter_co':    '20000000-0000-0000-0000-000000000005',
    'inventory.audit.view':           '20000000-0000-0000-0000-000000000006',
    'inventory.bulk_load':            '20000000-0000-0000-0000-000000000007',
    'inventory.location.manage':      '20000000-0000-0000-0000-000000000008',
    'inventory.cycle_count':          '20000000-0000-0000-0000-000000000009',
    'inventory.put_away':             '20000000-0000-0000-0000-000000000010',
    'master_data.product.read':       '20000000-0000-0000-0000-000000000011',
    'master_data.product.write':      '20000000-0000-0000-0000-000000000012',
    'master_data.price.read':         '20000000-0000-0000-0000-000000000013',
    'master_data.price.write':        '20000000-0000-0000-0000-000000000014',
    'master_data.partner.manage':     '20000000-0000-0000-0000-000000000015',
    'master_data.warehouse.manage':   '20000000-0000-0000-0000-000000000016',
    'hcm.collaborator.read':          '20000000-0000-0000-0000-000000000017',
    'hcm.collaborator.write':         '20000000-0000-0000-0000-000000000018',
    'hcm.collaborator.rfid_assign':   '20000000-0000-0000-0000-000000000019',
    'admin.user.manage':              '20000000-0000-0000-0000-000000000020',
    'admin.role.view':                '20000000-0000-0000-0000-000000000021',
    'pos.checkout':                   '20000000-0000-0000-0000-000000000022',
    'pos.price_override':             '20000000-0000-0000-0000-000000000023',
}

PERMISSIONS = [
    {'slug': 'inventory.stock.read',          'module_name': 'inventory_core',   'name': 'Ver saldos de stock'},
    {'slug': 'inventory.document.create',     'module_name': 'inventory_core',   'name': 'Crear documento de inventario'},
    {'slug': 'inventory.document.approve',    'module_name': 'inventory_core',   'name': 'Aprobar/procesar documento'},
    {'slug': 'inventory.document.cancel',     'module_name': 'inventory_core',   'name': 'Cancelar documento'},
    {'slug': 'inventory.transfer.inter_co',   'module_name': 'inventory_core',   'name': 'Transferencia inter-empresa'},
    {'slug': 'inventory.audit.view',          'module_name': 'inventory_core',   'name': 'Auditoría forense Kardex'},
    {'slug': 'inventory.bulk_load',           'module_name': 'inventory_core',   'name': 'Carga masiva'},
    {'slug': 'inventory.location.manage',     'module_name': 'inventory_core',   'name': 'Gestionar ubicaciones WMS'},
    {'slug': 'inventory.cycle_count',         'module_name': 'inventory_core',   'name': 'Conteo cíclico'},
    {'slug': 'inventory.put_away',            'module_name': 'inventory_core',   'name': 'Put-Away handheld'},
    {'slug': 'master_data.product.read',      'module_name': 'master_data_core', 'name': 'Ver productos'},
    {'slug': 'master_data.product.write',     'module_name': 'master_data_core', 'name': 'Crear/editar productos'},
    {'slug': 'master_data.price.read',        'module_name': 'master_data_core', 'name': 'Ver precios'},
    {'slug': 'master_data.price.write',       'module_name': 'master_data_core', 'name': 'Gestionar listas de precios'},
    {'slug': 'master_data.partner.manage',    'module_name': 'master_data_core', 'name': 'Gestionar socios de negocio'},
    {'slug': 'master_data.warehouse.manage',  'module_name': 'master_data_core', 'name': 'Gestionar almacenes'},
    {'slug': 'hcm.collaborator.read',         'module_name': 'hcm_core',         'name': 'Ver colaboradores'},
    {'slug': 'hcm.collaborator.write',        'module_name': 'hcm_core',         'name': 'Crear/editar colaboradores'},
    {'slug': 'hcm.collaborator.rfid_assign',  'module_name': 'hcm_core',         'name': 'Asignar tarjeta RFID'},
    {'slug': 'admin.user.manage',             'module_name': 'auth_core',        'name': 'Gestionar usuarios de empresa'},
    {'slug': 'admin.role.view',               'module_name': 'auth_core',        'name': 'Ver roles y permisos'},
    {'slug': 'pos.checkout',                  'module_name': 'inventory_core',   'name': 'Procesar venta POS'},
    {'slug': 'pos.price_override',            'module_name': 'inventory_core',   'name': 'Sobreescribir precio en POS'},
]

# admin: no rows (wildcard handled by _build_scopes detecting the admin role name)
# manager: all except inventory.put_away and pos.price_override
_MANAGER_SLUGS = [
    'inventory.stock.read', 'inventory.document.create', 'inventory.document.approve',
    'inventory.document.cancel', 'inventory.transfer.inter_co', 'inventory.audit.view',
    'inventory.bulk_load', 'inventory.location.manage', 'inventory.cycle_count',
    'master_data.product.read', 'master_data.product.write', 'master_data.price.read',
    'master_data.price.write', 'master_data.partner.manage', 'master_data.warehouse.manage',
    'hcm.collaborator.read', 'hcm.collaborator.write', 'hcm.collaborator.rfid_assign',
    'admin.user.manage', 'admin.role.view', 'pos.checkout',
]

ROLE_PERMISSION_ASSIGNMENTS = {
    'manager': _MANAGER_SLUGS,
    'warehouse_operator': [
        'inventory.stock.read', 'inventory.document.create', 'inventory.put_away',
        'inventory.cycle_count', 'master_data.product.read', 'master_data.price.read',
        'pos.checkout',
    ],
    'collaborator': [
        'inventory.stock.read', 'inventory.document.create',
        'master_data.product.read', 'master_data.price.read', 'pos.checkout',
    ],
}


def upgrade():
    conn = op.get_bind()

    # Idempotency guard — skip entirely if admin role already exists
    row = conn.execute(
        sa.text("SELECT 1 FROM roles WHERE id = :id"),
        {'id': ROLE_IDS['admin']}
    ).first()
    if row:
        return

    # 1. Permissions — ON CONFLICT on unique slug covers re-runs after partial failure
    for perm in PERMISSIONS:
        conn.execute(sa.text("""
            INSERT INTO permissions
                (id, name, slug, module_name, company_id, tenant_id, is_active, version_id, created_at)
            VALUES
                (:id, :name, :slug, :module_name, NULL, :tenant_id, true, 1, NOW())
            ON CONFLICT (slug) DO NOTHING
        """), {
            'id': PERM_IDS[perm['slug']],
            'name': perm['name'],
            'slug': perm['slug'],
            'module_name': perm['module_name'],
            'tenant_id': SENTINEL,
        })

    # 2. Roles — explicit existence check because PostgreSQL treats NULL≠NULL in
    # unique constraints, so ON CONFLICT (name, company_id) won't fire for two
    # system roles that both have company_id = NULL.
    system_roles = [
        ('admin',              True),
        ('manager',            True),
        ('warehouse_operator', True),
        ('collaborator',       True),
    ]
    for role_name, is_system in system_roles:
        exists = conn.execute(
            sa.text("SELECT 1 FROM roles WHERE id = :id"),
            {'id': ROLE_IDS[role_name]}
        ).first()
        if exists:
            continue
        conn.execute(sa.text("""
            INSERT INTO roles
                (id, name, is_system_role, company_id, tenant_id, is_active, version_id, created_at)
            VALUES
                (:id, :name, :is_system, NULL, :tenant_id, true, 1, NOW())
        """), {
            'id': ROLE_IDS[role_name],
            'name': role_name,
            'is_system': is_system,
            'tenant_id': SENTINEL,
        })

    # 3. role_permissions — deterministic id via uuid5 so ON CONFLICT on PK works
    # role_permissions.company_id is NOT NULL (schema constraint); sentinel used for system records.
    for role_name, slugs in ROLE_PERMISSION_ASSIGNMENTS.items():
        role_id = ROLE_IDS[role_name]
        for slug in slugs:
            perm_id = PERM_IDS[slug]
            rp_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{role_name}:{slug}"))
            conn.execute(sa.text("""
                INSERT INTO role_permissions
                    (id, role_id, permission_id, company_id, tenant_id, is_active, version_id, created_at)
                VALUES
                    (:id, :role_id, :perm_id, :company_id, :tenant_id, true, 1, NOW())
                ON CONFLICT (role_id, permission_id, id) DO NOTHING
            """), {
                'id': rp_id,
                'role_id': role_id,
                'perm_id': perm_id,
                'company_id': SENTINEL,
                'tenant_id': SENTINEL,
            })


def downgrade():
    conn = op.get_bind()

    all_role_ids = list(ROLE_IDS.values())
    all_perm_ids = list(PERM_IDS.values())

    # Remove system role_permissions first (FK child)
    conn.execute(sa.text(
        "DELETE FROM role_permissions WHERE role_id = ANY(:ids)"
    ), {'ids': all_role_ids})

    # Remove system roles
    conn.execute(sa.text(
        "DELETE FROM roles WHERE id = ANY(:ids)"
    ), {'ids': all_role_ids})

    # Remove system permissions
    conn.execute(sa.text(
        "DELETE FROM permissions WHERE id = ANY(:ids)"
    ), {'ids': all_perm_ids})
