"""
Tests for NotificationClient — RTR breach alert system.

Test coverage:
- Success case (200, 202 responses)
- Timeout case (3s timeout)
- 5xx error case
- Network unreachable case
- Exception handling (no exceptions propagated)
- Fire-and-forget pattern (never blocks)
"""
import pytest
import httpx
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock, MagicMock

from auth_app.infrastructure.clients.notification_client import NotificationClient


@pytest.fixture
def notification_client():
    """Create a NotificationClient instance for testing."""
    return NotificationClient()


@pytest.fixture
def sample_params():
    """Standard breach alert parameters."""
    return {
        "company_id": uuid4(),
        "user_id": uuid4(),
        "reason": "REUSE_DETECTED",
        "ip_address": "192.168.1.100",
        "timestamp": datetime.now(timezone.utc),
        "user_agent": "Mozilla/5.0",
    }


class TestNotificationClientSuccess:
    """Success cases — alert sent to notification_service."""

    @pytest.mark.asyncio
    async def test_send_breach_alert_http_200(self, notification_client, sample_params):
        """Test successful breach alert with HTTP 200."""
        with patch("httpx.AsyncClient") as mock_async_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 200

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None

            mock_async_client_class.return_value = mock_client

            # Should not raise
            await notification_client.send_breach_alert(**sample_params)

            # Verify POST was called
            mock_client.post.assert_called_once()
            call_kwargs = mock_client.post.call_args[1]
            assert call_kwargs["json"]["event_type"] == "RTRBreachDetected"
            assert call_kwargs["json"]["reason"] == "REUSE_DETECTED"

    @pytest.mark.asyncio
    async def test_send_breach_alert_http_202(self, notification_client, sample_params):
        """Test successful breach alert with HTTP 202 (Accepted)."""
        with patch("httpx.AsyncClient") as mock_async_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 202  # Async accepted

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None

            mock_async_client_class.return_value = mock_client

            # Should not raise
            await notification_client.send_breach_alert(**sample_params)

            mock_client.post.assert_called_once()


class TestNotificationClientResilience:
    """Failure cases — no exceptions propagated, all logged."""

    @pytest.mark.asyncio
    async def test_timeout_failure_logged_not_raised(self, notification_client, sample_params):
        """Test timeout: logged but not raised (best-effort pattern)."""
        with patch("httpx.AsyncClient") as mock_async_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None

            mock_async_client_class.return_value = mock_client

            # Should NOT raise
            with patch("auth_app.infrastructure.clients.notification_client.logger") as mock_logger:
                await notification_client.send_breach_alert(**sample_params)

                # Should log warning
                mock_logger.warning.assert_called_once()
                assert "timeout" in mock_logger.warning.call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_http_500_failure_logged_not_raised(self, notification_client, sample_params):
        """Test 5xx response: logged but not raised."""
        with patch("httpx.AsyncClient") as mock_async_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 500

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None

            mock_async_client_class.return_value = mock_client

            # Should NOT raise
            with patch("auth_app.infrastructure.clients.notification_client.logger") as mock_logger:
                await notification_client.send_breach_alert(**sample_params)

                # Should log warning (not error, since fallback is expected)
                mock_logger.warning.assert_called_once()
                assert "500" in mock_logger.warning.call_args[0][0]

    @pytest.mark.asyncio
    async def test_network_error_logged_not_raised(self, notification_client, sample_params):
        """Test network unreachable: logged but not raised."""
        with patch("httpx.AsyncClient") as mock_async_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=ConnectionError("Network unreachable"))
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None

            mock_async_client_class.return_value = mock_client

            # Should NOT raise
            with patch("auth_app.infrastructure.clients.notification_client.logger") as mock_logger:
                await notification_client.send_breach_alert(**sample_params)

                # Should log error (but not raise)
                mock_logger.error.assert_called_once()
                assert "failed" in mock_logger.error.call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_generic_exception_logged_not_raised(self, notification_client, sample_params):
        """Test generic exception: logged but not raised."""
        with patch("httpx.AsyncClient") as mock_async_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=ValueError("Invalid payload"))
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None

            mock_async_client_class.return_value = mock_client

            # Should NOT raise
            with patch("auth_app.infrastructure.clients.notification_client.logger") as mock_logger:
                await notification_client.send_breach_alert(**sample_params)

                mock_logger.error.assert_called_once()
                assert "ValueError" in mock_logger.error.call_args[0][0]


class TestNotificationClientPayload:
    """Verify correct payload structure sent to notification_service."""

    @pytest.mark.asyncio
    async def test_payload_structure(self, notification_client, sample_params):
        """Test that payload contains all required fields."""
        with patch("httpx.AsyncClient") as mock_async_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 202

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None

            mock_async_client_class.return_value = mock_client

            await notification_client.send_breach_alert(**sample_params)

            # Extract the payload from the call
            call_kwargs = mock_client.post.call_args[1]
            payload = call_kwargs["json"]

            # Verify all required fields
            assert "event_id" in payload
            assert payload["event_type"] == "RTRBreachDetected"
            assert payload["company_id"] == str(sample_params["company_id"])
            assert payload["user_id"] == str(sample_params["user_id"])
            assert payload["reason"] == "REUSE_DETECTED"
            assert payload["ip_address"] == "192.168.1.100"
            assert "timestamp" in payload
            assert payload["user_agent"] == "Mozilla/5.0"

    @pytest.mark.asyncio
    async def test_default_user_agent(self, notification_client):
        """Test that user_agent defaults to 'unknown' when not provided."""
        params = {
            "company_id": uuid4(),
            "user_id": uuid4(),
            "reason": "REUSE_DETECTED",
            "ip_address": "10.0.0.1",
            "timestamp": datetime.now(timezone.utc),
        }

        with patch("httpx.AsyncClient") as mock_async_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 202

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None

            mock_async_client_class.return_value = mock_client

            await notification_client.send_breach_alert(**params)

            call_kwargs = mock_client.post.call_args[1]
            payload = call_kwargs["json"]

            assert payload["user_agent"] == "unknown"


class TestNotificationClientHeaders:
    """Verify correct headers sent."""

    @pytest.mark.asyncio
    async def test_headers_include_company_id(self, notification_client, sample_params):
        """Test that X-Company-ID header is sent."""
        with patch("httpx.AsyncClient") as mock_async_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 202

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None

            mock_async_client_class.return_value = mock_client

            await notification_client.send_breach_alert(**sample_params)

            call_kwargs = mock_client.post.call_args[1]
            headers = call_kwargs["headers"]

            assert "X-Company-ID" in headers
            assert headers["X-Company-ID"] == str(sample_params["company_id"])
            assert headers["Content-Type"] == "application/json"


class TestNotificationClientFireAndForget:
    """Verify fire-and-forget pattern — async call doesn't block caller."""

    @pytest.mark.asyncio
    async def test_never_raises_exception(self, notification_client, sample_params):
        """Test that no exception is raised regardless of error."""
        exceptions_to_test = [
            httpx.TimeoutException("timeout"),
            ConnectionError("network error"),
            ValueError("invalid data"),
            RuntimeError("service error"),
        ]

        for exc in exceptions_to_test:
            with patch("httpx.AsyncClient") as mock_async_client_class:
                mock_client = AsyncMock()
                mock_client.post = AsyncMock(side_effect=exc)
                mock_client.__aenter__.return_value = mock_client
                mock_client.__aexit__.return_value = None

                mock_async_client_class.return_value = mock_client

                # Should never raise
                try:
                    await notification_client.send_breach_alert(**sample_params)
                except Exception as e:
                    pytest.fail(f"send_breach_alert raised {type(e).__name__}: {e}")
