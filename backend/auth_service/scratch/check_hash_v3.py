import hashlib
import sys

def hash_rfid(rfid_tag: str) -> str:
    salt = "INTERNO_HR_RFID_ALT_DEV_CHANGE_IN_PROD" # Typo check? 
    # Wait, let me look at docker-compose line 68 again carefully.
    # CORE_HR_RFID_SALT=INTERNO_HR_RFID_SALT_DEV_CHANGE_IN_PROD
    
    salt = "INTERNO_HR_RFID_SALT_DEV_CHANGE_IN_PROD"
    salted = f"{salt}:{rfid_tag}"
    return hashlib.sha256(salted.encode("utf-8")).hexdigest()

tag = "2327559684"
result = hash_rfid(tag)
print(f"Tag: {tag}")
print(f"Salt: INTERNO_HR_RFID_SALT_DEV_CHANGE_IN_PROD")
print(f"Hash: {result}")
