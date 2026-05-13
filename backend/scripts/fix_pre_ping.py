import os
import re

backend_dir = r"c:\API\interno\backend"

# Robust pattern to match create_async_engine calls
# Captures the function name and everything inside the parenthesis
pattern = re.compile(r"(create_async_engine\s*\()([^)]+)(\))", re.DOTALL)

for root, _, files in os.walk(backend_dir):
    for file in files:
        if file.endswith(".py"):
            file_path = os.path.join(root, file)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                if "create_async_engine" in content:
                    def replacer(match):
                        prefix = match.group(1) # create_async_engine(args_str = match.group(2, pool_pre_ping=True) # ... args ...
                        suffix = match.group(3) # )
                        
                        # Clean up any existing pool_pre_ping=True (even multiple ones)
                        # We use a greedy regex to remove it and surrounding commas/spaces
                        args_str = re.sub(r",\s*pool_pre_ping\s*=\s*True", "", args_str)
                        args_str = re.sub(r"pool_pre_ping\s*=\s*True\s*,", "", args_str)
                        args_str = re.sub(r"pool_pre_ping\s*=\s*True", "", args_str)
                        
                        args_str = args_str.strip()
                        
                        # Now insert it as the second argument if there are multiple, or just after the first
                        if "," in args_str:
                            parts = args_str.split(",", 1)
                            url_part = parts[0].strip()
                            rest_part = parts[1].strip()
                            return f"{prefix}{url_part}, pool_pre_ping=True, {rest_part}{suffix}"
                        else:
                            url_part = args_str.strip()
                            if url_part:
                                return f"{prefix}{url_part}, pool_pre_ping=True{suffix}"
                            else:
                                return match.group(0) # Shouldn't happen for valid calls
                    
                    new_content = pattern.sub(replacer, content)
                    
                    if new_content != content:
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        print(f"Fixed: {file_path}")
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
