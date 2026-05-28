# Master Data Service — Model Registry
# Importar todos los modelos aquí para que Alembic y SQLAlchemy los detecten
# al momento de auto-generar migraciones.

from master_app.models.product import Product, ProductVersion  # noqa: F401
from master_app.models.product_price import ProductPrice, UnitType  # noqa: F401
from master_app.models.product_category import ProductCategory  # noqa: F401
from master_app.models.product_brand import ProductBrand  # noqa: F401
from master_app.models.uom import UOM  # noqa: F401
from master_app.models.uom_conversion import UOMConversion  # noqa: F401
from master_app.models.warehouse import Warehouse  # noqa: F401
from master_app.models.movement_concept import MovementConcept  # noqa: F401
from master_app.models.partner import Partner  # noqa: F401
from master_app.models.price_agreement import PriceAgreement # noqa: F401
from master_app.models.location import InventoryLocation # noqa: F401
from master_app.models.exchange_rate import CurrencyExchangeRate # noqa: F401
from master_app.models.product_scan_pattern import ProductScanPattern  # noqa: F401
