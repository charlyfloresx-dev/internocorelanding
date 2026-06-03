"""Pytest configuration for Phase 179A security tests."""
import os
import sys
from pathlib import Path

# Ensure backend directory is in path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Set environment variables for tests
os.environ.setdefault("CORE_ENV_MODE", "test")
os.environ.setdefault("CORE_SECRET_KEY", "test_secret_key_123456_test_secret_key_123456")
os.environ.setdefault("CORE_ADMIN_MASTER_KEY", "ROTATED_MASTER_KEY_GOD_MODE")
os.environ.setdefault("CORE_INTERNAL_API_KEY", "ROTATED_INTERNAL_API_KEY_4567")
os.environ.setdefault("CORE_DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5433/test_db")
os.environ.setdefault("CORE_REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("CORE_ALGORITHM", "HS256")
os.environ.setdefault("CORE_ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
os.environ.setdefault("CORE_MULTI_TENANT_MODE", "True")
os.environ.setdefault("CORE_STORAGE_BACKEND", "local")
os.environ.setdefault("CORE_HR_RFID_SALT", "ROTATED_HR_RFID_SALT_7890")
os.environ.setdefault("CORE_BANXICO_TOKEN", "test_token")
os.environ.setdefault("CORE_STRIPE_SECRET_KEY", "sk_test_123")
os.environ.setdefault("CORE_RESEND_API_KEY", "re_test_123")
