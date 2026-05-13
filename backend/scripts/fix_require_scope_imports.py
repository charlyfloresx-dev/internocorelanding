import os
import re

dir_path = r'c:\API\interno\backend\master_data_service\master_app\api\v1\endpoints'
import_line = "from common.security.dependencies import require_scope\n"

files_fixed = []

for filename in os.listdir(dir_path):
    if filename.endswith('.py'):
        filepath = os.path.join(dir_path, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'Security(require_scope' in content and 'from common.security.dependencies import require_scope' not in content:
                # Find the best place to insert the import
                if 'from common.security.limiter import limiter' in content:
                    new_content = content.replace('from common.security.limiter import limiter', 
                                                'from common.security.dependencies import require_scope\nfrom common.security.limiter import limiter')
                elif 'from common.responses import ApiResponse' in content:
                     new_content = content.replace('from common.responses import ApiResponse', 
                                                'from common.security.dependencies import require_scope\nfrom common.responses import ApiResponse')
                elif 'from common.domain import' in content:
                     new_content = content.replace('from common.domain import', 
                                                'from common.security.dependencies import require_scope\nfrom common.domain import')
                else:
                    # Fallback: insert after the first 'from fastapi' import
                    match = re.search(r'(from fastapi import .*)\n', content)
                    if match:
                        new_content = content[:match.end()] + import_line + content[match.end():]
                    else:
                        new_content = import_line + content
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                files_fixed.append(filename)
        except Exception as e:
            print(f"Error processing {filename}: {e}")

if files_fixed:
    print(f"Fixed imports in: {', '.join(files_fixed)}")
else:
    print("No files needed fixing.")
