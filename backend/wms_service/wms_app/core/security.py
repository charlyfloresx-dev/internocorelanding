from jose import jwt, JWTError
from typing import Optional, Dict, Any
from .config import settings

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        decoded_payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return decoded_payload
    except JWTError:
        return None
