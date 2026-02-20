import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL)
Base = declarative_base()

# Import all models here so that Base has them registered and Alembic can detect them.
# The original error was caused by an incorrect import from 'um' instead of 'uom'.
from app.models.uom import UOM
from app.models.product_category import ProductCategory
from app.models.product_brand import ProductBrand