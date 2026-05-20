"""
Collaborator Login Command
==========================
Orchestrates the physical identity authentication flow:
  1. Receives raw RFID or PIN from the Kiosk frontend.
  2. Calls the hr_service internal /verify endpoint via HTTP.
  3. On success, mints a JWT with role=collaborator, wid, cid, is_supervisor.
"""
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from auth_app.core.config import settings
from auth_app.core.security import _encode
from auth_app.models.company import Company

logger = logging.getLogger(__name__)

from common.models import SecurityAuditLog

# JWT lifetime for collaborator sessions: 8 hours (a full shift)
COLLABORATOR_TOKEN_EXPIRE_HOURS = 8

_COLLABORATOR_SLUG_FALLBACK = [
    "inventory.stock.read", "inventory.document.create",
    "master_data.product.read", "master_data.price.read", "pos.checkout",
]


async def _load_collaborator_slugs(db: AsyncSession) -> list:
    """Returns Permission slugs for the system 'collaborator' role from DB."""
    from sqlalchemy import text
    result = await db.execute(text("""
        SELECT p.slug FROM permissions p
        JOIN role_permissions rp ON rp.permission_id = p.id
        JOIN roles r ON r.id = rp.role_id
        WHERE r.name = 'collaborator' AND r.company_id IS NULL AND r.is_active = true
        ORDER BY p.slug
    """))
    rows = [row[0] for row in result.fetchall()]
    return rows if rows else _COLLABORATOR_SLUG_FALLBACK


from auth_app.core import security


async def collaborator_login(
    db: AsyncSession,
    rfid_tag: Optional[str] = None,
    internal_id: Optional[str] = None,
    pin_code: Optional[str] = None,
    company_id: Optional[uuid.UUID] = None,
    ip_address: Optional[str] = None,
    transaction_id: Optional[uuid.UUID] = None
) -> dict:
    """
    Proxy login for floor collaborators.
    Returns:
       - {"access_token": "..."} if 1 match
       - {"selection_token": "...", "companies": [...]} if >1 matches
    """
    if not rfid_tag and not pin_code and not internal_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Se requiere rfid_tag, internal_id o pin_code para identificar al colaborador.",
        )

    # Limpiar entradas de posibles caracteres invisibles del escáner (\n, \r, espacios)
    if rfid_tag:
        rfid_tag = rfid_tag.strip()
    if internal_id:
        internal_id = internal_id.strip()
    if pin_code:
        pin_code = pin_code.strip()

    # ── Step 1: Call hr_service internal verification ──────────────────────────
    payload = {
        "company_id": str(company_id) if company_id else None,
        "rfid_tag": rfid_tag,
        "internal_id": internal_id,
        "pin_code": pin_code,
    }

    logger.debug(f"[COLLAB-AUTH] Forwarding credentials to HR Service: method={'RFID' if rfid_tag else 'PIN'}, identifier={internal_id or rfid_tag}")
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{settings.HCM_SERVICE_URL}/api/v1/internal/collaborators/verify",
                json=payload,
                headers={"X-Internal-Api-Key": settings.INTERNAL_API_KEY},
            )
            logger.debug(f"[COLLAB-AUTH] HR Service Response: {response.status_code} - {response.text}")
    except Exception as exc:
        logger.error(f"hr_service connection error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="HR Service no disponible para verificación física.",
        )

    if response.status_code == 401:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credencial no reconocida. Verifique su RFID o PIN.",
        )

    if response.status_code != 200:
        logger.warning(f"hr_service returned unexpected status: {response.status_code}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error al verificar identidad física.",
        )

    # ── Step 2: Handle Multi-Match Discovery ───────────────────────────────────
    hr_response = response.json()
    hr_data = hr_response.get("data", {})
    matches = hr_data.get("matches", [])
    
    if not matches:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se encontraron colaboradores para esa credencial.",
        )

    # Case A: Multiple Companies Found -> Selection Handshake (T1)
    if len(matches) > 1:
        # Usamos el primer ID de colaborador como sujeto del selection_token
        selection_token = security.create_selection_token(matches[0]["collaborator_id"])
        
        # Resolve company names from Auth DB
        match_cids = [uuid.UUID(m["company_id"]) if isinstance(m["company_id"], str) else m["company_id"] for m in matches]
        q = await db.execute(select(Company).where(Company.id.in_(match_cids)))
        names_map = {c.id: c.name for c in q.scalars().all()}
        
        companies_list = []
        for m in matches:
            cid = uuid.UUID(m["company_id"]) if isinstance(m["company_id"], str) else m["company_id"]
            companies_list.append({
                "company_id": str(cid),
                "company_name": names_map.get(cid, f"Interno - {str(cid)[:8]}"),
                "role_names": ["collaborator"],
                "is_new": False
            })
            
        return {
            "selection_token": selection_token,
            "companies": companies_list
        }

    # Case B: Exactly 1 Company Found -> Direct Access (T2 Bypass)
    identity = matches[0]
    dept = identity.get("department")
    is_supervisor = identity.get("is_supervisor", False)

    expire = datetime.now(timezone.utc) + timedelta(hours=COLLABORATOR_TOKEN_EXPIRE_HOURS)

    # Permission logic
    has_inventory_access = (dept == "Warehouse" or is_supervisor)

    # Scopes from DB (Permission slugs for system 'collaborator' role)
    scopes = await _load_collaborator_slugs(db)

    # Granular action codes for kiosk UI (separate from DB slugs)
    permissions = ["PHYSICAL_SCAN", "INVENTORY_READ"]
    if has_inventory_access:
        permissions.append("INVENTORY_WRITE")

    token = security.create_final_access_token(
        subject=uuid.UUID(str(identity["collaborator_id"])),
        company_id=uuid.UUID(str(identity["company_id"])),
        roles=["collaborator"],
        scopes=scopes,
        modules=["auth_core", "inventory_core"],
        extra_data={
            "wid": str(identity.get("home_warehouse_id")) if identity.get("home_warehouse_id") else None,
            "is_supervisor": is_supervisor, 
            "internal_id": identity.get("internal_id"),
            "full_name": identity.get("full_name"),
            "department": dept,
            "warehouse_permission": has_inventory_access,
            "permissions": permissions
        }
    )
    
    # Resolve company name for the header
    company_obj = await db.get(Company, identity["company_id"])
    company_name = company_obj.name if company_obj else "Interno Core"


    # ── Step 3: Forensic Audit Logging ────────────────────────────────────────
    try:
        audit_entry = SecurityAuditLog(
            id=uuid.uuid4(),
            company_id=uuid.UUID(str(identity["company_id"])),
            collaborator_id=uuid.UUID(str(identity["collaborator_id"])),
            access_method="RFID_SCAN" if rfid_tag else ("PIN_PAD" if pin_code else "WEB_FORM"),
            identity_identifier=rfid_tag if rfid_tag else (internal_id if internal_id else "UNKNOWN"),
            roles_snapshot=["collaborator"],
            scopes_snapshot=scopes,
            status="SUCCESS",
            ip_address=ip_address,
            transaction_id=transaction_id,
            is_active=True
        )
        db.add(audit_entry)
        # We don't commit here, the endpoint handler (collaborator_auth.py) should commit or 
        # it might be handled by middleware if using a certain pattern.
        # But looking at auth.py, they do await db.commit().
        # However, collaborator_auth.py doesn't have db.commit() yet.
        # I'll add a comment or better, I'll add the commit to the endpoint.
    except Exception as e:
        logger.error(f"Failed to log security audit: {e}")

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": str(identity["collaborator_id"]),
        "company_id": str(identity["company_id"]),
        "company_name": company_name,
        "scopes": scopes,
        "permissions": permissions,
        "user_full_name": identity.get("full_name"),
        "role": "collaborator"
    }
