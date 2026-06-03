"""
Phase 179A P0.4: Scope Elevation Prevention
Tests verify scopes are validated against server-side SSOT before accepting.
"""
import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from common.security.scope_validator import ScopeValidator, verify_user_scopes


class TestScopeElevationFix:
    """Verify JWT scopes are validated against Redis SSOT."""

    @pytest.mark.asyncio
    async def test_valid_scopes_accepted(self):
        """Valid scopes matching server record are accepted."""
        user_id = str(uuid4())
        company_id = str(uuid4())
        scopes = ["master_data.product.read", "inventory.warehouse.write"]

        validator = ScopeValidator()

        # Mock Redis with cached scopes
        mock_client = AsyncMock()
        mock_client.smembers = AsyncMock(return_value=set(scopes))

        with patch.object(validator, '_get_client', return_value=mock_client):
            is_valid = await validator.validate_scopes(user_id, company_id, scopes)
            assert is_valid is True, "Valid scopes should be accepted"

    @pytest.mark.asyncio
    async def test_elevated_scopes_rejected(self):
        """JWT claims elevated scopes not in server record → rejected."""
        user_id = str(uuid4())
        company_id = str(uuid4())
        cached_scopes = ["master_data.product.read"]
        jwt_scopes = ["master_data.product.read", "admin.user.delete"]  # Elevated

        validator = ScopeValidator()

        mock_client = AsyncMock()
        mock_client.smembers = AsyncMock(return_value=set(cached_scopes))

        with patch.object(validator, '_get_client', return_value=mock_client):
            is_valid = await validator.validate_scopes(user_id, company_id, jwt_scopes)
            assert is_valid is False, "Elevated scopes should be rejected"

    @pytest.mark.asyncio
    async def test_cache_miss_defaults_to_deny(self):
        """FAIL SECURE: Cache miss (no scopes cached) denies access."""
        user_id = str(uuid4())
        company_id = str(uuid4())
        jwt_scopes = ["admin.*"]

        validator = ScopeValidator()

        mock_client = AsyncMock()
        mock_client.smembers = AsyncMock(return_value=set())  # Empty = no entry

        with patch.object(validator, '_get_client', return_value=mock_client):
            is_valid = await validator.validate_scopes(user_id, company_id, jwt_scopes)
            assert is_valid is False, "Cache miss should deny access (FAIL SECURE)"

    @pytest.mark.asyncio
    async def test_redis_error_defaults_to_deny(self):
        """FAIL SECURE: Redis errors deny access."""
        user_id = str(uuid4())
        company_id = str(uuid4())

        validator = ScopeValidator()

        # Mock _get_client to raise exception
        async def failing_get_client():
            raise Exception("Redis down")

        with patch.object(validator, '_get_client', side_effect=failing_get_client):
            is_valid = await validator.validate_scopes(user_id, company_id, ["*"])
            assert is_valid is False, "Redis error should deny access (FAIL SECURE)"

    @pytest.mark.asyncio
    async def test_wildcard_admin_scope_accepted(self):
        """Wildcard scope '*' is accepted if in cached scopes."""
        user_id = str(uuid4())
        company_id = str(uuid4())

        validator = ScopeValidator()

        mock_client = AsyncMock()
        mock_client.smembers = AsyncMock(return_value={"*"})  # Admin has wildcard

        with patch.object(validator, '_get_client', return_value=mock_client):
            is_valid = await validator.validate_scopes(user_id, company_id, ["*"])
            assert is_valid is True, "Wildcard should be accepted if cached"

    @pytest.mark.asyncio
    async def test_empty_jwt_scopes_rejected(self):
        """Empty JWT scopes are rejected."""
        user_id = str(uuid4())
        company_id = str(uuid4())

        validator = ScopeValidator()
        is_valid = await validator.validate_scopes(user_id, company_id, [])
        assert is_valid is False, "Empty scopes should be rejected"

    @pytest.mark.asyncio
    async def test_none_jwt_scopes_rejected(self):
        """None JWT scopes are rejected."""
        user_id = str(uuid4())
        company_id = str(uuid4())

        validator = ScopeValidator()
        is_valid = await validator.validate_scopes(user_id, company_id, None)
        assert is_valid is False, "None scopes should be rejected"

    @pytest.mark.asyncio
    async def test_scope_subset_validation(self):
        """JWT scopes must be subset of cached scopes."""
        user_id = str(uuid4())
        company_id = str(uuid4())
        cached_scopes = {"users.read", "users.write", "products.read"}
        jwt_scopes = ["users.read", "products.read"]  # Subset

        validator = ScopeValidator()

        mock_client = AsyncMock()
        mock_client.smembers = AsyncMock(return_value=cached_scopes)

        with patch.object(validator, '_get_client', return_value=mock_client):
            is_valid = await validator.validate_scopes(user_id, company_id, jwt_scopes)
            assert is_valid is True, "Subset should be accepted"

    @pytest.mark.asyncio
    async def test_per_user_scope_isolation(self):
        """Different users have independent scope records."""
        user_a = str(uuid4())
        user_b = str(uuid4())
        company_id = str(uuid4())
        scopes_a = ["users.read"]
        scopes_b = ["products.write"]

        validator = ScopeValidator()

        # User A has read scope
        mock_client_a = AsyncMock()
        mock_client_a.smembers = AsyncMock(return_value=set(scopes_a))

        # User B has write scope
        mock_client_b = AsyncMock()
        mock_client_b.smembers = AsyncMock(return_value=set(scopes_b))

        with patch.object(validator, '_get_client', return_value=mock_client_a):
            is_a = await validator.validate_scopes(user_a, company_id, scopes_a)

        with patch.object(validator, '_get_client', return_value=mock_client_b):
            is_b = await validator.validate_scopes(user_b, company_id, scopes_b)

        # Each should validate only their own scopes
        assert is_a is True
        assert is_b is True

        # But cross-validation should fail
        with patch.object(validator, '_get_client', return_value=mock_client_a):
            is_invalid = await validator.validate_scopes(user_a, company_id, scopes_b)
        assert is_invalid is False, "User A shouldn't have User B's scopes"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
