import pytest
import uuid
from auth_app.models import User, Company, Role, UserCompanyRole
from auth_app.core.security import hash_password

@pytest.mark.asyncio
async def test_charly_limited_scopes_in_demo_plant(db):
    """
    Simula el escenario del seed V4:
    Charly tiene acceso a 'Nueva Planta Demo' pero SIN scopes/permisos adicionales.
    """
    # 1. Crear Entidades (Simulando Seed)
    charly_id = uuid.UUID("69aa5ddc-bbaa-46e6-a7f0-aeb4b92b6d38")
    demo_company_id = uuid.UUID("203e03c9-5d65-43ff-9e83-864ef605426c")
    
    # Intentamos buscar si ya existen para evitar duplicados en la sesi\u00f3n
    from sqlalchemy import select
    res = await db.execute(select(User).where(User.id == charly_id))
    charly = res.scalar_one_or_none()
    if not charly:
        charly = User(
            id=charly_id,
            email="charly@internocorp.com",
            hashed_password=hash_password("password123"),
            is_active=True
        )
        db.add(charly)
        
    res = await db.execute(select(Company).where(Company.id == demo_company_id))
    demo_company = res.scalar_one_or_none()
    if not demo_company:
        demo_company = Company(
            id=demo_company_id,
            name="Nueva Planta Demo",
            is_active=True
        )
        db.add(demo_company)
    
    member_role = Role(
        id=uuid.uuid4(),
        name="member",
        company_id=demo_company_id,
        is_active=True
    )
    db.add(member_role)
    
    await db.flush()
    
    # 2. Vincular a Charly con Scopes vac\u00edos (V4 Spec)
    # Check if link exists
    res = await db.execute(select(UserCompanyRole).where(
        UserCompanyRole.user_id == charly_id,
        UserCompanyRole.company_id == demo_company_id
    ))
    link = res.scalar_one_or_none()
    if not link:
        link = UserCompanyRole(
            user_id=charly_id,
            company_id=demo_company_id,
            role_id=member_role.id,
            scopes=[], # V4 Seeding: Charly en Demo no tiene scopes
            is_active=True
        )
        db.add(link)
    
    await db.commit()
    
    # 3. Validaci\u00f3n: El usuario debe tener acceso pero la lista de scopes debe estar vac\u00eda
    stmt = select(UserCompanyRole).where(
        UserCompanyRole.user_id == charly_id,
        UserCompanyRole.company_id == demo_company_id
    )
    result = await db.execute(stmt)
    link_db = result.scalar_one()
    
    assert link_db.company_id == demo_company_id
    assert link_db.scopes == []
    assert len(link_db.scopes) == 0
