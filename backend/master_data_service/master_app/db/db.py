from master_app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from common.models import Base

engine = create_async_engine(settings.ASYNC_DATABASE_URL, pool_pre_ping=True)
async_session = async_sessionmaker(engine, pool_pre_ping=True, expire_on_commit=False)

# Import all models here so that Base has them registered and Alembic can detect them.
# The original error was caused by an incorrect import from 'um' instead of 'uom'.
from master_app.models.uom import UOM
from master_app.models.product_category import ProductCategory
from master_app.models.product_brand import ProductBrand
from master_app.models.product import Product, ProductVersion
