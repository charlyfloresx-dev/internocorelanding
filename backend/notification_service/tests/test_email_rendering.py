import sys
import os

# Add notification_service to path
sys.path.append(os.path.join(os.getcwd(), "backend/notification_service"))

from app.services.template_service import TemplateService

def test_rendering():
    service = TemplateService()
    data = {
        "user_name": "Charly Flores",
        "company_name": "Demo Logistics",
        "plan_name": "Pro Plan",
        "expiry_date": "06/04/2026"
    }
    
    print("Testing render_subscription_success...")
    html = service.render_subscription_success(data)
    
    # Check for keywords
    assert "Charly Flores" in html
    assert "Demo Logistics" in html
    assert "Pro Plan" in html
    assert "data:image/svg+xml;base64," in html
    
    output_file = "test_email_output.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"✅ Rendering success! Output saved to {output_file}")

if __name__ == "__main__":
    test_rendering()
