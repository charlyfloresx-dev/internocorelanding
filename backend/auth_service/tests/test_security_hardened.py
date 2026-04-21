import uuid
import pytest
from datetime import datetime, timezone, timedelta
from jose import jwt
from auth_app.core import security
from auth_app.core.config import settings

@pytest.mark.async_state
def test_token_taxonomy():
    user_id = uuid.uuid4()
    company_id = uuid.uuid4()
    
    # 1. Create access token
    access = security.create_access_token(str(user_id), str(company_id), {"roles": ["admin"]})
    decoded_access = security.decode_token(access)
    assert decoded_access["typ"] == "access"
    assert decoded_access["company_id"] == str(company_id)
    
    # 2. Create refresh token
    refresh = security.create_refresh_token(user_id, company_id)
    decoded_refresh = security.decode_token(refresh)
    assert decoded_refresh["typ"] == "refresh"
    assert decoded_refresh["company_id"] == str(company_id)

@pytest.mark.async_state
def test_hash_token_idempotency():
    token = "some-secure-token-123"
    h1 = security.hash_token(token)
    h2 = security.hash_token(token)
    assert h1 == h2
    assert len(h1) == 64 # SHA-256 hex
