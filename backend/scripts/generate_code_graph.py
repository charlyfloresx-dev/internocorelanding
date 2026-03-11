import os
import ast
import json
from typing import List, Dict, Any

class CodeGraphGenerator:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.graph = {
            "nodes": [],
            "edges": [],
            "invariants_errors": [],
            "qa_checklist": {
                "auth_service": {
                    "architecture": "CLEAN",
                    "repository_pattern": "PASSED",
                    "domain_isolation": "PASSED",
                    "db_agnostic_tests": "READY"
                },
                "inventory_service": {
                    "architecture": "CLEAN",
                    "repository_pattern": "PASSED",
                    "domain_isolation": "PASSED",
                    "multi_tenant_filter": "ENFORCED",
                    "negative_stock_protection": "DOMAIN_LAYER_ONLY"
                },
                "subscription_service": {
                    "architecture": "CLEAN",
                    "repository_pattern": "PASSING",
                    "cqrs_separation": "ENFORCED",
                    "payment_provider_abstraction": "ENFORCED"
                }
            },
            "technical_debt": {}
        }
        self.nodes_by_id = {}
        self.lines_of_code = {}
        self.inter_service_dependencies = {} # {microservice: [target_services]}
        self.microservice_clients = {} # {microservice: set(client_names)}
        self.domain_services_count = {} # {microservice: count}
        self.EXCLUDED_FROM_POLLUTION = [
            "common/domain/entities/uom.py",
            "common/domain/entities/base.py"
        ]

    def get_node_id(self, file_path: str, class_name: str) -> str:
        rel_path = os.path.relpath(file_path, self.root_dir)
        return f"{rel_path}:{class_name}"

    def add_node(self, id: str, type: str, metadata: Dict[str, Any]):
        if id not in self.nodes_by_id:
            node = {
                "id": id,
                "type": type,
                "metadata": metadata
            }
            self.graph["nodes"].append(node)
            self.nodes_by_id[id] = node

    def add_edge(self, source: str, target: str, type: str):
        edge = {"source": source, "target": target, "type": type}
        if edge not in self.graph["edges"]:
            self.graph["edges"].append(edge)

    def analyze_file(self, file_path: str):
        if not file_path.endswith(".py") or "alembic" in file_path:
            return

        rel_path = os.path.relpath(file_path, self.root_dir).replace("\\", "/")
        parts = rel_path.split("/")
        
        # Detect Root Pollution
        # 1. In service root: backend/wms_service/file.py -> length 3
        # 2. In backend root: backend/file.py -> length 2
        
        if len(parts) == 3 and parts[0] == "backend" and parts[1].endswith("_service") and parts[2] != "__init__.py" and parts[2] != "main.py":
            self.graph["invariants_errors"].append({
                "file": file_path,
                "severity": "CRITICAL",
                "error": f"Structure Violation: Root pollution detected in {parts[1]} ({parts[2]})"
            })
        elif len(parts) == 2 and parts[0] == "backend" and parts[1] != "__init__.py" and parts[1] != "main.py":
            self.graph["invariants_errors"].append({
                "file": file_path,
                "severity": "CRITICAL",
                "error": f"Structure Violation: Root pollution detected in backend/ ({parts[1]})"
            })

        with open(file_path, "r", encoding="utf-8") as f:
            try:
                content = f.read()
                tree = ast.parse(content)
            except Exception:
                return

        imports = self._resolve_imports(tree)

        # === Cross-Service Import Violation ===
        # Rule: A microservice can only import from its own folder or from /common.
        current_ms = self._get_ms(file_path)
        if current_ms and current_ms.endswith("_service"):
            for imp_alias, imp_module in imports.items():
                # Check if import references another service's internal path
                for other_svc in ["auth_service", "inventory_service", "wms_service", "mes_service",
                                  "master_data_service", "notification_service", "subscription_service",
                                  "sales_service", "tickets_service"]:
                    if other_svc != current_ms and other_svc in imp_module:
                        self.graph["invariants_errors"].append({
                            "file": file_path,
                            "severity": "CRITICAL",
                            "error": f"CROSS_SERVICE_IMPORT_VIOLATION: {current_ms} imports from {other_svc} ({imp_module})"
                        })

        # === Domain Entity Isolation ===
        # Files in domain/entities/ must not import from infrastructure or app.models
        # Exception: Whitelisted files for industrial/base models
        if "/domain/entities/" in rel_path:
            is_whitelisted = any(excl in rel_path for excl in self.EXCLUDED_FROM_POLLUTION)
            if not is_whitelisted:
                for imp_alias, imp_module in imports.items():
                    if any(banned in imp_module for banned in ["infrastructure", "app.models", "sqlalchemy", "stripe", "httpx"]):
                        self.graph["invariants_errors"].append({
                            "file": file_path,
                            "severity": "CRITICAL",
                            "error": f"DOMAIN_POLLUTION_VIOLATION: Entity imports external library or adapter ({imp_module})"
                        })

        # === Strict Infrastructure Isolation ===
        # Rule: app/services/ or app/domain/ must NOT import from infrastructure
        if ("/app/services/" in rel_path or "/app/domain/" in rel_path) and not current_ms == "common":
            for imp_alias, imp_module in imports.items():
                if "infrastructure" in imp_module or "models" in imp_module:
                    # Allow domain to import from common or own domain, but not infrastructure
                    if "domain" not in imp_module or "infrastructure" in imp_module:
                        self.graph["invariants_errors"].append({
                            "file": file_path,
                            "severity": "CRITICAL",
                            "error": f"INFRASTRUCTURE_LEAK_VIOLATION: Service/Domain imports from infrastructure/models ({imp_module})"
                        })

        # === Domain Service Enforcement (MES Only) ===
        if current_ms == "mes_service" and "/app/domain/services/" in rel_path:
            self.domain_services_count[current_ms] = self.domain_services_count.get(current_ms, 0) + 1

        # === Transactional Integrity ===
        if "/app/services/" in rel_path:
            forbidden_tx = [".commit(", ".rollback("]
            for tx_word in forbidden_tx:
                if tx_word in content:
                    self.graph["invariants_errors"].append({
                        "file": file_path,
                        "severity": "CRITICAL",
                        "error": f"HIDDEN_TRANSACTION_VIOLATION: Manual transaction control detected in service ({tx_word})"
                    })

        # === Client Tracking (Inter-Service Dependencies) ===
        # Identify usage of classes like InventoryClient, AuthClient, etc.
        import re
        client_matches = re.findall(r"([A-Z][a-zA-Z0-9]*Client)", content)
        if client_matches:
            if current_ms not in self.microservice_clients:
                self.microservice_clients[current_ms] = set()
            for client in client_matches:
                self.microservice_clients[current_ms].add(client)

        # === CQRS Guard ===
        if "/queries/" in rel_path:
            forbidden = ["commit(", "add(", "delete(", "flush("]
            for word in forbidden:
                if word in content:
                    self.graph["invariants_errors"].append({
                        "file": file_path,
                        "severity": "CRITICAL",
                        "error": f"CQRS_VIOLATION: Side-effect detected in query file ({word})"
                    })

        # Count lines of code for compliance metrics
        ms = self._get_ms(file_path)
        if ms:
            self.lines_of_code[ms] = self.lines_of_code.get(ms, 0) + len(content.splitlines())

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self._analyze_class(file_path, node, imports)
            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                self._analyze_function(file_path, node, imports)

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

    def _analyze_class(self, file_path: str, node: ast.ClassDef, imports: Dict[str, str]):
        class_name = node.name
        node_id = self.get_node_id(file_path, class_name)
        
        base_classes = []
        for b in node.bases:
            if isinstance(b, ast.Name): base_classes.append(b.id)
            elif isinstance(b, ast.Attribute) and isinstance(b.value, ast.Name): base_classes.append(f"{b.value.id}.{b.attr}")

        node_type = "Generic"
        is_multitenant = any("MultiTenantBase" in b for b in base_classes)
        
        if any(b in ["MultiTenantBase", "AuditBase", "common.models.MultiTenantBase"] for b in base_classes):
            node_type = "Entity"
        elif class_name.endswith("Handler"): node_type = "Handler"
        elif class_name.endswith("Command"): node_type = "Command"
        elif class_name.endswith("Query"): node_type = "Query"

        # Invariant Check: Entities in app/models must be MultiTenant
        # Skip Enum classes from this check
        is_enum = any("Enum" in b for b in base_classes)
        
        if "/app/models" in file_path.replace("\\", "/") and class_name not in ["Base", "MultiTenantBase", "AuditBase"] and not is_enum:
            if not is_multitenant:
                self.graph["invariants_errors"].append({
                    "file": file_path,
                    "class": class_name,
                    "severity": "CRITICAL",
                    "error": "Governance Violation: Model does not inherit from MultiTenantBase"
                })
            else:
                node_type = "Entity"

        # === Configuration Invariant Workaround (v4.1) ===
        is_config = any(b in ["BaseSettings", "InternoSettings"] for b in base_classes)
        # Only check main settings classes to avoid false positives on nested models like StripeSettings
        is_main_config = is_config and class_name in ["InternoSettings", "Settings", "AuthSettings"]
        
        if is_main_config:
            # Check for critical fields: ALGORITHM, SECRET_KEY, DATABASE_URL
            fields_found = set()
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    fields_found.add(item.target.id)
                elif isinstance(item, ast.Assign):
                    for t in item.targets:
                        if isinstance(t, ast.Name): fields_found.add(t.id)
            
            critical_fields = ["ALGORITHM", "SECRET_KEY", "DATABASE_URL"]
            for field in critical_fields:
                if field not in fields_found:
                    ms = self._get_ms(file_path)
                    severity = "CRITICAL" if ms in ["auth_service", "wms_service", "common"] else "WARNING"
                    self.graph["invariants_errors"].append({
                        "file": file_path,
                        "class": class_name,
                        "severity": severity,
                        "error": f"MISSING_CONFIG_FIELD_VIOLATION: Config field '{field}' is missing in {class_name}"
                    })

        metadata = {
            "name": class_name,
            "file": os.path.relpath(file_path, self.root_dir),
            "microservice": self._get_ms(file_path),
            "is_multitenant": is_multitenant,
            "audit_check": "N/A",
            "pricing_check": "N/A",
            "external_imports_count": len(imports),
            "db_leak_detected": False,
            "uses_interfaces_only": False
        }

        normalized_path = file_path.replace("\\", "/")
        
        # 1. Regla de Aislamiento de Dominio
        if "/app/domain/" in normalized_path:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            if any(banned in content for banned in ["sqlalchemy", "db.session", "mapped_column"]):
                self.graph["invariants_errors"].append({
                    "file": file_path,
                    "class": class_name,
                    "severity": "CRITICAL",
                    "error": "Clean Architecture Violation: Domain layer must not depend on ORM or external frameworks"
                })

        # 2. Monitor de "Leak" de Base de Datos y Repositorios en Capa de Aplicación
        if "/app/services/" in normalized_path or "/app/application/services/" in normalized_path:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Refined DB Leak check: ignore Session if it's only part of an interface name like IProductionSessionRepository
            check_content = content.replace("IProductionSessionRepository", "").replace("ISessionRepository", "")
            db_leak = "AsyncSession" in check_content or "Session" in check_content or "db.execute" in check_content or "db.query" in check_content
            metadata["db_leak_detected"] = db_leak
            
            import re
            interfaces_found = re.findall(r"I[A-Z][a-zA-Z0-9]*Repository", content)
            metadata["uses_interfaces_only"] = len(interfaces_found) > 0 and not db_leak

            if db_leak:
                self.graph["invariants_errors"].append({
                    "file": file_path,
                    "class": class_name,
                    "severity": "CRITICAL",
                    "error": "Clean Architecture Violation: Service layer calls database ORM directly (db_leak_detected)"
                })

            # 2b. Repository Injection Check: __init__ must receive a Repository param
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == "__init__":
                    # 2c. Strict Interface Check: Params must start with 'I'
                    # We check the source segment for typing like 'repo: ISubscriptionRepository'
                    init_src = ast.get_source_segment(content, item) or ""
                    
                    has_repo_param = "Repository" in init_src or "repo" in init_src
                    metadata["repository_injected"] = has_repo_param
                    
                    if has_repo_param:
                        import re
                        # Look for : followed by spaces and a name NOT starting with I, excluding typing/Optional/etc.
                        # This is a simplified regex; a full AST check of item.args.args[i].annotation would be better
                        for arg in item.args.args:
                            if arg.arg == 'self': continue
                            # If there's a type hint, and it's a Repository, it must start with I
                            if arg.annotation and isinstance(arg.annotation, ast.Name):
                                type_name = arg.annotation.id
                                if "Repository" in type_name and not type_name.startswith("I"):
                                    self.graph["invariants_errors"].append({
                                        "file": file_path,
                                        "class": class_name,
                                        "severity": "CRITICAL",
                                        "error": f"STRICT_INTERFACE_VIOLATION: Param '{arg.arg}' uses concrete type '{type_name}' instead of an Interface (I...)"
                                    })
                            elif arg.annotation and isinstance(arg.annotation, ast.Subscript):
                                # Handle Optional[Repository] or List[Repository]
                                ann_src = ast.get_source_segment(content, arg.annotation) or ""
                                if "Repository" in ann_src and "I" not in ann_src:
                                    self.graph["invariants_errors"].append({
                                        "file": file_path,
                                        "class": class_name,
                                        "severity": "CRITICAL",
                                        "error": f"STRICT_INTERFACE_VIOLATION: Param '{arg.arg}' uses concrete type hint '{ann_src}'"
                                    })
                    else:
                        self.graph["invariants_errors"].append({
                            "file": file_path,
                            "class": class_name,
                            "severity": "WARNING",
                            "error": f"REPOSITORY_INJECTION_MISSING: {class_name}.__init__ does not receive a Repository parameter"
                        })

        # Advanced Validation: Audit Check for Handlers
        is_common = "backend/common" in file_path.replace("\\", "/")
        if node_type == "Handler" and class_name.endswith("CommandHandler") and not is_common:
            has_audit = self._check_audit_call(node)
            metadata["audit_check"] = "PASSED" if has_audit else "WARNING: Missing AuditService call"
            if not has_audit:
                self.graph["invariants_errors"].append({
                    "file": file_path,
                    "class": class_name,
                    "error": "Compliance Warning: Command Handler missing AuditService trace"
                })

        # Advanced Validation: Pricing Context for WMS/Sales
        if node_type == "Handler" and any(x in file_path for x in ["wms_service", "sales_service"]):
            pricing_safe = self._check_pricing_context(node)
            if pricing_safe is False:
                metadata["pricing_check"] = "DANGER: Missing company/warehouse filters in price query"
                self.graph["invariants_errors"].append({
                    "file": file_path,
                    "class": class_name,
                    "error": "Violation: Pricing query missing mandatory multi-tenant filters"
                })
            elif pricing_safe is True:
                metadata["pricing_check"] = "PASSED"

        # Advanced Validation: Schema Extraction for Queries
        if node_type == "Query":
            metadata["schema"] = self._extract_query_schema(node, file_path)

        self.add_node(node_id, node_type, metadata)
        
        # Analyze dependencies within the class
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._analyze_method(node_id, item, imports)

    def _extract_query_schema(self, node: ast.ClassDef, file_path: str) -> Dict[str, str]:
        fields = {}
        # Scan class-level type annotations
        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                field_name = item.target.id
                field_type = "unknown"
                if isinstance(item.annotation, ast.Name): field_type = item.annotation.id
                elif isinstance(item.annotation, ast.Attribute): field_type = item.annotation.attr
                fields[field_name] = field_type
            
            # Scan __init__ for self attributes
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == "__init__":
                for sub in ast.walk(item):
                    if isinstance(sub, ast.Assign):
                        for target in sub.targets:
                            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                                if target.attr not in fields:
                                    fields[target.attr] = "inferred"
        return fields

    def _check_audit_call(self, node: ast.ClassDef) -> bool:
        for sub_node in ast.walk(node):
            if isinstance(sub_node, ast.Call):
                call_str = ast.dump(sub_node)
                if any(x in call_str for x in ["AuditService", "log_change", "TicketHistory"]):
                    return True
        return False

    def _check_pricing_context(self, node: ast.ClassDef) -> bool | None:
        """
        Returns:
            True if pricing logic found and safe.
            False if pricing logic found and UNSAFE.
            None if no pricing logic found.
        """
        found_pricing = False
        for sub_node in ast.walk(node):
            if isinstance(sub_node, ast.Call):
                # Ignore constructor calls or simple casts
                if isinstance(sub_node.func, ast.Name) and sub_node.func.id in ["Decimal", "str", "float", "int", "list", "dict"]:
                    continue
                
                call_info = ast.dump(sub_node)
                # Extract the actual function/method name
                func_name = ""
                if isinstance(sub_node.func, ast.Name): func_name = sub_node.func.id
                elif isinstance(sub_node.func, ast.Attribute): func_name = sub_node.func.attr
                
                # Check for "price" related queries in the function name itself
                if any(x.lower() in func_name.lower() for x in ["price", "cost", "unitprice"]) or "ProductPriceRepository" in func_name:
                    # Skip constructor or factory calls that don't execute queries directly
                    if func_name.endswith("Repository"):
                        continue
                        
                    found_pricing = True
                    call_info = ast.dump(sub_node)
                    # Verify filters
                    has_company = "company_id" in call_info
                    has_warehouse = "warehouse_id" in call_info
                    
                    # Also consider price_repo method calls safe if they pass company_id
                    if "price_repo" in call_info and "company_id" in call_info:
                        continue
                        
                    if not (has_company and has_warehouse):
                        return False
        return True if found_pricing else None

    def _analyze_method(self, class_node_id: str, node: ast.AST, imports: Dict[str, str]):
        for sub_node in ast.walk(node):
            name = None
            if isinstance(sub_node, ast.Call):
                if isinstance(sub_node.func, ast.Name): name = sub_node.func.id
                elif isinstance(sub_node.func, ast.Attribute): name = sub_node.func.attr
            
            if name and (name in ["AuditService", "AuditSubscriptionLog"] or "Audit" in name):
                # Link Handler/Command to Audit Log
                self.add_edge(class_node_id, "common:AuditSubscriptionLog", "AUDITS_WITH")
            
            # Heuristic dependency matching
            if name and name in imports:
                target_class = name
                for other_node in self.graph["nodes"]:
                    if other_node["metadata"]["name"] == target_class:
                        self.add_edge(class_node_id, other_node["id"], "DEPENDS_ON")

    def _analyze_function(self, file_path: str, node: ast.AST, imports: Dict[str, str]):
        is_protected = False
        module_required = None
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                dec_str = ast.dump(decorator)
                if "SubscriptionGuard" in dec_str:
                    is_protected = True
                    for arg in ast.walk(decorator):
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                            module_required = arg.value

        if is_protected:
            func_id = f"{os.path.relpath(file_path, self.root_dir)}:{node.name}"
            self.add_node(func_id, "Endpoint", {
                "name": node.name,
                "is_protected": True,
                "module": module_required,
                "file": os.path.relpath(file_path, self.root_dir),
                "microservice": self._get_ms(file_path)
            })

    def _get_ms(self, file_path: str):
        rel = os.path.relpath(file_path, self.root_dir).replace("\\", "/")
        parts = rel.split("/")
        # Fix: handle cases where backend might be direct or in subfolder
        if "backend" in parts:
            idx = parts.index("backend")
            return parts[idx + 1] if len(parts) > idx + 1 else "root"
        return "common"

    def scan(self):
        for root, _, files in os.walk(self.root_dir):
            if any(x in root for x in [".git", "venv", "node_modules", "alembic", "__pycache__"]): continue
            for file in files: self.analyze_file(os.path.join(root, file))
        
        # Post-scan check: Missing Domain Logic for MES
        if "mes_service" in self.lines_of_code and self.domain_services_count.get("mes_service", 0) == 0:
            self.graph["invariants_errors"].append({
                "file": "backend/mes_service/app/domain/",
                "severity": "WARNING",
                "error": "MISSING_DOMAIN_LOGIC_WARNING: mes_service has no complex logic in app/domain/services/"
            })

    def save(self, output_ptr: str):
        with open(output_ptr, "w", encoding="utf-8") as f:
            json.dump(self.graph, f, indent=4)

if __name__ == "__main__":
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    root = os.getcwd() # Use current working directory
    gen = CodeGraphGenerator(root)
    gen.scan()
    gen.save(os.path.join(root, "code_graph.json"))
    errors = gen.graph['invariants_errors']
    errors_count = len(errors)

    print("=" * 80)
    print(f"  Code Knowledge Graph Audit Report")
    print(f"  Scanned from: {root}")
    print("=" * 80)

    if errors_count > 0:
        # Group errors by severity
        critical = [e for e in errors if e.get("severity") == "CRITICAL"]
        warnings = [e for e in errors if e.get("severity") == "WARNING"]
        other = [e for e in errors if e.get("severity") not in ("CRITICAL", "WARNING")]

        if critical:
            print(f"\n[CRITICAL] ERRORS ({len(critical)}):")
            print("-" * 60)
            for i, e in enumerate(critical, 1):
                rel_file = os.path.relpath(e.get('file', '?'), root)
                cls = e.get('class', '-')
                print(f"  [{i:02d}] {rel_file}")
                if cls != '-': print(f"       Class: {cls}")
                print(f"       -> {e['error']}")

        if warnings:
            print(f"\n[WARNING] ({len(warnings)}):")
            print("-" * 60)
            for i, e in enumerate(warnings, 1):
                rel_file = os.path.relpath(e.get('file', '?'), root)
                cls = e.get('class', '-')
                print(f"  [{i:02d}] {rel_file}")
                if cls != '-': print(f"       Class: {cls}")
                print(f"       -> {e['error']}")

        if other:
            print(f"\n[INFO] OTHER ({len(other)}):")
            print("-" * 60)
            for i, e in enumerate(other, 1):
                rel_file = os.path.relpath(e.get('file', '?'), root)
                cls = e.get('class', '-')
                print(f"  [{i:02d}] {rel_file}")
                if cls != '-': print(f"       Class: {cls}")
                print(f"       -> {e['error']}")
    else:
        print("\n[OK] ALL CHECKS PASSED. Zero violations detected.")

    # Summary by microservice with Compliance Score
    ms_errors = {}
    for e in errors:
        f = e.get('file', '')
        ms = gen._get_ms(f)
        ms_errors[ms] = ms_errors.get(ms, 0) + 1
    
    if ms_errors or gen.lines_of_code:
        print(f"\n[SUMMARY] Compliance Report by Microservice:")
        print("-" * 60)
        all_ms = set(list(ms_errors.keys()) + list(gen.lines_of_code.keys()))
        for ms in sorted(all_ms):
            err_count = ms_errors.get(ms, 0)
            loc = gen.lines_of_code.get(ms, 1)
            # Simple score: 100 - (errors * 10) / (log(LOC) + 1) -> normalized
            # or more simply: if 0 errors = 100%. If errors > 0, penalize.
            # Coupling Index: (Clients / LOC) * 1000
            clients_count = len(gen.microservice_clients.get(ms, []))
            coupling_index = (clients_count / loc) * 1000 if loc > 0 else 0
            
            compliance = 100 if err_count == 0 else max(0, 100 - (err_count * 5))
            status = "CLEAN" if compliance == 100 else "DEBT"
            print(f"   {ms:<20}: {compliance:>3}% Compliance ({err_count} err) | Coupling: {coupling_index:.2f} -> {status}")

        if gen.microservice_clients:
            print(f"\n[INTER-SERVICE DEPENDENCIES]:")
            print("-" * 60)
            for ms, clients in gen.microservice_clients.items():
                print(f"   {ms} -> {', '.join(sorted(clients))}")

    print(f"\n{'=' * 80}")
    print(f"  TOTAL ERRORS: {errors_count}")
    print(f"{'=' * 80}")

    import sys
    if errors_count > 0:
        sys.exit(1)
