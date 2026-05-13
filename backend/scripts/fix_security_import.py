import os

endpoints_dir = r"c:\API\interno\backend\master_data_service\master_app\api\v1\endpoints"

for file in os.listdir(endpoints_dir):
    if file.endswith(".py"):
        file_path = os.path.join(endpoints_dir, file)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        if "Security(" in content and "from fastapi import" in content and "Security" not in content[:content.find("Security(")]:
            # This is a bit naive, let's just make sure "Security" is in the fastapi import
            if "from fastapi import " in content:
                # Find the first 'from fastapi import ' and add 'Security, '
                lines = content.splitlines()
                for i, line in enumerate(lines):
                    if line.startswith("from fastapi import") and "Security" not in line:
                        lines[i] = line.replace("from fastapi import ", "from fastapi import Security, ")
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write("\n".join(lines) + "\n")
                        print(f"Fixed {file_path}")
                        break
