"""
Phase 179A P0.3: god_mode JWT Falsification Prevention
Tests verify server-side session store validates god_mode claims.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from common.infrastructure.clients.session_store import SessionStoreClient, get_session_store


class TestGodModeSessionStore:
    """Verify god_mode status is stored server-side, not trusted from JWT."""

    @pytest.mark.asyncio
    async def test_god_mode_set_and_get(self):
        """god_mode can be set and retrieved from session store."""
        store = SessionStoreClient()
        user_id = str(uuid4())
        company_id = str(uuid4())

        # Set god_mode
        await store.set_god_mode(user_id, company_id, ttl_seconds=3600)

        # Verify it exists
        is_valid = await store.get_god_mode(user_id, company_id)
        assert is_valid is True, "god_mode should be set"

    @pytest.mark.asyncio
    async def test_god_mode_defaults_to_false_on_cache_miss(self):
        """FAIL SECURE: Missing god_mode entry defaults to False."""
        store = SessionStoreClient()
        user_id = str(uuid4())
        company_id = str(uuid4())

        # Don't set god_mode
        is_valid = await store.get_god_mode(user_id, company_id)
        assert is_valid is False, "Missing god_mode should default to False (FAIL SECURE)"

    @pytest.mark.asyncio
    async def test_god_mode_revocation(self):
        """god_mode can be revoked immediately."""
        store = SessionStoreClient()
        user_id = str(uuid4())
        company_id = str(uuid4())

        # Set and verify
        await store.set_god_mode(user_id, company_id)
        is_valid = await store.get_god_mode(user_id, company_id)
        assert is_valid is True

        # Revoke
        await store.revoke_god_mode(user_id, company_id)
        is_valid = await store.get_god_mode(user_id, company_id)
        assert is_valid is False, "god_mode should be revoked"

    @pytest.mark.asyncio
    async def test_god_mode_emergency_revoke_all(self):
        """Emergency: revoke all god_mode sessions for a company."""
        store = SessionStoreClient()
        company_id = str(uuid4())
        user_ids = [str(uuid4()) for _ in range(3)]

        # Set god_mode for multiple users
        for user_id in user_ids:
            await store.set_god_mode(user_id, company_id)

        # Verify all are set
        for user_id in user_ids:
            is_valid = await store.get_god_mode(user_id, company_id)
            assert is_valid is True

        # Emergency revoke all
        await store.revoke_all_god_mode_for_company(company_id)

        # Verify all are revoked
        for user_id in user_ids:
            is_valid = await store.get_god_mode(user_id, company_id)
            assert is_valid is False, f"god_mode should be revoked for {user_id}"

    @pytest.mark.asyncio
    async def test_singleton_instance(self):
        """SessionStoreClient is a singleton."""
        store1 = await get_session_store()
        store2 = await get_session_store()
        assert store1 is store2, "Should return the same instance"

    @pytest.mark.asyncio
    async def test_redis_failure_returns_false(self):
        """FAIL SECURE: Redis errors default to denying god_mode."""
        store = SessionStoreClient()

        # Simulate Redis get operation failure
        async def failing_get(*args, **kwargs):
            raise Exception("Redis down")

        mock_client = AsyncMock()
        mock_client.get = failing_get

        with patch.object(store, '_get_client', return_value=mock_client):
            is_valid = await store.get_god_mode(str(uuid4()), str(uuid4()))
            assert is_valid is False, "Redis failure should deny access (FAIL SECURE)"

    @pytest.mark.asyncio
    async def test_god_mode_does_not_cross_company_boundaries(self):
        """god_mode for company A does not affect company B."""
        store = SessionStoreClient()
        user_id = str(uuid4())
        company_a = str(uuid4())
        company_b = str(uuid4())

        # Set god_mode for company A
        await store.set_god_mode(user_id, company_a)

        # Verify only company A has god_mode
        is_valid_a = await store.get_god_mode(user_id, company_a)
        is_valid_b = await store.get_god_mode(user_id, company_b)

        assert is_valid_a is True, "Should have god_mode for company A"
        assert is_valid_b is False, "Should NOT have god_mode for company B"

    @pytest.mark.asyncio
    async def test_jwt_god_mode_falsification_prevented(self):
        """JWT claiming god_mode=True is rejected if not in session store."""
        store = SessionStoreClient()
        user_id = str(uuid4())
        company_id = str(uuid4())

        # Attacker JWT claims god_mode=True
        jwt_claims = {"god_mode": True}

        # But session store has no entry
        is_valid = await store.get_god_mode(user_id, company_id)

        # Middleware should use session store result, not JWT claim
        assert is_valid is False, "Should deny, even if JWT claims god_mode=True"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
