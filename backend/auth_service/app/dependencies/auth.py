from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token # Corrected import
from app.core.database import get_db # Corrected import
from app.services import AuthService # Corrected import
from app.schemas import AccessTokenResponse # Corrected import

# OAuth2PasswordBearer is usually for username/password login, but can be adapted for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login") 

async def get_current_user_payload(
    token: str = Depends(oauth2_scheme),
    x_company_id: Optional[str] = Header(None, alias="X-Company-ID")
) -> Dict[str, Any]:
    """
    Decodes the JWT token and validates the company_id from the header.
    Returns the decoded token payload if valid.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate company_id from token against X-Company-ID header
    token_company_id = payload.get("company_id")
    
    if x_company_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Company-ID header is required"
        )
    
    try:
        x_company_id_int = int(x_company_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Company-ID header must be an integer"
        )

    if token_company_id != x_company_id_int:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Company ID in token does not match X-Company-ID header"
        )
    
    return payload

# You can also create a dependency that returns the full user object if needed
# async def get_current_active_user(
#     current_user_payload: Dict[str, Any] = Depends(get_current_user_payload),
#     db: AsyncSession = Depends(get_db)
# ) -> User:
#     user_id = current_user_payload.get("user_id") # Assuming 'user_id' is in payload
#     user = await AuthService.get_user_by_id(db, user_id)
#     if not user:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
#     return user
