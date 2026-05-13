import os
import re

path = r'c:\API\interno\backend\master_data_service\master_app\api\v1\endpoints'
files = [os.path.join(path, f) for f in os.listdir(path) if f.endswith('.py')]
for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
        
    if 'require_scope' not in content and 'get_current_user' in content:
        content = re.sub(r'from common.security.dependencies import (.*)', r'from common.security.dependencies import \1, require_scope\nfrom fastapi import Security', content, count=1)
    
    lines = content.split('\n')
    out = []
    method = 'read'
    for line in lines:
        if '@router.get' in line: method = 'read'
        elif any(x in line for x in ['@router.post', '@router.put', '@router.delete', '@router.patch']): method = 'write'
        if 'Depends(get_current_user)' in line:
            line = line.replace('Depends(get_current_user)', f'Security(require_scope, scopes=["master_data:{method}"])')
        out.append(line)
        
    with open(f, 'w', encoding='utf-8') as file:
        file.write('\n'.join(out))
print("Fix scopes applied successfully!")
