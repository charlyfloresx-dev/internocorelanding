# This import is crucial to fix the NameError: name 'List' is not defined
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from uuid import UUID

from app.models.product import Product, ProductVersion
from app.schemas.product import ProductCreate
from common.exceptions import BusinessRuleException, NotFoundException
# from common.messaging import EventPublisher
from common.enums import ProductStatus, VersionStatus

class ProductService:
    def __init__(self, db: AsyncSession):
        self.db = db
        # self.publisher = EventPublisher()
    
    async def get_products_by_company(self, company_id: UUID) -> List[Product]:
        """ Recupera todos los productos de la empresa actual. """
        stmt = select(Product).where(Product.company_id == company_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_product_by_id(self, product_id: UUID, company_id: UUID) -> Product:
        """ Obtiene un producto específico validando el tenant. """
        stmt = select(Product).where(
            Product.id == product_id, 
            Product.company_id == company_id
        )
        result = await self.db.execute(stmt)
        product = result.scalar_one_or_none()
        
        if not product:
            raise NotFoundException("Producto no encontrado")
        return product

    async def create_product(self, data: ProductCreate, company_id: UUID) -> Product:
        """
        Crea un producto y su versión inicial de forma atómica.
        """
        try:
            async with self.db.begin():
                # 1. Crear Producto Base
                new_product = Product(
                    company_id=company_id,
                    sku=data.sku,
                    name=data.name,
                    description=data.description,
                    product_type=data.product_type,
                    category_id=data.category_id,
                    status=ProductStatus.DRAFT
                )
                self.db.add(new_product)
                await self.db.flush() # Obtener ID para la versión

                # 2. Crear Versión Inicial
                initial_ver = ProductVersion(
                    company_id=company_id,
                    product_id=new_product.id,
                    version_number=data.initial_version.version_number,
                    weight=data.initial_version.weight,
                    dimensions=data.initial_version.dimensions,
                    technical_specs=data.initial_version.technical_specs,
                    um_id=data.initial_version.um_id,
                    version_status=VersionStatus.DESIGN,
                    is_active=True # La primera es activa por defecto en diseño
                )
                self.db.add(initial_ver)
            
            await self.db.refresh(new_product)
            
            # 3. Publicar Evento
            # await self.publisher.publish("master_data.product.created", {
            #     "product_id": str(new_product.id),
            #     "sku": new_product.sku,
            #     "company_id": str(company_id)
            # })
            
            return new_product

        except IntegrityError as e:
            if "sku" in str(e.orig):
                raise BusinessRuleException(f"El SKU '{data.sku}' ya existe en esta compañía.")
            raise e

    async def approve_version(self, product_id: UUID, version_number: int, company_id: UUID):
        """
        Aprueba una versión para producción.
        Regla: Solo una versión activa (PRODUCTION) a la vez.
        """
        # 1. Buscar la versión
        stmt = select(ProductVersion).where(
            ProductVersion.product_id == product_id,
            ProductVersion.version_number == version_number,
            ProductVersion.company_id == company_id
        )
        result = await self.db.execute(stmt)
        version = result.scalar_one_or_none()
        
        if not version:
            raise NotFoundException("Versión de producto no encontrada.")

        # 2. Desactivar otras versiones si esta pasa a Producción
        # (Opcional: Depende de si permitimos múltiples activas, aquí asumimos Single Active Version)
        await self.db.execute(
            update(ProductVersion)
            .where(ProductVersion.product_id == product_id, ProductVersion.company_id == company_id)
            .values(is_active=False)
        )

        # 3. Activar y Aprobar esta versión
        version.version_status = VersionStatus.PRODUCTION
        version.is_active = True
        version.is_validated = True
        
        await self.db.commit()
        return version