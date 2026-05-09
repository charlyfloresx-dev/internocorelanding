import os
import json
import re
from typing import List, Dict, Any, Set

class MobileGraphGenerator:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.mobile_root = os.path.join(root_dir, "interno_billing_app")
        self.graph = {
            "nodes": [],
            "edges": [],
            "invariants_errors": [],
            "compliance_report": {}
        }
        self.errors_by_layer = {
            "presentation": 0,
            "domain": 0,
            "data": 0,
            "core": 0,
            "other": 0
        }
        self.scanned_files = 0
        self.total_loc = 0

    def _get_layer(self, rel_path: str) -> str:
        if "presentation" in rel_path: return "presentation"
        if "domain" in rel_path: return "domain"
        if "data" in rel_path: return "data"
        if "core" in rel_path: return "core"
        return "other"

    def scan(self):
        lib_path = os.path.join(self.mobile_root, "lib")
        if not os.path.exists(lib_path):
            print(f"Error: lib directory not found at {lib_path}")
            return

        for root, _, files in os.walk(lib_path):
            for file in files:
                if file.endswith(".dart"):
                    file_path = os.path.join(root, file)
                    self.scanned_files += 1
                    self.analyze_file(file_path)

    def analyze_file(self, file_path: str):
        rel_path = os.path.relpath(file_path, self.mobile_root).replace("\\", "/")
        layer = self._get_layer(rel_path)
        
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                content = f.read()
                lines = content.splitlines()
                self.total_loc += len(lines)
            except Exception: return

        # 1. Hardcoded URL Violation
        if "http://" in content or "https://" in content:
            # Exclude injection.dart as it's the valid place for base URLs
            if "injection.dart" not in rel_path:
                # Match actual URLs in strings
                urls = re.findall(r'https?://[^\s\'"]+', content)
                if urls:
                    self.add_error(rel_path, "CRITICAL", layer, f"HARDCODED_URL_VIOLATION: Direct URL usage detected: {urls[0]}")

        # 2. Theme Violation (Direct Colors usage)
        if "Colors." in content or "Color(0x" in content:
            # Exclude theme/color definitions and the main design system file
            if not any(x in rel_path for x in ["theme.dart", "colors.dart", "app_colors.dart", "injection.dart"]):
                # Simple check for common Material Colors
                material_colors = ["Colors.red", "Colors.blue", "Colors.green", "Colors.black", "Colors.white", "Colors.yellow"]
                for mc in material_colors:
                    if mc in content:
                        self.add_error(rel_path, "WARNING", layer, f"THEME_VIOLATION: Use of Material {mc} detected. Use InternoColors instead.")
                        break

        # 3. Clean Architecture Violation: Blocs importing Dio
        if "_bloc.dart" in rel_path:
            if "import 'package:dio/dio.dart'" in content or "Dio " in content:
                self.add_error(rel_path, "CRITICAL", layer, "CLEAN_ARCH_VIOLATION: BLoC layer should not depend on Dio. Use Repositories.")

        # 4. Localization Check (Simplified)
        if "Text('" in content or 'Text("' in content:
            # Check if strings are translated with .tr() or if they are just raw strings
            # This is a heuristic: search for Text('Something') without .tr()
            suspicious_strings = re.findall(r"Text\(['\"]([^'\"]+)['\"]\)", content)
            for s in suspicious_strings:
                if len(s) > 3 and not s.isupper(): # Ignore icons or short codes
                    # Check if the next part is .tr()
                    # (This regex is limited, but good for a start)
                    if not re.search(f"Text\\(['\"]{re.escape(s)}['\"]\\)\\.tr\\(\\)", content):
                        self.add_error(rel_path, "WARNING", layer, f"MISSING_LOCALIZATION: Raw string '{s}' in Text widget. Use .tr().")

        # 5. Missing Tenant Header in Repositories
        if "_repository.dart" in rel_path and "Repository" in content:
            # Repositories should ideally mention companyId or tenant_id or headers
            if "companyId" not in content and "X-Company-ID" not in content and "token" not in content:
                # Exclude AuthRepository as it might not need tenant yet
                if "auth_repository" not in rel_path:
                    self.add_error(rel_path, "WARNING", layer, "TENANT_AWARENESS_VIOLATION: Repository might be missing company_id / token injection.")

    def add_error(self, file: str, severity: str, layer: str, error: str):
        err = {"file": file, "severity": severity, "layer": layer, "error": error}
        self.graph["invariants_errors"].append(err)
        self.errors_by_layer[layer] += 1

    def print_report(self):
        critical = [e for e in self.graph["invariants_errors"] if e["severity"] == "CRITICAL"]
        warnings = [e for e in self.graph["invariants_errors"] if e["severity"] == "WARNING"]
        
        print("="*80)
        print("  INTERNO POS: Mobile Code Knowledge Graph Audit")
        print(f"  Scanned: {self.scanned_files} files | {self.total_loc} lines of code")
        print("="*80)
        
        if critical:
            print(f"\n[CRITICAL] ERRORS ({len(critical)}):")
            print("-" * 60)
            for e in critical:
                print(f"  [!!] {e['file']} -> {e['error']}")
        
        if warnings:
            print(f"\n[WARNING] ({len(warnings)}):")
            print("-" * 60)
            for i, e in enumerate(warnings, 1):
                print(f"  [{i:02d}] {e['file']} -> {e['error']}")

        print("\n[SUMMARY] Compliance Report by Layer:")
        print("-" * 60)
        for layer, err_count in self.errors_by_layer.items():
            score = max(0, 100 - (err_count * 10))
            status = "CLEAN" if score == 100 else "DEBT"
            print(f"   {layer:20} : {score:3}% Compliance ({err_count} err) | Status: {status}")

        print("\n" + "="*80)
        print(f"  TOTAL ERRORS: {len(self.graph['invariants_errors'])}")
        print("="*80)

    def save(self, output_ptr: str):
        self.graph["compliance_report"] = {l: max(0, 100 - (c * 10)) for l, c in self.errors_by_layer.items()}
        with open(output_ptr, "w", encoding="utf-8") as f:
            json.dump(self.graph, f, indent=4)

if __name__ == "__main__":
    import sys
    # Find project root (one level up from scripts if it was in a subfolder, 
    # but here we assume we run from the project root)
    root = os.getcwd()
    gen = MobileGraphGenerator(root)
    gen.scan()
    gen.print_report()
    gen.save(os.path.join(root, "mobile_code_graph.json"))
    
    critical_errors = [e for e in gen.graph["invariants_errors"] if e["severity"] == "CRITICAL"]
    if len(critical_errors) > 0:
        # sys.exit(1) # Un-comment to fail CI/CD
        pass
