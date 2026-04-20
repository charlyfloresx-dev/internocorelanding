import os
import re

backends = [
    'auth_service', 'currency_service', 'inventory_service', 
    'master_data_service', 'mes_service', 'notification_service', 
    'subscription_service', 'tickets_service', 'wms_service'
]
base = r'C:/API/interno/backend'

for b in backends:
    p = os.path.join(base, b, 'app', 'main.py')
    if os.path.exists(p):
        with open(p, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 1. Ensure setup_cors is imported
        if 'setup_cors' not in content:
            # Add at the top if missing
            content = "from common.security.cors_setup import setup_cors\n" + content
            
        # 2. Find and replace CORSMiddleware blocks
        # This matches CORSMiddleware added via app.add_middleware
        # and removes the manual configuration and the CORS_ORIGINS variable
        
        # Pattern for the middleware addition
        pattern_mid = r'app\.add_middleware\(\s*CORSMiddleware,[\s\S]+?\)'
        new_content = re.sub(pattern_mid, 'setup_cors(app)', content)
        
        # Pattern for CORS_ORIGINS list
        pattern_origins = r'CORS_ORIGINS\s*=\s*\[[\s\S]+?\]'
        new_content = re.sub(pattern_origins, '', new_content)

        if new_content != content:
            with open(p, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✅ Microservice {b} migrated to Centralized CORS.")

print("Done.")
