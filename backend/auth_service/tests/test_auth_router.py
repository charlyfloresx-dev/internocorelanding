import pytest
from httpx import AsyncClient
from auth_app.models import UserCompanyRole
from auth_app.core.security import decode_token

@pytest.mark.asyncio
async def test_full_auth_handshake_flow(async_client: AsyncClient, db, user_factory, company_factory, role_factory):
    # 1. Arrange: Setup User & Company
    company = await company_factory(name="Handshake Integration Inc")
    user = await user_factory(email="fullflow@example.com", company_id=company.id)
    role = await role_factory(name="Admin")
    db.add(UserCompanyRole(user_id=user.id, company_id=company.id, role_id=role.id))
    await db.commit()

    # 2. Login (Handshake T1)
    login_payload = {"email": "fullflow@example.com", "password": "password123"}
    login_res = await async_client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    stoken = login_res.json()["data"]["selection_token"]
    assert stoken is not None

    # 3. Select Company (T2)
    select_payload = {"company_id": str(company.id)}
    headers = {"X-Selection-Token": stoken}
    select_res = await async_client.post("/api/v1/auth/select-company", json=select_payload, headers=headers)
    assert select_res.status_code == 200
    atoken = select_res.json()["data"]["access_token"]
    
    # Assert claims
    decoded = decode_token(atoken)
    assert decoded["company_id"] == str(company.id)
    assert "Admin" in decoded["role_names"]
    assert "jti" in decoded

@pytest.mark.asyncio
async def test_blacklist_revocation_at_middleware(async_client: AsyncClient, db, user_factory, company_factory, role_factory, redis_mock):
    # 1. Arrange: Logged in user
    company = await company_factory()
    user = await user_factory(company_id=company.id)
    role = await role_factory()
    db.add(UserCompanyRole(user_id=user.id, company_id=company.id, role_id=role.id))
    await db.commit()

    # Get Token
    login_res = await async_client.post("/api/v1/auth/login", json={"email": user.email, "password": "password123"})
    stoken = login_res.json()["data"]["selection_token"]
    select_res = await async_client.post("/api/v1/auth/select-company", json={"company_id": str(company.id)}, headers={"X-Selection-Token": stoken})
    atoken = select_res.json()["data"]["access_token"]
    jti = decode_token(atoken)["jti"]

    # 2. Blacklist the JTI
    await redis_mock.setex(f"blacklist:{jti}", 3600, "true")

    # 3. Act: Request protected endpoint
    headers = {"Authorization": f"Bearer {atoken}", "X-Company-Id": str(company.id)}
    response = await async_client.get("/api/v1/auth/me", headers=headers)

    # 4. Assert: Middleware must catch it
    assert response.status_code == 401
    assert "Token has been revoked" in response.json()["message"]

@pytest.mark.asyncio
async def test_idor_across_tenants_at_me_endpoint(async_client: AsyncClient, db, user_factory, company_factory, role_factory):
    # 1. Arrange: User in Corp A, attempts to use X-Company-Id of Corp B
    corp_a = await company_factory(name="Corp A")
    corp_b = await company_factory(name="Corp B")
    user_a = await user_factory(company_id=corp_a.id)
    role = await role_factory()
    db.add(UserCompanyRole(user_id=user_a.id, company_id=corp_a.id, role_id=role.id))
    await db.commit()

    # Get Token for Corp A
    login_res = await async_client.post("/api/v1/auth/login", json={"email": user_a.email, "password": "password123"})
    stoken = login_res.json()["data"]["selection_token"]
    select_res = await async_client.post("/api/v1/auth/select-company", json={"company_id": str(corp_a.id)}, headers={"X-Selection-Token": stoken})
    atoken = select_res.json()["data"]["access_token"]

    # 2. Act: Request /me with Corp B header (Attack)
    headers = {"Authorization": f"Bearer {atoken}", "X-Company-Id": str(corp_b.id)}
    response = await async_client.get("/api/v1/auth/me", headers=headers)

    # 3. Assert: TenantSecurityMiddleware must catch mismatch
    assert response.status_code == 403
    assert "Tenant Mismatch" in response.json()["message"]
