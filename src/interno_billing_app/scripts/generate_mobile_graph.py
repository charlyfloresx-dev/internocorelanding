import os
import json
import re
from typing import List, Dict, Any, Set

class MobileGraphGenerator:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.mobile_root = os.path.join(root_dir, "src", "interno_billing_app")
        self.graph = {
            "nodes": [],
            "edges": [],
            "invariants_errors": [],
            "compliance_report": {}
        }
        self.errors_by_layer = {}
        self.scanned_files = 0
        self.total_loc = 0
        self.scanned_files_log = []

    def _get_layer(self, rel_path: str) -> str:
        if "presentation" in rel_path: return "presentation"
        if "domain" in rel_path: return "domain"
        if "data" in rel_path: return "data"
        if "core" in rel_path: return "core"
        return "other"

    def add_error(self, file: str, severity: str, layer: str, error: str):
        err = {"file": file, "severity": severity, "layer": layer, "error": error}
        self.graph["invariants_errors"].append(err)
        self.errors_by_layer[layer] = self.errors_by_layer.get(layer, 0) + 1

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
        
        # Post-scan analysis (Circular Deps or global invariants)
        self._check_layer_isolation()

    def _check_layer_isolation(self):
        # Placeholder for future isolation logic
        pass

    def analyze_file(self, file_path: str):
        rel_path = os.path.relpath(file_path, self.mobile_root).replace("\\", "/")
        layer = self._get_layer(rel_path)
        self.scanned_files_log.append(f"AUDITED: {rel_path} [{layer}]")
        
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                content = f.read()
                lines = content.splitlines()
                self.total_loc += len(lines)
            except Exception: return

        # --- AUDIT RULES (Sincronizado con Backend Patterns) ---

        # 1. HARDCODED_URL_VIOLATION (AWS Budget/Security Guard)
        if "http://" in content or "https://" in content:
            if "injection.dart" not in rel_path and "resilience_mocks" not in rel_path:
                urls = re.findall(r'https?://[^\s\'"]+', content)
                # Whitelist image CDNs and assets to avoid false positives on UI placeholders
                image_cdns = ["images.unsplash.com", "cdn.pixabay.com", "images.pexels.com"]
                if urls and not any(ext in urls[0] for ext in [".png", ".jpg", ".svg", ".jpeg", ".webp"]):
                    if not any(cdn in urls[0] for cdn in image_cdns):
                        self.add_error(rel_path, "CRITICAL", layer, f"HARDCODED_URL_VIOLATION: Direct API URL usage detected: {urls[0]}")

        # 2. THEME_VIOLATION (Design System Integrity)
        if "Colors." in content and "InternoColors" not in content:
            if not any(x in rel_path for x in ["theme.dart", "colors.dart", "injection.dart"]):
                self.add_error(rel_path, "WARNING", layer, "THEME_VIOLATION: Use of Material Colors instead of InternoColors.")

        # 3. CLEAN_ARCH_VIOLATION (Layer Isolation)
        if "_bloc.dart" in rel_path and "import 'package:dio/dio.dart'" in content:
            self.add_error(rel_path, "CRITICAL", layer, "CLEAN_ARCH_VIOLATION: Presentation layer (BLoC) should not import Dio directly.")

        # 4. SENTINEL_RESILIENCE_INVARIANTS (Phase 102)
        if "injection.dart" in rel_path:
            if "ResilienceInterceptor" not in content:
                self.add_error(rel_path, "CRITICAL", layer, "RESILIENCE_MISSING: ResilienceInterceptor not registered in injection chain.")
            if "ConnectivityService" not in content:
                self.add_error(rel_path, "WARNING", layer, "CONNECTIVITY_SENSOR_MISSING: Hardware sensor not initialized.")

        if "connection_status_provider.dart" in rel_path and "Wakelock" not in content:
            self.add_error(rel_path, "WARNING", layer, "WAKELOCK_MISSING: Sentinel UI does not manage screen lock during recovery.")

    def print_report(self):
        critical = [e for e in self.graph["invariants_errors"] if e["severity"] == "CRITICAL"]
        warnings = [e for e in self.graph["invariants_errors"] if e["severity"] == "WARNING"]
        
        print("="*80)
        print("  INTERNO POS: Mobile Code Knowledge Graph Audit (Sync-Docs Mode)")
        print(f"  Scanned: {self.scanned_files} files | {self.total_loc} LOC")
        print("="*80)
        
        if critical:
            print(f"\n[CRITICAL] ERRORS ({len(critical)}):")
            print("-" * 60)
            for e in critical:
                print(f"  [!!] {e['file']:40} -> {e['error']}")

        if warnings:
            print(f"\n[WARNING] ({len(warnings)}):")
            print("-" * 60)
            for i, e in enumerate(warnings, 1):
                print(f"  [{i:02d}] {e['file']:40} -> {e['error']}")
        
        print("\n[SUMMARY] Compliance Report by Layer:")
        print("-" * 60)
        for layer in ["presentation", "domain", "data", "core"]:
            err_count = self.errors_by_layer.get(layer, 0)
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
        
        # Write execution log (Backend Synchronization)
        log_ptr = output_ptr.replace(".json", "_execution_log.txt")
        with open(log_ptr, "w", encoding="utf-8") as f:
            f.write("="*80 + "\n")
            f.write(" MOBILE CODE GRAPH AUDITOR - EXECUTION LOG\n")
            f.write("="*80 + "\n\n")
            f.write("\n".join(sorted(self.scanned_files_log)))

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
