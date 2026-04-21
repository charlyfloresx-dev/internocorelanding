from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from master_app.db.session import get_db
from master_app.domain.repositories.master_data_repository import IMasterDataRepository
from master_app.infrastructure.repositories.sqlalchemy_master_data_repository import SQLAlchemyMasterDataRepository


def get_master_data_repository(db: AsyncSession = Depends(get_db)) -> IMasterDataRepository:
    """Factory for IMasterDataRepository - resolves the DI graph."""
    return SQLAlchemyMasterDataRepository(db)
