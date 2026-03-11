import uuid
from typing import List, Optional, Any
from uuid import UUID

from app.domain.repositories.master_data_repository import IMasterDataRepository
from app.schemas.product import ProductCreate
from common.exceptions import BusinessRuleException, NotFoundException
from common.domain import ProductStatus, VersionStatus
from common.context import request_context


class ProductService:
    def __init__(self, repo: IMasterDataRepository):
        self.repo = repo

    async def get_products_by_company(self, company_id: UUID, group_id: Optional[UUID] = None) -> List[Any]:
        """Recupera todos los productos de la empresa actual."""
        return await self.repo.get_products(company_id, group_id)

    async def get_product_by_id(self, product_id: Any, company_id: Any) -> Any:
        """Obtiene un producto especifico validando el tenant."""
        p_id = uuid.UUID(str(product_id)) if not isinstance(product_id, uuid.UUID) else product_id
        c_id = uuid.UUID(str(company_id)) if not isinstance(company_id, uuid.UUID) else company_id

        product = await self.repo.get_product_by_id(p_id, c_id)
        if not product:
            raise NotFoundException("Producto no encontrado")
        return product

    async def create_product(self, product_in: ProductCreate) -> Any:
        """Crea un producto y su version inicial de forma atomica."""
        user_ctx = request_context.get()
        if not user_ctx or not user_ctx.company_id or not user_ctx.user_id:
            raise BusinessRuleException("Contexto de usuario o empresa no encontrado.")

        company_id = user_ctx.company_id
        user_id = user_ctx.user_id

        product_data = {
            "company_id": company_id,
            "group_id": product_in.group_id or getattr(user_ctx, 'group_id', None),
            "sku": product_in.sku,
            "name": product_in.name,
            "description": product_in.description,
            "product_type": product_in.product_type,
            "category_id": product_in.category_id,
            "status": ProductStatus.DRAFT,
            "created_by": user_id,
            "updated_by": user_id,
        }
        version_data = {
            "company_id": company_id,
            "version_number": 1,
            "um_id": product_in.uom_id,
            "version_status": VersionStatus.DESIGN,
            "is_active": True,
            "created_by": user_id,
            "updated_by": user_id,
        }
        return await self.repo.create_product(product_data, version_data)

    async def approve_version(self, product_id: UUID, version_number: int, company_id: UUID) -> Any:
        """Aprueba una version para produccion."""
        version = await self.repo.approve_version(product_id, version_number, company_id)
        if not version:
            raise NotFoundException("Version de producto no encontrada.")
        return version