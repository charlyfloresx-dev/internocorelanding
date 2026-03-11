"""
Tests for PreferenceService channel selection logic.
Run with: pytest tests/notification_service/ -v
"""
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

# We import the service under test
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend/notification_service'))
from app.services.preference_service import PreferenceService
from app.models.preferences import UserPreferences


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def make_preferences(in_app=True, email=True, push=False) -> UserPreferences:
    pref = UserPreferences()
    pref.receive_in_app = in_app
    pref.receive_email = email
    pref.receive_push = push
    return pref


async def _mock_db(pref=None) -> AsyncSession:
    """Return a mock async session that returns `pref` from scalar_one_or_none."""
    result = MagicMock()
    result.scalar_one_or_none = MagicMock(return_value=pref)
    db = AsyncMock(spec=AsyncSession)
    db.execute = AsyncMock(return_value=result)
    return db


# ──────────────────────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_high_priority_forces_all_channels():
    """HIGH priority must override preferences and return all 3 channels."""
    db = await _mock_db(pref=make_preferences(in_app=False, email=False, push=False))
    svc = PreferenceService(db)
    channels = await svc.get_user_channels(
        user_id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        priority="HIGH",
    )
    assert set(channels) == {"IN_APP", "EMAIL", "PUSH"}


@pytest.mark.asyncio
async def test_low_priority_respects_preferences():
    """LOW priority should respect user flags (IN_APP + EMAIL, no PUSH)."""
    db = await _mock_db(pref=make_preferences(in_app=True, email=True, push=False))
    svc = PreferenceService(db)
    channels = await svc.get_user_channels(
        user_id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        priority="LOW",
    )
    assert "IN_APP" in channels
    assert "EMAIL" in channels
    assert "PUSH" not in channels


@pytest.mark.asyncio
async def test_no_preferences_returns_default_in_app():
    """When no UserPreferences record exists, default to IN_APP only."""
    db = await _mock_db(pref=None)
    svc = PreferenceService(db)
    channels = await svc.get_user_channels(
        user_id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        priority="MEDIUM",
    )
    assert channels == ["IN_APP"]


@pytest.mark.asyncio
async def test_all_channels_disabled_returns_empty():
    """If user explicitly disabled all channels (non-HIGH priority), return empty list."""
    db = await _mock_db(pref=make_preferences(in_app=False, email=False, push=False))
    svc = PreferenceService(db)
    channels = await svc.get_user_channels(
        user_id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        priority="LOW",
    )
    assert channels == []
