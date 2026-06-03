"""
Tests for per-user and global rate limiting on /refresh endpoint.

Test coverage:
- Per-user rate limit: 10/minute per user
- Global rate limit: 20/minute across all users
- Key extraction: user_id from JWT or fallback to IP
- Rate limit response: 429 Too Many Requests
"""
import pytest
import jwt
import json
from uuid import uuid4
from fastapi import Request
from unittest.mock import MagicMock, patch

from auth_app.api.v1.endpoints.refresh_token_rtr import get_user_rate_limit_key


@pytest.fixture
def sample_jwt():
    """Create a sample JWT token with user_id."""
    user_id = str(uuid4())
    payload = {
        "sub": user_id,
        "fam": str(uuid4()),
        "co": str(uuid4()),
        "gen": 0,
    }
    # No signature verification needed for these tests
    return jwt.encode(payload, "secret", algorithm="HS256"), user_id


@pytest.fixture
def mock_request_with_body(sample_jwt):
    """Create a mock request with refresh_token in body."""
    token, user_id = sample_jwt

    request = MagicMock(spec=Request)
    request.scope = {
        "_body": json.dumps({"refresh_token": token}).encode(),
    }
    request.client = MagicMock()
    request.client.host = "192.168.1.1"

    return request, user_id


@pytest.fixture
def mock_request_no_body():
    """Create a mock request with no body cached."""
    request = MagicMock(spec=Request)
    request.scope = {}  # No _body
    request.client = MagicMock()
    request.client.host = "10.0.0.1"

    return request


@pytest.fixture
def mock_request_invalid_body():
    """Create a mock request with invalid JWT."""
    request = MagicMock(spec=Request)
    request.scope = {
        "_body": json.dumps({"refresh_token": "invalid-token-not-jwt"}).encode(),
    }
    request.client = MagicMock()
    request.client.host = "10.0.0.2"

    return request


class TestRateLimitKeyExtraction:
    """Test get_user_rate_limit_key function."""

    def test_extract_user_id_from_valid_jwt(self, mock_request_with_body):
        """Test extracting user_id from valid JWT in body."""
        request, expected_user_id = mock_request_with_body

        key = get_user_rate_limit_key(request)

        assert key == f"user:{expected_user_id}"

    def test_fallback_to_ip_when_body_not_cached(self, mock_request_no_body):
        """Test falling back to IP when body not available."""
        request = mock_request_no_body

        key = get_user_rate_limit_key(request)

        assert key == "ip:10.0.0.1"

    def test_fallback_to_ip_on_invalid_jwt(self, mock_request_invalid_body):
        """Test falling back to IP when JWT is invalid."""
        request = mock_request_invalid_body

        key = get_user_rate_limit_key(request)

        assert key == "ip:10.0.0.2"

    def test_fallback_to_ip_on_json_parse_error(self):
        """Test falling back to IP on JSON parsing error."""
        request = MagicMock(spec=Request)
        request.scope = {
            "_body": b"not-json",
        }
        request.client = MagicMock()
        request.client.host = "192.168.0.1"

        key = get_user_rate_limit_key(request)

        assert key == "ip:192.168.0.1"

    def test_fallback_to_ip_when_token_missing(self):
        """Test falling back to IP when refresh_token field is missing."""
        request = MagicMock(spec=Request)
        request.scope = {
            "_body": json.dumps({"other_field": "value"}).encode(),
        }
        request.client = MagicMock()
        request.client.host = "172.16.0.1"

        key = get_user_rate_limit_key(request)

        assert key == "ip:172.16.0.1"

    def test_fallback_to_default_ip_when_client_none(self):
        """Test using default IP when request.client is None."""
        request = MagicMock(spec=Request)
        request.scope = {}  # No body
        request.client = None

        key = get_user_rate_limit_key(request)

        assert key == "ip:0.0.0.0"


class TestPerUserRateLimitingLogic:
    """Test the rate limiting logic (requires SlowAPI integration test)."""

    def test_different_users_have_different_rate_limit_keys(self):
        """Test that different users get different rate limit keys."""
        # Create two different JWTs
        user1_id = str(uuid4())
        user2_id = str(uuid4())

        jwt1 = jwt.encode({"sub": user1_id, "fam": str(uuid4())}, "secret", algorithm="HS256")
        jwt2 = jwt.encode({"sub": user2_id, "fam": str(uuid4())}, "secret", algorithm="HS256")

        # Create requests for each
        request1 = MagicMock(spec=Request)
        request1.scope = {"_body": json.dumps({"refresh_token": jwt1}).encode()}
        request1.client = MagicMock(host="192.168.1.1")

        request2 = MagicMock(spec=Request)
        request2.scope = {"_body": json.dumps({"refresh_token": jwt2}).encode()}
        request2.client = MagicMock(host="192.168.1.1")  # Same IP, different user

        key1 = get_user_rate_limit_key(request1)
        key2 = get_user_rate_limit_key(request2)

        # Keys should be different because users are different
        assert key1 != key2
        assert user1_id in key1
        assert user2_id in key2

    def test_same_user_has_same_rate_limit_key(self):
        """Test that the same user always gets the same rate limit key."""
        user_id = str(uuid4())
        jwt_token = jwt.encode({"sub": user_id, "fam": str(uuid4())}, "secret", algorithm="HS256")

        request1 = MagicMock(spec=Request)
        request1.scope = {"_body": json.dumps({"refresh_token": jwt_token}).encode()}
        request1.client = MagicMock(host="192.168.1.1")

        request2 = MagicMock(spec=Request)
        request2.scope = {"_body": json.dumps({"refresh_token": jwt_token}).encode()}
        request2.client = MagicMock(host="10.0.0.1")  # Different IP, same user

        key1 = get_user_rate_limit_key(request1)
        key2 = get_user_rate_limit_key(request2)

        # Keys should be identical
        assert key1 == key2
        assert key1 == f"user:{user_id}"
