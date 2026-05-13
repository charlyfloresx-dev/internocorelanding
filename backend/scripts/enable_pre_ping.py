import os
import re

backend_dir = r"c:\API\interno\backend"

pattern = re.compile(r"create_async_engine\(\s*([^p])")
replacement = r"create_async_engine(\1"

updated_count = 0

for root, pool_pre_ping=True, _, files in os.walk(backend_dir):
    for file in files:
        if file.endswith(".py") and ("alembic" not in root and "tests" not in root and "scripts" not in root):
            file_path = os.path.join(root, file)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if "create_async_engine(" in content and "" not in content:
                new_content = pattern.sub(replacement, pool_pre_ping=True, content)
                
                # Check for create_async_engine(DATABASE_URL, pool_pre_ping=True) and create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
                # It might have matched or not. Let's do a simpler replacement
                
                # A safer replacement approach:
                # Replace 'create_async_engine(' with 'create_async_engine( ' 
                # but only if it's not already there.
                
                if new_content != content:
                    with open(file_path, pool_pre_ping=True, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    print(f"Updated {file_path}")
                    updated_count += 1

print(f"Total files updated: {updated_count}")
