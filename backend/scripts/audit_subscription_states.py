import unittest
import requests
import uuid
import json
import time
from jose import jwt
from datetime import datetime, timedelta

import os

# Configuración del Entorno - Cargando de variables de entorno para cumplimiento Industrial
BASE_URL = os.getenv("AUDIT_TARGET_URL", "http://localhost:8006")
SECRET_KEY = os.getenv("CORE_SECRET_KEY", "DEV_SECRET_KEY_CAMBIAME_EN_PROD_12345")
ALGORITHM = "HS256"
COMPANY_ID = os.getenv("AUDIT_COMPANY_ID", "00000000-0000-0000-0000-000000000000")

class SubscriptionAuditTest(unittest.TestCase):
    """
    Suite de Auditor\u00eda Automatizada para Fase 19: Grace Period y Degradaci\u00f3n.
    Verifica que el middleware global bloquee seg\u00fan el estatus de suscripci\u00f3n.
    """

    def create_token(self, status: str, readonly: bool = False):
        payload = {
            "sub": "audit-user",
            "status": status,
            "readonly": readonly,
            "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp(),
            "company_id": self.company_id
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    def setUp(self):
        self.company_id = str(uuid.uuid4())
        self.headers = {
            "X-Company-ID": self.company_id,
            "Content-Type": "application/json"
        }

    def test_01_active_access(self):
        """Verifica que una suscripción ACTIVE tenga acceso total."""
        token = self.create_token("ACTIVE")
        headers = {**self.headers, "Authorization": f"Bearer {token}"}
        
        # Valid path in inventory service
        dummy_id = str(uuid.uuid4())
        response = requests.get(f"{BASE_URL}/api/v1/inventory/stock/{dummy_id}/{dummy_id}", headers=headers)
        self.assertNotEqual(response.status_code, 402, "ACTIVE subscription should not be blocked with 402")

    def test_02_past_due_access(self):
        """Verifica que una suscripción PAST_DUE (Día 1-3) tenga acceso total."""
        token = self.create_token("PAST_DUE")
        headers = {**self.headers, "Authorization": f"Bearer {token}"}
        
        payload = {"quantity": 10, "product_id": str(uuid.uuid4()), "warehouse_id": str(uuid.uuid4()), "type": "IN"}
        response = requests.post(f"{BASE_URL}/api/v1/inventory/movements", headers=headers, json=payload)
        self.assertNotEqual(response.status_code, 402, "PAST_DUE should allow POST in the first 3 days")

    def test_03_restricted_read_only(self):
        """
        Verifica que una suscripción RESTRICTED (o readonly=True):
        - Permita GET.
        - Bloquee POST/DELETE con 402.
        """
        token = self.create_token("RESTRICTED")
        headers = {**self.headers, "Authorization": f"Bearer {token}"}

        # 1. Probar GET (Permitido)
        dummy_id = str(uuid.uuid4())
        response_get = requests.get(f"{BASE_URL}/api/v1/inventory/stock/{dummy_id}/{dummy_id}", headers=headers)
        self.assertNotEqual(response_get.status_code, 402, "RESTRICTED should allow GET for audit")

        # 2. Probar POST (Bloqueado con 402)
        payload = {"quantity": 1, "product_id": dummy_id, "warehouse_id": dummy_id, "type": "IN"}
        response_post = requests.post(f"{BASE_URL}/api/v1/inventory/movements", headers=headers, json=payload)
        
        self.assertEqual(response_post.status_code, 402, "RESTRICTED must block POST with 402 Payment Required")
        data = response_post.json()
        self.assertIn("Subscription Restricted", data["message"])

    def test_04_unpaid_total_block(self):
        """Verifica que una suscripción UNPAID bloquee incluso los GET."""
        token = self.create_token("UNPAID")
        headers = {**self.headers, "Authorization": f"Bearer {token}"}
        
        dummy_id = str(uuid.uuid4())
        response = requests.get(f"{BASE_URL}/api/v1/inventory/stock/{dummy_id}/{dummy_id}", headers=headers)
        self.assertEqual(response.status_code, 402, "UNPAID must block ALL requests including GET")
        data = response.json()
        self.assertIn("Subscription Unpaid", data["message"])

    def test_05_billing_exception(self):
        """Verifica que las rutas de /api/v1/billing sean accesibles incluso en UNPAID."""
        token = self.create_token("UNPAID")
        headers = {**self.headers, "Authorization": f"Bearer {token}"}
        # Hitting port 8002 for subscription service billing routes
        BILLING_URL = "http://localhost:8002/api/v1/billing/webhook"
        response = requests.post(BILLING_URL, headers=headers)
        # 400 is fine (missing signature), but not 402.
        self.assertNotEqual(response.status_code, 402, "Billing routes should be exempt from 402 lockdowns")

if __name__ == "__main__":
    print("--- INICIANDO AUDITORIA DE ESTADOS DE SUSCRIPCION (FASE 19) ---")
    unittest.main()
