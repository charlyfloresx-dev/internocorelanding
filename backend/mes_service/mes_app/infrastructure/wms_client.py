import httpx
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("mes.wms_client")

class WMSClient:
    """
    Cliente asíncrono para interactuar con el microservicio WMS.
    Aplica la Política 'No-Stop': Información sin bloqueo.
    """
    
    def __init__(self, base_url: str = "http://wms-service:8000"):
        self.base_url = base_url

    async def check_stock(self, sku: str, company_id: str) -> Dict[str, Any]:
        """
        Consulta el stock disponible para un SKU.
        Retorna un dict con la disponibilidad.
        """
        # En un entorno real, esto llamaría al API del WMS
        # Por ahora, simulamos una respuesta positiva o negativa según el SKU
        logger.info(f"Checking WMS stock for SKU: {sku}")
        
        # Simulación: Si el SKU termina en 'ERR', no hay stock
        has_stock = not sku.endswith("ERR")
        
        return {
            "sku": sku,
            "available_qty": 100.0 if has_stock else 0.0,
            "has_stock": has_stock,
            "warning": None if has_stock else f"WMS WARNING: SKU {sku} is out of stock in WMS. Production allowed by No-Stop Policy."
        }
