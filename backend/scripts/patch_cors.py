import os
import re

backends = [
    'auth_service', 'currency_service', 'inventory_service', 
    'master_data_service', 'mes_service', 'notification_service', 
    'subscription_service', 'tickets_service', 'wms_service'
]
base = r'C:\API\interno\backend'
headers_to_add = ['X-User-ID', 'x-user-id', 'X-Client-Request-ID', 'x-client-request-id', 'x-company-id', 'x-selection-token']

for b in backends:
    p = os.path.join(base, b, 'app', 'main.py')
    if os.path.exists(p):
        with open(p, 'r', encoding='utf-8') as f:
            content = f.read()
        
        def repl(m):
            inner = m.group(1)
            for h in headers_to_add:
                if f'"{h}"' not in inner and f"'{h}'" not in inner:
                    inner += f', "{h}"'
            return f'allow_headers=[{inner}]'
            
        new_content = re.sub(r'allow_headers=\[([^\]]+)\]', repl, content, flags=re.DOTALL)
        
        # also add allowed hosts if missing (like 8080) for origins, but for now we just add headers
        if new_content != content:
            with open(p, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated {b}")
print("Done")
