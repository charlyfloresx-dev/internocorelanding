from common.config import settings
print(f"CORE_DATABASE_URL: {settings.int_database_url}")
print(f"DATABASE_URL Property: {settings.DATABASE_URL}")
print(f"ENV_MODE: {settings.int_environment}")
print(f"STRIPE_PRODUCT_ID: {settings.stripe.int_stripe_product_id}")
