from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import os
import logging
import base64

logger = logging.getLogger("notification.template_service")

class TemplateService:
    def __init__(self):
        # Path relative to this file: ../templates
        template_path = os.path.join(os.path.dirname(__file__), "../templates")
        if not os.path.exists(template_path):
            os.makedirs(template_path)
            logger.warning(f"Template path {template_path} did not exist and was created.")
            
        self.env = Environment(loader=FileSystemLoader(template_path))

    def _get_logo_data_uri(self):
        """
        Reads the local InternoCoreSVGBlack.svg and returns it as a Base64 data URI.
        """
        try:
            # Requisito 10.6: Usar InternoCoreSVGBlack.svg
            logo_path = os.path.join(os.path.dirname(__file__), "../templates/InternoCoreSVGBlack.svg")
            if os.path.exists(logo_path):
                with open(logo_path, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode("utf-8")
                    return f"data:image/svg+xml;base64,{encoded}"
            else:
                logger.warning(f"Logo not found at {logo_path}")
        except Exception as e:
            logger.error(f"Error reading logo.svg: {str(e)}")
        return "https://cdn.internocore.com/logos/default.png"

    def render_subscription_success(self, data: dict):
        """
        Renders the specialized subscription success template.
        Expected data: {user_name, company_name, plan_name, expiry_date}
        """
        logo_url = self._get_logo_data_uri()
        privacy_url = "https://internocore.com/privacy" 
        
        try:
            template = self.env.get_template("subscription_success.html")
            return template.render(
                logo_url=logo_url,
                privacy_policy_url=privacy_url,
                year=datetime.now().year,
                **data
            )
        except Exception as e:
            logger.error(f"Error rendering subscription_success template: {str(e)}")
            return f"<html><body><h2>¡Bienvenido!</h2><p>Tu suscripción para {data.get('company_name')} ha sido activada.</p></body></html>"

    def render_notification(self, content: str, company_id: str):
        """
        Combines the base layout with the specific content and company branding.
        """
        # Multi-tenant logic: logo and privacy dynamic by company_id
        # In a real scenario, this would fetch from a Cache or Database
        # Fallback to local logo if no specific URL is found (simulated)
        logo_url = self._get_logo_data_uri()
        privacy_url = "https://internocore.com/privacy" 

        try:
            template = self.env.get_template("base_layout.html")
            
            return template.render(
                logo_url=logo_url,
                content=content,
                privacy_policy_url=privacy_url,
                year=datetime.now().year
            )
        except Exception as e:
            logger.error(f"Error rendering template: {str(e)}")
            # Fallback to simple content if template fails
            return f"<html><body>{content}</body></html>"
