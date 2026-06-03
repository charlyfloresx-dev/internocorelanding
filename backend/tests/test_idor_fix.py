"""
Phase 179A P0.2: IDOR Fix in Rate Limiting
Tests verify that rate limit buckets use JWT-verified claims, not client-controlled headers.
"""
import pytest
from unittest.mock import Mock
from uuid import uuid4
from fastapi import Request

from common.security.limiter import multi_layer_key_func


class TestIDORFixInRateLimiting:
    """Verify company_id comes from JWT, not X-Company-ID header."""

    def test_rate_limit_uses_jwt_claims_not_header(self):
        """Rate limit should use user.sub from JWT, never trust X-Company-ID header."""
        user_id = str(uuid4())
        header_company_id = str(uuid4())

        # JWT-verified token
        user_token = Mock()
        user_token.sub = user_id
        # No company_id attribute to force use of user.sub layer

        request = Mock(spec=Request)
        request.state = Mock(user_token=user_token)
        request.headers = {
            "X-Company-ID": header_company_id,  # Attacker tries to inject
        }

        result = multi_layer_key_func(request)

        # Should use JWT user.sub, NOT header value
        expected = f"user:{user_id}"
        assert result == expected, f"Should use JWT sub, not header"
        assert header_company_id not in result, "Should not accept X-Company-ID header"

    def test_header_company_id_alone_not_accepted(self):
        """X-Company-ID header alone (without JWT) should not be used."""
        header_company_id = str(uuid4())

        request = Mock(spec=Request)
        request.state = Mock(user_token=None)  # No JWT token
        request.headers = {
            "X-Company-ID": header_company_id,  # Client-provided, should be ignored
        }
        request.client = Mock(host="192.168.1.1")

        result = multi_layer_key_func(request)

        # Should NOT use the header value
        assert header_company_id not in result, "Should not use X-Company-ID without JWT"
        assert result.startswith("ip:"), "Should fall back to IP-based limiting"

    def test_user_id_from_jwt_takes_priority_over_headers(self):
        """User ID from JWT should be used before any header-based identifiers."""
        user_id = str(uuid4())
        header_company_id = str(uuid4())
        header_user_id = str(uuid4())

        user_token = Mock()
        user_token.sub = user_id

        request = Mock(spec=Request)
        request.state = Mock(user_token=user_token)
        request.headers = {
            "X-User-ID": header_user_id,      # Should be ignored
            "X-Company-ID": header_company_id, # Should be ignored
        }

        result = multi_layer_key_func(request)

        # Should use JWT sub exclusively
        expected = f"user:{user_id}"
        assert result == expected
        assert header_user_id not in result
        assert header_company_id not in result

    def test_jwt_company_id_not_from_header(self):
        """When user has no sub, company_id comes only from JWT, not header."""
        jwt_company_id = str(uuid4())
        header_company_id = str(uuid4())

        # JWT with company_id but no user ID
        user_token = Mock()
        user_token.sub = None  # No user ID
        user_token.company_id = jwt_company_id

        request = Mock(spec=Request)
        request.state = Mock(user_token=user_token)
        request.headers = {
            "X-Company-ID": header_company_id,  # Different from JWT
        }

        result = multi_layer_key_func(request)

        # Should use JWT company_id, not header
        expected = f"tenant:{jwt_company_id}"
        assert result == expected
        assert header_company_id not in result, "Should not accept header value"

    def test_no_spoofing_via_x_company_id_header(self):
        """Attacker cannot spoof competitor's rate limit bucket via X-Company-ID header."""
        my_id = str(uuid4())
        attacker_target_id = str(uuid4())

        user_token = Mock()
        user_token.sub = my_id
        # Sub exists, so company_id layer won't be checked

        request = Mock(spec=Request)
        request.state = Mock(user_token=user_token)
        request.headers = {
            "X-Company-ID": attacker_target_id,  # Spoofing attempt
        }

        result = multi_layer_key_func(request)

        # Rate limit bucket based on MY ID, not spoofed ID
        expected = f"user:{my_id}"
        assert result == expected
        assert attacker_target_id not in result

    def test_each_user_has_independent_rate_limit_bucket(self):
        """Different users should have independent rate limit buckets."""
        user_a_id = str(uuid4())
        user_b_id = str(uuid4())

        user_a = Mock()
        user_a.sub = user_a_id

        request_a = Mock(spec=Request)
        request_a.state = Mock(user_token=user_a)
        request_a.headers = {}

        user_b = Mock()
        user_b.sub = user_b_id

        request_b = Mock(spec=Request)
        request_b.state = Mock(user_token=user_b)
        request_b.headers = {}

        result_a = multi_layer_key_func(request_a)
        result_b = multi_layer_key_func(request_b)

        # Each user should have their own bucket
        assert result_a == f"user:{user_a_id}"
        assert result_b == f"user:{user_b_id}"
        assert result_a != result_b, "Different users must have different buckets"

    def test_unauthenticated_requests_use_ip_not_header(self):
        """Unauthenticated requests should use IP, never header-based identifiers."""
        header_company_id = str(uuid4())
        client_ip = "203.0.113.42"

        request = Mock(spec=Request)
        request.state = Mock(user_token=None)  # Unauthenticated
        request.headers = {
            "X-Company-ID": header_company_id,
            "X-Real-IP": client_ip,
        }

        result = multi_layer_key_func(request)

        # Should use X-Real-IP, NOT X-Company-ID
        assert result == f"ip:{client_ip}"
        assert header_company_id not in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
