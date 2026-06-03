import uuid
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from wms_app.models.product_price import ProductPrice, PriceType
from common.repository import BaseRepository

class ProductPriceRepository(BaseRepository[ProductPrice]):
    def __init__(self, db: AsyncSession):
        super().__init__(ProductPrice, db)

    async def get_effective_price(
        self, 
        product_id: uuid.UUID, 
        company_id: uuid.UUID,
        warehouse_id: Optional[uuid.UUID] = None,
        channel_code: Optional[str] = None,
        customer_id: Optional[uuid.UUID] = None
    ) -> Optional[ProductPrice]:
        """
        Implementa la lógica de descubrimiento de precios jerárquica de Interno Core:
        Precedencia:
        1. Contrato/Cliente específico.
        2. Canal específico.
        3. Almacén/Zona específica.
        4. Precio General (Lista).
        
        Todos filtrados por vigencia (start_date <= now <= end_date o end_date IS NULL).
        """
        now = datetime.now(timezone.utc)
        
        # Filtros base comunes
        base_filters = [
            ProductPrice.product_id == product_id,
            ProductPrice.company_id == company_id,
            ProductPrice.is_active == True,
            ProductPrice.start_date <= now,
            or_(ProductPrice.end_date == None, ProductPrice.end_date >= now)
        ]

        # Intentamos en orden de precedencia
        discovery_steps = []
        
        # 1. Contrato
        if customer_id:
            discovery_steps.append(and_(*base_filters, ProductPrice.customer_id == customer_id))
        
        # 2. Canal
        if channel_code:
            discovery_steps.append(and_(*base_filters, ProductPrice.channel_code == channel_code))
            
        # 3. Almacén
        if warehouse_id:
            discovery_steps.append(and_(*base_filters, ProductPrice.warehouse_id == warehouse_id))
            
        # 4. General (fallback)
        discovery_steps.append(and_(*base_filters, ProductPrice.warehouse_id == None, ProductPrice.channel_code == None, ProductPrice.customer_id == None))

        for condition in discovery_steps:
            stmt = select(ProductPrice).where(condition).order_by(ProductPrice.effective_date.desc()).limit(1)
            result = await self.db.execute(stmt)
            price = result.scalar_one_or_none()
            if price:
                return price

        return None

    async def upsert_with_audit(self, new_price: ProductPrice) -> ProductPrice:
        """
        Inserta un nuevo precio aplicando la regla de auditoría "Append-Only" por corte de vigencia.
        """
        now = datetime.now(timezone.utc)
        from datetime import timedelta
        
        # 1. Buscar colisión (Mismo contexto jerárquico que esté activo)
        stmt = select(ProductPrice).where(
            ProductPrice.product_id == new_price.product_id,
            ProductPrice.price_type == new_price.price_type,
            ProductPrice.company_id == new_price.company_id,
            ProductPrice.warehouse_id == new_price.warehouse_id,
            ProductPrice.channel_code == new_price.channel_code,
            ProductPrice.customer_id == new_price.customer_id,
            or_(ProductPrice.end_date == None, ProductPrice.end_date > now)
        ).with_for_update()
        
        result = await self.db.execute(stmt)
        active_price = result.scalar_one_or_none()
        
        next_version = 1
        
        if active_price:
            # 2. Cierre de Ventana (Desactivación por Superposición)
            active_price.end_date = now - timedelta(microseconds=1)
            next_version = active_price.version + 1
            self.db.add(active_price)
            
        # 3. Inserción Limpia
        new_price.start_date = now
        new_price.version = next_version
        self.db.add(new_price)
        
        await self.db.flush()
        return new_price
