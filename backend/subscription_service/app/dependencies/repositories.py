from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
from app.domain.repositories.subscription_repository import ISubscriptionRepository
from app.infrastructure.repositories.sqlalchemy_subscription_repository import SQLAlchemySubscriptionRepository
from app.infrastructure.interfaces.payment_provider import IPaymentProvider
from app.infrastructure.providers.stripe_payment_provider import StripePaymentProvider


def get_subscription_repository(db: AsyncSession = Depends(get_db)) -> ISubscriptionRepository:
    return SQLAlchemySubscriptionRepository(db)


def get_payment_provider() -> IPaymentProvider:
    return StripePaymentProvider()
