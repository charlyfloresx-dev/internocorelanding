import uuid
from typing import Annotated
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError
from pydantic import ValidationError

from common.config import settings

from app.db.session import get_db
from app.infrastructure.repositories.sqlalchemy_master_data_repository import SQLAlchemyMasterDataRepository
from app.services.product_service import ProductService
from app.services.product_brand_service import ProductBrandService
from app.services.product_category_service import ProductCategoryService
from app.services.uom_service import UOMService
from app.services.currency_service import CurrencyService
from app.infrastructure.repositories.sqlalchemy_currency_repository import SQLAlchemyCurrencyRepository
from app.infrastructure.clients.currency_client import DummyCurrencyClient
from common.domain.entities.user_context import UserContext
from common.context import request_context

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="http://localhost:8001/api/v1/auth/login"
)

async def get_current_user_payload(request: Request, token: Annotated[str, Depends(oauth2_scheme)] = None) -> UserContext:
    if not token:
        # Fallback to header token parsing if somehow OAuth2PasswordBearer fails but header is there
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id = payload.get("sub", "00000000-0000-0000-0000-000000000000")
        company_id = payload.get("company_id")
        
        # Verify X-Company-Id matches token if provided
        header_company_id = request.headers.get("X-Company-ID")
        if header_company_id and header_company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant context mismatch"
            )

        user_context = UserContext(
            user_id=user_id, 
            company_id=uuid.UUID(str(company_id)),
            group_id=uuid.UUID(str(payload.get("group_id"))) if payload.get("group_id") else None,
            role_names=payload.get("role_names", []),
            token=token
        )
        request_context.set(user_context)
        return user_context

    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales invalidas o token expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

get_current_user = get_current_user_payload

# Repository Dependency
async def get_master_data_repository(db: AsyncSession = Depends(get_db)) -> SQLAlchemyMasterDataRepository:
    return SQLAlchemyMasterDataRepository(db)

# Service Dependencies
async def get_product_service(repo: SQLAlchemyMasterDataRepository = Depends(get_master_data_repository)) -> ProductService:
    return ProductService(repo)

async def get_brand_service(repo: SQLAlchemyMasterDataRepository = Depends(get_master_data_repository)) -> ProductBrandService:
    return ProductBrandService(repo)

async def get_category_service(repo: SQLAlchemyMasterDataRepository = Depends(get_master_data_repository)) -> ProductCategoryService:
    return ProductCategoryService(repo)

async def get_uom_service(repo: SQLAlchemyMasterDataRepository = Depends(get_master_data_repository)) -> UOMService:
    return UOMService(repo)

async def get_currency_repository(db: AsyncSession = Depends(get_db)) -> SQLAlchemyCurrencyRepository:
    return SQLAlchemyCurrencyRepository(db)

from app.infrastructure.clients.currency_client import ExternalCurrencyClient

async def get_currency_service(repo: SQLAlchemyCurrencyRepository = Depends(get_currency_repository)) -> CurrencyService:
    client = ExternalCurrencyClient()
    return CurrencyService(repository=repo, client=client)
