from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from subscription_app.dependencies import get_db
from subscription_app.domain.repositories.subscription_repository import ISubscriptionRepository
from subscription_app.infrastructure.repositories.sqlalchemy_subscription_repository import SQLAlchemySubscriptionRepository
from subscription_app.infrastructure.interfaces.payment_provider import IPaymentProvider
from subscription_app.infrastructure.providers.stripe_payment_provider import StripePaymentProvider


def get_subscription_repository(db: AsyncSession = Depends(get_db)) -> ISubscriptionRepository:
    return SQLAlchemySubscriptionRepository(db)


def get_payment_provider() -> IPaymentProvider:
    return StripePaymentProvider()
