import asyncio
import sys
import os

# Add backend and notification_service to sys.path
sys.path.append(os.path.abspath("c:/API/interno/backend"))
sys.path.append(os.path.abspath("c:/API/interno/backend/notification_service"))

from common.config import settings
from app.services.providers.email_resend import ResendEmailProvider
from app.services.template_service import TemplateService

async def test_resend():
    # Set the API key for testing if not set in .env
    if not settings.RESEND_API_KEY:
        settings.int_resend_api_key = "re_6AVNku7R_LgZSQa4JcmVqcAr8y1QfLD4C"
    
    print(f"Testing Resend with key: {settings.RESEND_API_KEY[:5]}...")
    
    template_service = TemplateService()
    provider = ResendEmailProvider()
    
    # Render message using the new TemplateService
    raw_message = "Este es un mensaje de prueba con el nuevo sistema de plantillas e imagen incrustada (Logo SVG Base64)."
    company_id = "00000000-0000-0000-0000-000000000001"
    
    html_content = template_service.render_notification(
        content=raw_message,
        company_id=company_id
    )
    
    success = await provider.send(
        recipient="charly.flores.x@gmail.com", # Updated recipient
        title="Interno Core - Prueba de Template con Logo",
        message=html_content,
        metadata={"company_id": company_id}
    )
    
    if success:
        print("✅ Resend test successful!")
    else:
        print("❌ Resend test failed.")

if __name__ == "__main__":
    asyncio.run(test_resend())
