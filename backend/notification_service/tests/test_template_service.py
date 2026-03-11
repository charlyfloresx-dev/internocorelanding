import asyncio
import sys
import os

# Add backend and notification_service to sys.path
sys.path.append(os.path.abspath("c:/API/interno/backend"))
sys.path.append(os.path.abspath("c:/API/interno/backend/notification_service"))

from app.services.template_service import TemplateService

async def test_template():
    service = TemplateService()
    content = "Hello! A new ticket has been created for you. <br> <strong>Ticket ID:</strong> 123"
    company_id = "550e8400-e29b-41d4-a716-446655440000"
    
    html = service.render_notification(content, company_id)
    
    print("--- Rendered HTML ---")
    print(html)
    print("---------------------")
    
    if "<!DOCTYPE html>" in html and "data:image/svg+xml;base64," in html:
        print("✅ Template rendering successful with embedded logo!")
    else:
        print("❌ Template rendering failed or logo mismatch.")

if __name__ == "__main__":
    asyncio.run(test_template())
