import hashlib
import uuid
from typing import Optional

from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_rfid(raw_rfid: str) -> str:
    """
    Hash an RFID tag for secure storage.
    Uses SHA-256 with a static application salt (from config) for O(1) indexed lookups.
    This prevents rainbow table attacks while keeping verification fast.
    """
    salted = f"{settings.RFID_STATIC_SALT}:{raw_rfid}"
    hashed = hashlib.sha256(salted.encode("utf-8")).hexdigest()
    print(f"DEBUG_RFID: salt='{settings.RFID_STATIC_SALT}' raw='{raw_rfid}' hash='{hashed}'")
    return hashed


def verify_rfid(raw_rfid: str, hashed_rfid: str) -> bool:
    """Compare a raw scan input against the stored hash."""
    return hash_rfid(raw_rfid) == hashed_rfid


def hash_pin(raw_pin: str) -> str:
    """Hash a PIN using Bcrypt for strong password protection."""
    return pwd_context.hash(raw_pin)


def verify_pin(raw_pin: str, hashed_pin: str) -> bool:
    """Verify a PIN against a Bcrypt hash."""
    return pwd_context.verify(raw_pin, hashed_pin)
