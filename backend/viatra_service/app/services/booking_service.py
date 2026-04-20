import uuid
from typing import List, Optional
from app.domain.entities.viatra_entities import TravelPackage, TravelerGroup
from common.value_objects import Money
from common.exceptions import BusinessRuleException, NotFoundException

# Interface definitions should belong to domain/ports
from app.domain.ports.viatra_repositories import IPackageRepository, IGroupRepository
from app.services.stripe_service import StripeService

class BookingService:
    """
    Application Service for managing travel bookings and packages.
    Clean Architecture compliant: No ORM, no Session, No direct commits.
    """
    def __init__(self, package_repo: IPackageRepository, group_repo: IGroupRepository):
        self.package_repo = package_repo
        self.group_repo = group_repo

    async def create_travel_package(
        self, 
        name: str, 
        destination: str, 
        total_price: Money, 
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        description: Optional[str] = None,
        max_capacity: int = 20
    ) -> TravelPackage:
        # Financial Invariant: Price must be greater than zero
        if not total_price or total_price.amount <= 0:
            raise BusinessRuleException("El precio del paquete debe ser mayor que cero.")

        package = TravelPackage(
            id=uuid.uuid4(),
            name=name,
            destination=destination,
            description=description,
            total_price=total_price.amount if hasattr(total_price, 'amount') else total_price,
            max_capacity=max_capacity,
            company_id=company_id
        )

        # Sync to Stripe via service (Should be an interface but for now we call it directly)
        try:
            # Note: StripeService should ideally receive the domain entity
            stripe_price_id = await StripeService.sync_package_to_stripe(package)
            package.stripe_price_id = stripe_price_id
        except Exception as e:
            raise BusinessRuleException(f"Error al sincronizar con Stripe: {str(e)}")

        # Persistence via Repository Interface
        return await self.package_repo.create(package, user_id)

    async def list_packages(self, company_id: uuid.UUID) -> List[TravelPackage]:
        return await self.package_repo.list_all(company_id)

    async def create_traveler_group(
        self, 
        name: str, 
        package_id: uuid.UUID, 
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        leader_name: Optional[str] = None
    ) -> TravelerGroup:
        # Verify package existence via repository interface
        package = await self.package_repo.get_by_id(package_id, company_id)
        if not package:
            raise NotFoundException("El paquete especificado no existe o no pertenece a esta agencia.")

        group = TravelerGroup(
            id=uuid.uuid4(),
            name=name,
            package_id=package_id,
            leader_name=leader_name,
            company_id=company_id
        )

        # Persistence via Repository Interface
        return await self.group_repo.create(group, user_id)
