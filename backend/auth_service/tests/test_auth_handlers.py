import pytest
from uuid import uuid4
from sqlalchemy.future import select
from app.queries.login_query import LoginQuery, LoginQueryHandler
from app.commands.select_company_command import SelectCompanyCommand, SelectCompanyCommandHandler
from app.models import UserCompanyRole
from common.exceptions import UnauthorizedException

@pytest.mark.asyncio
async def test_login_query_success(db, user_factory, company_factory, role_factory):
    # Arrange
    company = await company_factory(name="Handshake Corp")
    user = await user_factory(email="login@example.com", company_id=company.id)
    role = await role_factory(name="Admin")
    
    db.add(UserCompanyRole(user_id=user.id, company_id=company.id, role_id=role.id))
    await db.commit()

    handler = LoginQueryHandler(db)
    query = LoginQuery(email="login@example.com", password="password123")

    # Act
    result = await handler.handle(query)

    # Assert
    assert result.selection_token is not None
    assert len(result.companies) == 1
    assert result.companies[0].company_id == company.id

@pytest.mark.asyncio
async def test_select_company_handler_success(db, user_factory, company_factory, role_factory):
    # Arrange
    company = await company_factory(name="Target Corp")
    user = await user_factory(company_id=company.id)
    role = await role_factory(name="operator")
    
    db.add(UserCompanyRole(user_id=user.id, company_id=company.id, role_id=role.id))
    await db.commit()

    handler = SelectCompanyCommandHandler(db)
    command = SelectCompanyCommand(user_id=user.id, company_id=company.id)

    # Act
    result = await handler.handle(command)

    # Assert
    assert "access_token" in result
    assert result["company_id"] == str(company.id)

@pytest.mark.asyncio
async def test_select_company_handler_idor_attack(db, user_factory, company_factory, role_factory):
    # Arrange: Usuario en Corp A intenta elegir Corp B (ajena)
    corp_a = await company_factory(name="Corp A")
    corp_b = await company_factory(name="Corp B")
    user = await user_factory(company_id=corp_a.id)
    role = await role_factory()
    
    db.add(UserCompanyRole(user_id=user.id, company_id=corp_a.id, role_id=role.id))
    await db.commit()

    handler = SelectCompanyCommandHandler(db)
    # ATAQUE: user_id de Corp A pide token para Corp B
    command = SelectCompanyCommand(user_id=user.id, company_id=corp_b.id)

    # Act & Assert
    with pytest.raises(UnauthorizedException) as exc:
        await handler.handle(command)
    assert "User not associated with this company" in str(exc.value.message)
