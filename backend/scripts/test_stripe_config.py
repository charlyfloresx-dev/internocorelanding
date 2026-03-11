import os
import sys

# Ajuste de PYTHONPATH para encontrar 'common'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from common.config import settings

def test_stripe_config():
    print("🔍 Verificando Configuración de Stripe...")
    
    # Verificar que el objeto existe
    if not hasattr(settings, "stripe"):
        print("❌ ERROR: El objeto 'stripe' no existe en settings.")
        return

    # Verificar llaves (sin imprimirlas completas por seguridad)
    pub_key = settings.stripe.int_stripe_public_key
    sec_key = settings.stripe.int_stripe_secret_key
    webhook = settings.stripe.int_stripe_webhook_secret
    product = settings.stripe.int_stripe_product_id

    if pub_key:
        print(f"✅ Public Key: Cargada ({pub_key[:10]}...)")
    else:
        print("❌ Public Key: NO CARGADA")

    if sec_key:
        print(f"✅ Secret Key: Cargada (****{sec_key[-4:]})")
    else:
        print("❌ Secret Key: NO CARGADA")

    if webhook:
        print(f"✅ Webhook Secret: Cargado ({webhook[:10]}...)")
    else:
        print("❌ Webhook Secret: NO CARGADA")

    if product:
        print(f"✅ Product ID: {product}")
    else:
        print("❌ Product ID: NO CARGADO")

if __name__ == "__main__":
    test_stripe_config()
