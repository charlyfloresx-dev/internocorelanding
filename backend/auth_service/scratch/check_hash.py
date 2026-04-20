import hashlib
import sys

def hash_rfid(rfid_tag: str) -> str:
    # Mimic the app's hashing logic (SHA-256)
    return hashlib.sha256(rfid_tag.encode()).hexdigest()

tag = "2327559684"
result = hash_rfid(tag)
print(f"Tag: {tag}")
print(f"Hash: {result}")
