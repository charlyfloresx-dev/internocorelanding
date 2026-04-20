import os
import re
from pathlib import Path
from collections import defaultdict

def find_env_files(root_dir):
    """Recursively finds all .env files in the given root directory."""
    env_files = []
    for path in Path(root_dir).rglob('.env'):
        env_files.append(str(path))
    return env_files

def parse_env_file(file_path):
    """Parses a .env file and returns a dictionary of key-value pairs."""
    env_vars = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Ignore empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Match key=value pattern
            match = re.match(r'^([^=]+)=(.*)$', line)
            if match:
                key, value = match.groups()
                env_vars[key.strip()] = value.strip()
            else:
                print(f"[WARNING] Invalid format in {file_path}: {line}")
    return env_vars

def validate_envs(root_dir):
    print("=" * 50)
    print("  AWS Secrets Manager - .env Validation Script")
    print("=" * 50)
    
    env_files = find_env_files(root_dir)
    print(f"[*] Found {len(env_files)} .env files.")
    
    global_keys = defaultdict(list)
    has_errors = False
    
    for file_path in env_files:
        print(f"\nScanning: {file_path}")
        env_vars = parse_env_file(file_path)
        
        # Check specific CORE_ duplicate logic or any duplicates across files if needed
        for key, value in env_vars.items():
            global_keys[key].append(file_path)
    
    print("\n" + "=" * 50)
    print("  Duplicate Key Analysis")
    print("=" * 50)
    
    duplicates = {k: v for k, v in global_keys.items() if len(v) > 1}
    
    if not duplicates:
        print("[+] No duplicate environment variables found across files.")
    else:
        print("[!] Found duplicate definitions for the following keys:\n")
        for key, paths in duplicates.items():
            print(f"Key: {key}")
            for p in paths:
                print(f"  - {p}")
            # Highlight as error if it's a critical CORE_ variable that shouldn't be duplicated unnecessarily
            if key.startswith("CORE_"):
                print("  [ACTION REQUIRED] Consider consolidating this CORE_ variable.")
                has_errors = True
            print("-" * 30)

    if has_errors:
        print("\n[CONCLUSION] Validation completed with warnings. Please review duplicates before AWS migration.")
    else:
        print("\n[CONCLUSION] Validation successful. Ready for AWS Secrets Manager migration script!")

if __name__ == "__main__":
    # Assuming script is run from backend/scripts/ or root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    validate_envs(project_root)
