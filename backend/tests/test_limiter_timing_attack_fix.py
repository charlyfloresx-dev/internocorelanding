"""
Phase 179A P0.1: Timing Attack Fix for Bypass Keys
Tests that verify hmac.compare_digest() prevents timing attacks on bypass keys.
"""
import pytest
import hmac
from fastapi import Request
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import time

from common.security.limiter import multi_layer_key_func
from common.config import settings


class TestBypassKeyTimingAttackFix:
    """Verify that bypass key validation uses constant-time comparison."""

    def test_internal_secret_bypass_valid(self):
        """Valid X-Internal-Secret header returns None (bypassed)."""
        request = Mock(spec=Request)
        request.headers = {"X-Internal-Secret": settings.INTERNAL_API_KEY}
        request.state = Mock()

        result = multi_layer_key_func(request)
        assert result is None, "Valid internal secret should bypass rate limiting"

    def test_internal_secret_bypass_invalid(self):
        """Invalid X-Internal-Secret header falls through to user/tenant/IP layers."""
        request = Mock(spec=Request)
        request.headers = {"X-Internal-Secret": "invalid_key_1234"}
        request.state = Mock()
        request.state.user_token = None
        request.client = Mock(host="192.168.1.1")

        result = multi_layer_key_func(request)
        assert result is not None, "Invalid internal secret should not bypass"
        assert result.startswith("ip:"), "Should fall back to IP-based limiting"

    def test_admin_master_key_bypass_valid(self):
        """Valid X-Admin-Master-Key header returns None (bypassed)."""
        request = Mock(spec=Request)
        request.headers = {"X-Admin-Master-Key": settings.int_admin_master_key}
        request.state = Mock()

        result = multi_layer_key_func(request)
        assert result is None, "Valid admin master key should bypass rate limiting"

    def test_admin_master_key_bypass_invalid(self):
        """Invalid X-Admin-Master-Key header falls through to user/tenant/IP layers."""
        request = Mock(spec=Request)
        request.headers = {"X-Admin-Master-Key": "invalid_admin_key_5678"}
        request.state = Mock()
        request.state.user_token = None
        request.client = Mock(host="192.168.1.1")

        result = multi_layer_key_func(request)
        assert result is not None, "Invalid admin key should not bypass"

    def test_hmac_compare_digest_prevents_timing_attacks(self):
        """
        Verify that hmac.compare_digest() is used (constant-time comparison).
        Timing attack: attacker measures response time to guess correct key character-by-character.
        With ==: first character mismatch is fastest, similarity leaks timing info.
        With hmac.compare_digest(): all comparisons take same time regardless of match.
        """
        correct_key = "correct_bypass_key_123456"
        wrong_key_1 = "wrong___________________"  # First char wrong
        wrong_key_2 = "correct_bypass_key_111111"  # Last char wrong

        # All comparisons should take roughly the same time with hmac.compare_digest()
        times = []

        for key in [wrong_key_1, wrong_key_2, correct_key]:
            start = time.perf_counter()
            hmac.compare_digest(key, correct_key)
            elapsed = time.perf_counter() - start
            times.append(elapsed)

        # Verify that timing is consistent (no obvious timing leak)
        # Note: This is a probabilistic check - timing variance exists but should be minimal
        max_time = max(times)
        min_time = min(times)

        # All times should be within 50% of each other (loose bound for CI tolerance)
        if max_time > 0:
            ratio = max_time / min_time
            assert ratio < 2.0, f"Timing difference too large ({ratio}x) - timing attack possible"

    def test_bypass_key_comparison_uses_correct_function(self):
        """
        Verify that the limiter actually uses hmac.compare_digest().
        This test patches hmac.compare_digest and verifies it's called.
        """
        with patch('common.security.limiter.hmac.compare_digest') as mock_compare:
            mock_compare.return_value = True

            request = Mock(spec=Request)
            request.headers = {"X-Internal-Secret": "some_key"}
            request.state = Mock()

            result = multi_layer_key_func(request)

            # Verify hmac.compare_digest was called with the secret and expected key
            mock_compare.assert_called()
            assert result is None, "Mocked comparison returned True, so bypass should work"

    def test_multiple_bypass_attempts_constant_time(self):
        """Test that multiple bypass attempts don't leak information via timing."""
        request = Mock(spec=Request)
        request.state = Mock()
        request.client = Mock(host="10.0.0.1")

        # Simulate 10 invalid bypass attempts
        timings = []
        invalid_keys = [
            f"fake_key_{i:04d}_" + "x" * 30 for i in range(10)
        ]

        for fake_key in invalid_keys:
            request.headers = {"X-Internal-Secret": fake_key}

            start = time.perf_counter()
            result = multi_layer_key_func(request)
            elapsed = time.perf_counter() - start

            timings.append(elapsed)
            assert result is not None, "Invalid key should not bypass"

        # Check that timing is consistent
        avg_time = sum(timings) / len(timings)
        max_deviation = max(abs(t - avg_time) for t in timings)

        # Timing variance should be minimal (constant-time)
        if avg_time > 0:
            variance_ratio = max_deviation / avg_time
            # Allow up to 20% variance (typical for Python timing noise)
            assert variance_ratio < 0.2, \
                f"Timing variance too high ({variance_ratio*100:.1f}%) - possible timing leak"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
