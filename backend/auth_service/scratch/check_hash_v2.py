import hashlib
import sys

def hash_rfid(rfid_tag: str) -> str:
    salt = "INTERNO_HR_RFID_DEFAULT_SALT_CHANGE_ME"
    salted = f"{salt}:{rfid_tag}"
    return hashlib.sha256(salted.encode("utf-8")).hexdigest()

tag = "2327559684"
result = hash_rfid(tag)
print(f"Tag: {tag}")
print(f"Salt: INTERNO_HR_RFID_DEFAULT_SALT_CHANGE_ME")
print(f"Hash: {result}")
