import asyncio
from app.core.security import create_selection_token
from app.dependencies.auth import get_selection_payload
import uuid
from jose import jwt, JWTError
from app.core.config import settings
from pydantic import ValidationError

async def main():
    user_id = uuid.uuid4()
    token = create_selection_token(user_id)
    print("Generated token:", token)
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"verify_iat": False})
        print("Manual jwt.decode:", payload)
        
        from app.dependencies.auth import SelectionTokenPayload
        token_data = SelectionTokenPayload(**payload)
        print("Validation success:", token_data)
        
    except ValidationError as e:
        print("Pydantic ValidationError:", e.errors())
    except JWTError as e:
        print("JWTError:", e)
    except Exception as e:
        print("Other Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
