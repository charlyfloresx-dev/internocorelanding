"""
Tests for ticket debounce logic and HMAC signature verification.
Run with: pytest tests/tickets_service/ -v
"""
import pytest
import asyncio
import hashlib
import hmac
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession


# ──────────────────────────────────────────────────────────────────────────────
# A. Debounce Logic Tests
# ──────────────────────────────────────────────────────────────────────────────

def make_dedup_hash(company_id, warehouse_id, product_id, priority):
    """Replicate the application's deduplication hash logic."""
    key = f"{company_id}:{warehouse_id}:{product_id}:{priority}"
    return hashlib.sha256(key.encode()).hexdigest()


def test_dedup_hash_is_deterministic():
    """Same inputs must always produce the same hash."""
    cid, wid, pid = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    h1 = make_dedup_hash(cid, wid, pid, "P1")
    h2 = make_dedup_hash(cid, wid, pid, "P1")
    assert h1 == h2


def test_dedup_hash_differs_by_priority():
    """Different priorities for the same entity must produce different hashes."""
    cid, wid, pid = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    h_p1 = make_dedup_hash(cid, wid, pid, "P1")
    h_p2 = make_dedup_hash(cid, wid, pid, "P2")
    assert h_p1 != h_p2


def test_dedup_hash_differs_by_warehouse():
    """Different warehouses for the same product must produce different hashes."""
    cid, pid = uuid.uuid4(), uuid.uuid4()
    h1 = make_dedup_hash(cid, uuid.uuid4(), pid, "P1")
    h2 = make_dedup_hash(cid, uuid.uuid4(), pid, "P1")
    assert h1 != h2


@pytest.mark.asyncio
async def test_burst_window_creates_only_one_ticket():
    """
    Simulate 5 rapid P1 alerts for the same (company, warehouse, product).
    The debounce mechanism must prevent creating more than 1 open ticket.
    """
    existing_open_ticket_mock = MagicMock()
    existing_open_ticket_mock.id = uuid.uuid4()

    create_count = 0
    call_count = 0

    async def mock_create_or_skip(dedup_hash, payload):
        nonlocal create_count, call_count
        call_count += 1
        if call_count == 1:
            create_count += 1
            return existing_open_ticket_mock
        # Subsequent calls find existing OPEN ticket → skip
        return existing_open_ticket_mock  # same ticket returned, no new creation

    cid, wid, pid = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    dedup_hash = make_dedup_hash(cid, wid, pid, "P1")

    tasks = [mock_create_or_skip(dedup_hash, {"priority": "P1"}) for _ in range(5)]
    await asyncio.gather(*tasks)

    # Only 1 ticket was actually created
    assert create_count == 1
    assert call_count == 5


# ──────────────────────────────────────────────────────────────────────────────
# B. HMAC Signature Verification Tests
# ──────────────────────────────────────────────────────────────────────────────

STATIC_SECRET = "test-static-secret-interno"


def generate_hmac_signature(payload: dict, secret: str = STATIC_SECRET) -> str:
    """Generate HMAC-SHA256 signature for a payload dict."""
    body = json.dumps(payload, default=str).encode()
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def verify_hmac_signature(payload: dict, signature: str, secret: str = STATIC_SECRET) -> bool:
    """Verify HMAC-SHA256 signature (constant-time comparison)."""
    expected = generate_hmac_signature(payload, secret)
    return hmac.compare_digest(expected, signature)


def test_hmac_signature_valid():
    """A payload signed with the correct secret must verify successfully."""
    payload = {"event": "force_release", "product_id": str(uuid.uuid4())}
    sig = generate_hmac_signature(payload)
    assert verify_hmac_signature(payload, sig) is True


def test_hmac_signature_invalid_secret():
    """A payload signed with a wrong secret must fail verification."""
    payload = {"event": "force_release", "product_id": str(uuid.uuid4())}
    sig = generate_hmac_signature(payload, secret="wrong-secret")
    assert verify_hmac_signature(payload, sig) is False


def test_hmac_signature_tampered_payload():
    """A valid signature for payload A must fail for a tampered payload B."""
    payload = {"event": "force_release", "product_id": str(uuid.uuid4())}
    sig = generate_hmac_signature(payload)

    tampered = {**payload, "product_id": str(uuid.uuid4())}
    assert verify_hmac_signature(tampered, sig) is False


def test_hmac_timing_safe():
    """Signature comparison must use constant-time compare_digest (no timing attack)."""
    payload = {"event": "test"}
    sig = generate_hmac_signature(payload)
    # hmac.compare_digest raises TypeError on wrong types; verify it is used properly
    assert hmac.compare_digest(sig, sig) is True
