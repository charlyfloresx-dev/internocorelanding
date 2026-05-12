import os
import ast
import json
import re
from typing import List, Dict, Any, Set

class CodeGraphGenerator:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.graph = {
            "nodes": [],
            "edges": [],
            "invariants_errors": [],
            "compliance_report": {},
            "inter_service_deps": {}
        }
        self.nodes_by_id = {}
        self.lines_of_code = {}
        self.errors_by_ms = {}
        self.inter_service_dependencies = {} # {microservice: set(target_services)}
        self.domain_services_count = {} # {microservice: count}
        # Microservices to track for report
        self.ms_scanned_files = {} # {microservice: count}
        self.MICROSERVICES = self._discover_microservices()

    def _discover_microservices(self) -> List[str]:
        """Auto-detect microservices based on backend directory structure."""
        backend_path = os.path.join(self.root_dir, "backend")
        if not os.path.exists(backend_path):
            return ["common"]
        
        services = ["common"] # Always track common
        exclude = ["scripts", "tests", "archive", "tmp", "docs", ".pytest_cache", "__pycache__", "backend"]
        
        for item in os.listdir(backend_path):
            item_path = os.path.join(backend_path, item)
            if os.path.isdir(item_path) and item not in exclude:
                # A directory is a microservice if it has an 'app' folder or 'requirements.txt'
                if os.path.exists(os.path.join(item_path, "app")) or os.path.exists(os.path.join(item_path, "requirements.txt")):
                    services.append(item)
        return sorted(list(set(services)))

    def get_node_id(self, file_path: str, class_name: str) -> str:
        rel_path = os.path.relpath(file_path, self.root_dir)
        return f"{rel_path}:{class_name}"

    def add_node(self, id: str, type: str, metadata: Dict[str, Any]):
        if id not in self.nodes_by_id:
            node = {"id": id, "type": type, "metadata": metadata}
            self.graph["nodes"].append(node)
            self.nodes_by_id[id] = node

    def add_edge(self, source: str, target: str, type: str):
        edge = {"source": source, "target": target, "type": type}
        if edge not in self.graph["edges"]:
            self.graph["edges"].append(edge)

    def _get_ms(self, file_path: str):
        rel = os.path.relpath(file_path, self.root_dir).replace("\\", "/")
        parts = rel.split("/")
        if "backend" in parts:
            idx = parts.index("backend")
            return parts[idx + 1] if len(parts) > idx + 1 else "root"
        return "common"

    def _resolve_imports(self, tree: ast.AST) -> Dict[str, str]:
        imports = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports[alias.asname or alias.name] = alias.name
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports[alias.asname or alias.name] = f"{module}.{alias.name}"
        return imports

    def _check_circular_dependencies(self):
        visited = set()
        stack = []
        path = []

        def has_cycle(u):
            visited.add(u)
            stack.append(u)
            path.append(u)
            for v in self.inter_service_dependencies.get(u, set()):
                if v not in visited:
                    if has_cycle(v): return True
                elif v in stack:
                    cycle_path = " -> ".join(path[path.index(v):] + [v])
                    self.graph["invariants_errors"].append({
                        "file": "MICROSERVICE_ARCHITECTURE",
                        "severity": "CRITICAL",
                        "error": f"CIRCULAR_DEPENDENCY_VIOLATION: detected cycle {cycle_path}"
                    })
                    return True
            stack.pop()
            path.pop()
            return False

        for ms in list(self.inter_service_dependencies.keys()):
            if ms not in visited:
                has_cycle(ms)

    def scan(self):
        for root, _, files in os.walk(self.root_dir):
            root_normalized = root.replace("\\", "/")
            # Strict exclusions for report cleanliness
            if any(x in root_normalized for x in [".git", "venv", "node_modules", "alembic", "__pycache__", "/docs", "/tests", "/archive", "/tmp"]):
                continue
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    ms = self._get_ms(file_path)
                    self.ms_scanned_files[ms] = self.ms_scanned_files.get(ms, 0) + 1
                    self.analyze_file(file_path)
        
        # Post-scan invariants
        self._check_circular_dependencies()
        if "mes_service" in self.lines_of_code and self.domain_services_count.get("mes_service", 0) == 0:
            self.graph["invariants_errors"].append({
                "file": "backend/mes_service/mes_app/domain/",
                "severity": "WARNING",
                "ms": "mes_service",
                "error": "MISSING_DOMAIN_LOGIC_WARNING: mes_service has no complex logic in mes_app/domain/services/"
            })

    def analyze_file(self, file_path: str):
        rel_path = os.path.relpath(file_path, self.root_dir).replace("\\", "/")
        ms = self._get_ms(file_path)
        
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                content = f.read()
                tree = ast.parse(content)
            except Exception: return

        self.lines_of_code[ms] = self.lines_of_code.get(ms, 0) + len(content.splitlines())
        imports = self._resolve_imports(tree)

        filename = os.path.basename(file_path)

        # Definitions for filters
        is_config = filename.endswith("config.py") and "logging_config" not in filename
        is_test = filename.startswith("test_") or "/tests/" in rel_path or "/scripts/" in rel_path

        # 1. ENV Violation (Ignore config files and core folder as they are the source of truth)
        if "/app/core/" not in rel_path and not is_config and "setup.py" not in rel_path and "seed" not in rel_path and not is_test:
            if "os.getenv(" in content or "os.environ" in content:
                err = {"file": rel_path, "severity": "WARNING", "ms": ms, "error": "ENV_ACCESS_VIOLATION: Direct OS environment access detected"}
                self.graph["invariants_errors"].append(err)
                self.errors_by_ms[ms] = self.errors_by_ms.get(ms, 0) + 1

        # 1.3 AWS Budget Guard (FinOps - Phase 58+)
        # Prevents re-introduction of costly ALBs (Minimizing $16.20/mo charge)
        if "ApplicationLoadBalancer" in content or "AWS::ElasticLoadBalancingV2::LoadBalancer" in content:
            if not is_test:
                err = {"file": rel_path, "severity": "CRITICAL", "ms": ms, "error": "AWS_BUDGET_VIOLATION: ALB detected. Use AWS App Runner for microservices to maintain $5.00-$20.00 budget."}
                self.graph["invariants_errors"].append(err)
                self.errors_by_ms[ms] = self.errors_by_ms.get(ms, 0) + 1

        # 1.4 Secret Concentration Check (Reducing Secrets Manager costs)
        if "get_secret_value" in content:
            secret_ids = re.findall(r"SecretId=['\"]([^'\"]+)['\"]", content)
            if len(set(secret_ids)) > 1:
                err = {"file": rel_path, "severity": "WARNING", "ms": ms, "error": "AWS_ECONOMY_VIOLATION: Multiple secrets detected. Use one JSON secret with key-value pairs to keep cost at $0.40/mo."}
                self.graph["invariants_errors"].append(err)
                self.errors_by_ms[ms] = self.errors_by_ms.get(ms, 0) + 1

        if is_config and not is_test:
            if "BaseSettings" not in content and "InternoSettings" not in content:
                err = {"file": rel_path, "severity": "CRITICAL", "ms": ms, "error": "AWS_READINESS_VIOLATION: Config should inherit from pydantic BaseSettings (or InternoSettings) for AWS env injection"}
                self.graph["invariants_errors"].append(err)
                self.errors_by_ms[ms] = self.errors_by_ms.get(ms, 0) + 1
            if "localhost" in content.lower() and "=" in content:
                 # Only flag localhost if it's in a DB or service connection string
                 critical_fields = ["database", "url", "host", "uri"]
                 line_content = [line.lower() for line in content.split("\n") if "localhost" in line.lower()]
                 for line in line_content:
                     # Check for critical fields but EXCLUDE the word 'localhost' itself from the field check
                     other_than_localhost = line.replace("localhost", "")
                     if any(field in other_than_localhost for field in critical_fields):
                        err = {"file": rel_path, "severity": "WARNING", "ms": ms, "error": "AWS_READINESS_VIOLATION: Hardcoded 'localhost' detected in critical connection string, use env-injected variables"}
                        self.graph["invariants_errors"].append(err)
                        self.errors_by_ms[ms] = self.errors_by_ms.get(ms, 0) + 1
                        break
            
            if "load_aws_secrets" not in content and ms != "common":
                err = {"file": rel_path, "severity": "WARNING", "ms": ms, "error": "AWS_SECRETS_VIOLATION: Microservice config missing 'load_aws_secrets()' logic for AWS ENV_MODE"}
                self.graph["invariants_errors"].append(err)
                self.errors_by_ms[ms] = self.errors_by_ms.get(ms, 0) + 1

        # 1.2 CORS Lifecycle Dependency Check (AWS Stability)
        if filename == "main.py":
            settings_idx = content.find("from app.core.config import settings")
            cors_idx = content.find("from common.security.cors_setup import setup_cors")
            if settings_idx != -1 and cors_idx != -1 and cors_idx < settings_idx:
                err = {"file": rel_path, "severity": "CRITICAL", "ms": ms, "error": "AWS_CORS_LIFECYCLE_VIOLATION: 'settings' must be imported BEFORE 'setup_cors' in main.py so AWS Secrets are loaded first"}
                self.graph["invariants_errors"].append(err)
                self.errors_by_ms[ms] = self.errors_by_ms.get(ms, 0) + 1

        # 2. Schema-Model Coupling
        if "/app/schemas/" in rel_path:
            for imp_module in imports.values():
                if "app.models" in imp_module:
                    err = {"file": rel_path, "severity": "CRITICAL", "ms": ms, "error": f"SCHEMA_MODEL_COUPLING: Schema depends on ORM models ({imp_module})"}
                    self.graph["invariants_errors"].append(err)
                    self.errors_by_ms[ms] = self.errors_by_ms.get(ms, 0) + 1

        # 3. Leaked DB Exception
        if ("/app/services/" in rel_path or "/app/api/" in rel_path) and "worker.py" not in rel_path:
            for imp_module in imports.values():
                if "sqlalchemy.exc" in imp_module:
                    err = {"file": rel_path, "severity": "WARNING", "ms": ms, "error": f"LEAKED_DB_EXCEPTION: Database exception imported in non-infra layer ({imp_module})"}
                    self.graph["invariants_errors"].append(err)
                    self.errors_by_ms[ms] = self.errors_by_ms.get(ms, 0) + 1

        # Phase 3: Float Extermination Guard (Domain Parity)
        if "/models/" in rel_path or "/schemas/" in rel_path or "domain/" in rel_path:
            # We specifically want to flag type hints like ": float" or "= float" or "Float(" or "[float]"
            if re.search(r"(: float|\[float\]|Mapped\[float\]| Float\(|= float)", content):
                err = {"file": rel_path, "severity": "CRITICAL", "ms": ms, "error": "PRIMITIVE_FLOAT_VIOLATION: Use of float detected in models/schemas. Use Decimal or Money Value Object (Phase 3 Audit)"}
                self.graph["invariants_errors"].append(err)
                self.errors_by_ms[ms] = self.errors_by_ms.get(ms, 0) + 1

        # 5. RLS / Muro de Hierro Guard (Phase 5)
        if filename == "database.py" and "infrastructure" in rel_path:
            if "do_orm_execute" not in content or "with_loader_criteria" not in content:
                err = {"file": rel_path, "severity": "CRITICAL", "ms": ms, "error": "MURO_DE_HIERRO_VIOLATION: missing do_orm_execute for tenant isolation in database.py"}
                self.graph["invariants_errors"].append(err)
                self.errors_by_ms[ms] = self.errors_by_ms.get(ms, 0) + 1
            if "set_tenant_on_checkout" not in content or "checkout" not in content:
                err = {"file": rel_path, "severity": "CRITICAL", "ms": ms, "error": "MURO_DE_HIERRO_VIOLATION: missing connection checkout listener for Postgres RLS in database.py"}
                self.graph["invariants_errors"].append(err)
                self.errors_by_ms[ms] = self.errors_by_ms.get(ms, 0) + 1

        # 4. Cross-Service Dependency Tracking
        if ms in self.MICROSERVICES:
            for imp_module in imports.values():
                for other in self.MICROSERVICES:
                    if other != ms and f"{other}." in imp_module and "common" not in imp_module:
                        deps = self.inter_service_dependencies.get(ms, set())
                        deps.add(other)
                        self.inter_service_dependencies[ms] = deps

        # Analyze structure
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                self._analyze_class(file_path, node, imports, ms)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._analyze_function(file_path, None, node, ms)
                
            if ("_app/domain/services/" in rel_path or "_app/services/" in rel_path) and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                self.domain_services_count[ms] = self.domain_services_count.get(ms, 0) + 1

    def _analyze_class(self, file_path: str, node: ast.ClassDef, imports: Dict[str, str], ms: str):
        rel_path = os.path.relpath(file_path, self.root_dir).replace("\\", "/")
        base_classes = [b.id if isinstance(b, ast.Name) else (b.attr if isinstance(b, ast.Attribute) else "") for b in node.bases]
        
        if "MultiTenantBase" in base_classes and "AuditBase" in base_classes:
            err = {"file": rel_path, "class": node.name, "severity": "LOW", "ms": ms, "error": "Redundant Inheritance: MultiTenantBase already includes AuditBase"}
            self.graph["invariants_errors"].append(err)

        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._analyze_function(file_path, node, item, ms)

    def _analyze_function(self, file_path: str, class_node: ast.ClassDef | None, node: ast.AST, ms: str):
        rel_path = os.path.relpath(file_path, self.root_dir).replace("\\", "/")
        source = ""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = ast.get_source_segment(f.read(), node) or ""
        except: pass

        class_name = class_node.name if class_node else "ModuleLevel"

        # Phase 2: Scope Enforcement Guard (Endpoints)
        if "/api/" in rel_path or "/endpoints/" in rel_path or "/routers/" in rel_path:
            if "Depends(get_current_active_user)" in source or "Depends(get_current_user)" in source:
                # Exclude purely read-only or public functions that don't need explicit scopes,
                # but flag if it's an operational endpoint missing require_scope
                if not any(k in source for k in ["require_scope", "SecurityScopes", "Depends(get_login_token)"]):
                    # Flag as WARNING to manually review if it should have a scope
                    err = {"file": rel_path, "class": class_name, "method": node.name, "severity": "WARNING", "ms": ms, "error": "MISSING_SCOPE_VALIDATION: Endpoint uses get_current_user but lacks require_scope or SecurityScopes (Phase 2 Audit)"}
                    self.graph["invariants_errors"].append(err)
                    self.errors_by_ms[ms] = self.errors_by_ms.get(ms, 0) + 1

        # Multi-tenancy check (Phase 89+ — Smart Exclusions)
        # Methods that access data globally by design are excluded:
        #   - External/public token lookups (providers don't know company_id)
        #   - Escalation/SLA cron jobs (cross-tenant orchestration)
        #   - Global aggregation/reporting methods
        if class_node and "Repository" in class_node.name and node.name.startswith(("get_", "find_", "list_")):
            if any(k in source for k in ["select(", "filter(", "where("]):
                # Known tenant-aware markers
                tenant_markers = [
                    "company_id", "tenant_id", "filter_by_company",
                    "MultiTenant", "_apply_tenant_filter", "bypass_tenant"
                ]
                # Smart exclusion: method names that are global by design
                global_access_patterns = [
                    "external_token", "escalation", "public",
                    "global", "cron", "webhook", "migration"
                ]
                method_lower = node.name.lower()
                is_global_by_design = any(p in method_lower for p in global_access_patterns)

                if not is_global_by_design and not any(t in source for t in tenant_markers):
                    err = {"file": rel_path, "class": class_name, "method": node.name, "severity": "WARNING", "ms": ms, "error": "MISSING_TENANT_FILTER: Possible missing company_id filter"}
                    self.graph["invariants_errors"].append(err)
                    self.errors_by_ms[ms] = self.errors_by_ms.get(ms, 0) + 1

        # 2. Density Guard Validation (Warehouse Integrity - Phase 59)
        # Ensures location capacity is checked before recording stock entry.
        inventory_critical_methods = ["record_entry", "complete_transfer", "receive", "relocate", "register_movement"]
        if ms == "inventory_service" and any(m in node.name.lower() for m in inventory_critical_methods):
            # If recording a movement (IN or RELOCATE)
            if "record_movement" in source:
                # Must call capacity check beforehand
                if not any(k in source for k in ["_check_location_capacity", "DensityGuard", 'validation_status="PENDING"', 'validation_status = "PENDING"']):
                    err = {"file": rel_path, "class": class_name, "method": node.name, "severity": "CRITICAL", "ms": ms, "error": "MISSING_DENSITY_GUARD: Warehouse entry detected without location capacity validation."}
                    self.graph["invariants_errors"].append(err)
                    self.errors_by_ms[ms] = self.errors_by_ms.get(ms, 0) + 1

        # 3. Subscription Guard Compliance (SaaS Integrity - Phase 74/19)
        # Verifies that write operations in critical services are aware of the readonly status.
        write_methods = ["post", "put", "patch", "delete", "create_", "update_", "delete_"]
        critical_write_services = ["inventory_service", "mes_service", "wms_service", "asset_manager_service"]
        if ms in critical_write_services and any(m in node.name.lower() for m in write_methods):
            if "/app/api/" in rel_path or "/app/services/" in rel_path:
                # We expect them to at least reference SecurityContext or the status claim
                # if they are performing domain-level enforcement or if the middleware is bypassed
                if "status" not in source.lower() and "readonly" not in source.lower() and "security_context" not in source.lower():
                     # Only warning because global middleware handles most cases, but domain-level awareness is preferred for granular feedback
                     err = {"file": rel_path, "class": class_name, "method": node.name, "severity": "WARNING", "ms": ms, "error": "SUBSCRIPTION_AWARENESS_WARNING: Write operation in critical service might be missing subscription-state awareness (readonly/status)"}
                     self.graph["invariants_errors"].append(err)
                     self.errors_by_ms[ms] = self.errors_by_ms.get(ms, 0) + 1

        # 4. Public Endpoint Data Leakage Guard (Phase 90)
        # Endpoints under /public/ must NOT return sensitive tenant fields
        if "/routers/" in rel_path or "/endpoints/" in rel_path:
            if "public" in node.name.lower():
                sensitive_fields = ["company_id", "tenant_id", "created_by", "assigned_to_id", "user_id"]
                leaked = [f for f in sensitive_fields if f'"{f}"' in source or f"'{f}'" in source]
                # Only flag if the method explicitly serializes these fields in a response dict
                if leaked and ("return {" in source or "jsonable_encoder" in source):
                    err = {"file": rel_path, "class": class_name, "method": node.name, "severity": "WARNING", "ms": ms, "error": f"PUBLIC_DATA_LEAKAGE: Public endpoint may expose sensitive fields: {', '.join(leaked)}"}
                    self.graph["invariants_errors"].append(err)
                    self.errors_by_ms[ms] = self.errors_by_ms.get(ms, 0) + 1

    def print_report(self):
        critical = [e for e in self.graph["invariants_errors"] if e["severity"] == "CRITICAL"]
        warnings = [e for e in self.graph["invariants_errors"] if e["severity"] == "WARNING"]
        
        print("="*80)
        print("  Code Knowledge Graph Audit Report")
        print(f"  Scanned from: {self.root_dir}")
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

        print("\n[SUMMARY] Compliance Report by Microservice:")
        print("-" * 60)
        for ms in sorted(self.MICROSERVICES):
            if self.ms_scanned_files.get(ms, 0) == 0:
                continue
            err_count = self.errors_by_ms.get(ms, 0)
            score = max(0, 100 - (err_count * 10))
            status = "CLEAN" if score == 100 else "DEBT"
            print(f"   {ms:20} : {score:3}% Compliance ({err_count} err) | Status: {status}")

        print("\n[INTER-SERVICE DEPENDENCIES]:")
        print("-" * 60)
        for ms, deps in sorted(self.inter_service_dependencies.items()):
            print(f"   {ms:20} -> {', '.join(sorted(deps))}")

        print("\n" + "="*80)
        print(f"  TOTAL ERRORS: {len(self.graph['invariants_errors'])}")
        print("="*80)

    def save(self, output_ptr: str):
        # Update graph with final metrics
        self.graph["compliance_report"] = {ms: max(0, 100 - (self.errors_by_ms.get(ms, 0) * 10)) for ms in self.MICROSERVICES}
        self.graph["inter_service_deps"] = {ms: list(deps) for ms, deps in self.inter_service_dependencies.items()}
        with open(output_ptr, "w", encoding="utf-8") as f:
            json.dump(self.graph, f, indent=4)

if __name__ == "__main__":
    import sys
    root = os.getcwd()
    gen = CodeGraphGenerator(root)
    gen.scan()
    gen.print_report()
    gen.save(os.path.join(root, "code_graph.json"))
    
    critical_errors = [e for e in gen.graph["invariants_errors"] if e["severity"] == "CRITICAL"]
    if len(critical_errors) > 0:
        sys.exit(1)
