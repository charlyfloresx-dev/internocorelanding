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
        # Rev163 — HARD_FK_CROSS_SERVICE two-pass data
        self.service_tables: Dict[str, str] = {}   # table_name → microservice
        self.model_files: List[tuple] = []          # [(file_path, ms)]
        # Microservices to track for report
        self.ms_scanned_files = {} # {microservice: count}
        self.scanned_files_log = [] # Track every file audited
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

    def _check_hard_fk_cross_service(self):
        """
        N4. HARD_FK_CROSS_SERVICE (CRITICAL) — two-pass check.
        Pass 1 (during analyze_file): builds self.service_tables {table_name → microservice}.
        Pass 2 (here, post-scan): validates that no model defines a DB-level ForeignKey()
        pointing to a table owned by a different microservice.
        Cross-service relationships must use soft FKs (UUID field, no DB constraint).
        """
        for file_path, ms in self.model_files:
            rel_path = os.path.relpath(file_path, self.root_dir).replace("\\", "/")
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue
            # Match ForeignKey("tablename.column") — both quote styles
            for fk_match in re.finditer(r'ForeignKey\(["\'](\w+)\.\w+["\']', content):
                ref_table = fk_match.group(1)
                owner_ms = self.service_tables.get(ref_table)
                # Skip: unknown table, shared/disputed ownership, common tables, self-reference
                if not owner_ms or owner_ms in ("__SHARED__", "common") or owner_ms == ms:
                    continue
                if owner_ms != ms and owner_ms != "common":
                    err = {
                        "file": rel_path, "severity": "CRITICAL", "ms": ms,
                        "error": (
                            f"HARD_FK_CROSS_SERVICE: ForeignKey('{ref_table}.*') in {ms} "
                            f"references table owned by {owner_ms} — "
                            f"use a soft FK (UUID field, no DB constraint) per Iron Wall ADR"
                        )
                    }
                    self.graph["invariants_errors"].append(err)
                    self.errors_by_ms[ms] = self.errors_by_ms.get(ms, 0) + 1

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
        self._check_hard_fk_cross_service()  # N4 Rev163
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
        
        self.scanned_files_log.append(f"AUDITED: {rel_path} [{ms}]")
        
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
        # Exclude test files, root-level diagnostic/utility scripts, and known cross-service
        # seed orchestrators that intentionally import from multiple services by design.
        SEED_ORCHESTRATORS = {"unified_industrial_seed.py"}
        is_test = (
            filename.startswith("test_")
            or "/tests/" in rel_path
            or "/scripts/" in rel_path
            or rel_path.startswith("scripts/")   # root-level dev utilities
            or filename in SEED_ORCHESTRATORS    # dev-only seed scripts, not production code
        )

        # 1. ENV Violation (Ignore config files and core folder as they are the source of truth)
        if "/app/core/" not in rel_path and not is_config and "setup.py" not in rel_path and "seed" not in rel_path and not is_test:
            if "os.getenv(" in content or "os.environ" in content:
                err = {"file": rel_path, "severity": "WARNING", "ms": ms, "error": "ENV_ACCESS_VIOLATION: Direct OS environment access detected"}
                self.graph["invariants_errors"].append(err)
                self.errors_by_ms[ms] = self.errors_by_ms.get(ms, 0) + 1

        # 1.3 AWS Budget Guard (FinOps - Phase 58+)
        # Prevents re-introduction of costly ALBs (Minimizing $16.20/mo charge)
        if "ApplicationLoadBalancer" in content or "AWS::ElasticLoadBalancingV2::LoadBalancer" in content:
            if not is_test and "generate_code_graph.py" not in filename:
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
            # Exclude latitude and longitude since geo-coordinates are standardly represented as floats
            content_without_geo = re.sub(r"(lat|lng|latitude|longitude)[^:\n]*:\s*Optional\[float\]|(lat|lng|latitude|longitude)[^:\n]*:\s*float", "", content)
            if re.search(r"(: float|\[float\]|Mapped\[float\]| Float\(|= float)", content_without_geo):
                err = {"file": rel_path, "severity": "CRITICAL", "ms": ms, "error": "PRIMITIVE_FLOAT_VIOLATION: Use of float detected in models/schemas. Use Decimal or Money Value Object (Phase 3 Audit)"}
                self.graph["invariants_errors"].append(err)
                self.errors_by_ms[ms] = self.errors_by_ms.get(ms, 0) + 1

        # ── Rev163 Common Audit Specs ──────────────────────────────────────────

        # N1. UNIQUE_WITHOUT_COMPANY_ID (CRITICAL)
        # UniqueConstraints on business fields without company_id scope allow data collision
        # across tenants (e.g. two companies sharing the same folio / SKU / code).
        if "/models/" in rel_path and ms not in ("common",) and not is_test:
            GLOBAL_UNIQUE_WHITELIST = {
                "email", "token_hash", "family_salt", "stripe_customer_id",
                "stripe_subscription_id", "slug", "external_id",
            }
            for uc_match in re.finditer(r"UniqueConstraint\((.*?)\)", content, re.DOTALL):
                uc_args = uc_match.group(1)
                normalized_uc = re.sub(r"\s+", " ", uc_args).strip()
                if "company_id" in normalized_uc or "tenant_id" in normalized_uc:
                    continue
                positional = [
                    a.strip().strip("\"'")
                    for a in normalized_uc.split(",")
                    if not a.strip().startswith(("name=", "schema="))
                ]
                positional_clean = [p for p in positional if p]
                has_id_field = any(f.endswith("_id") for f in positional_clean)
                all_whitelisted = all(f in GLOBAL_UNIQUE_WHITELIST for f in positional_clean)
                if not has_id_field and not all_whitelisted and positional_clean:
                    err = {
                        "file": rel_path, "severity": "CRITICAL", "ms": ms,
                        "error": (
                            f"UNIQUE_WITHOUT_COMPANY_ID: UniqueConstraint({normalized_uc}) "
                            f"missing company_id — allows cross-tenant collision on: "
                            f"{', '.join(positional_clean)}"
                        )
                    }
                    self.graph["invariants_errors"].append(err)
                    self.errors_by_ms[ms] = self.errors_by_ms.get(ms, 0) + 1

        # N2. TIMING_ATTACK_VIOLATION (CRITICAL)
        # Comparing HMAC digests with == leaks timing information that allows offline brute-force.
        # Must use hmac.compare_digest() for constant-time comparison.
        if not is_test and ("import hmac" in content or "from hmac import" in content):
            has_hmac_compute = re.search(r"hmac\.(new|digest|HMAC)\(", content)
            has_compare_digest = "compare_digest" in content
            if has_hmac_compute and not has_compare_digest:
                suspicious_eq = re.search(
                    r'\b(hash|signature|hmac_val|digest|seal|expected_hash|computed)\s*==|'
                    r'==\s*\b(hash|signature|hmac_val|digest|seal|expected_hash|computed)\b',
                    content, re.IGNORECASE
                )
                if suspicious_eq:
                    err = {
                        "file": rel_path, "severity": "CRITICAL", "ms": ms,
                        "error": (
                            "TIMING_ATTACK_VIOLATION: Direct == comparison of HMAC/cryptographic value "
                            "— use hmac.compare_digest() to prevent timing attacks"
                        )
                    }
                    self.graph["invariants_errors"].append(err)
                    self.errors_by_ms[ms] = self.errors_by_ms.get(ms, 0) + 1

        # N3. NAIVE_DATETIME_VIOLATION (WARNING)
        # datetime.utcnow() returns a naive datetime. In non-UTC timezones, .timestamp()
        # generates a future Unix timestamp → ImmatureSignatureError in JWT iat/exp claims.
        # Use datetime.now(timezone.utc) instead (Phase 162 fix).
        is_app_logic = any(p in rel_path for p in [
            "/services/", "/handlers/", "/commands/",
            "/repositories/", "/api/", "/endpoints/"
        ])
        if not is_test and is_app_logic:
            content_no_comments = re.sub(r'#[^\n]*', '', content)
            if re.search(r'datetime\.utcnow\(\)', content_no_comments):
                err = {
                    "file": rel_path, "severity": "WARNING", "ms": ms,
                    "error": (
                        "NAIVE_DATETIME_VIOLATION: datetime.utcnow() detected — "
                        "use datetime.now(timezone.utc) to prevent ImmatureSignatureError "
                        "in non-UTC deployments"
                    )
                }
                self.graph["invariants_errors"].append(err)
                self.errors_by_ms[ms] = self.errors_by_ms.get(ms, 0) + 1

        # N4. Table collection for HARD_FK_CROSS_SERVICE (post-scan, see _check_hard_fk_cross_service)
        # "First writer wins" policy: if two services claim the same __tablename__, the second
        # claimant is the violation — reported immediately. Table marked __SHARED__ so FK checks skip it.
        #
        # CROSS_DB_SHARED_TABLES: tables that legitimately exist in MULTIPLE separate databases
        # (e.g. a table that was migrated to a new service's DB but the old service DB still has a copy).
        # These are NOT Iron Wall violations — they are independent tables in different database schemas.
        CROSS_DB_SHARED_TABLES = {
            "inventory_item_variants",  # Phase 119: SSOT moved to master_data_db; inventory_db still has its own copy
        }
        if "/models/" in rel_path and ms not in ("common",) and not is_test:
            for tbl_match in re.finditer(r'__tablename__\s*=\s*["\'](\w+)["\']', content):
                tbl_name = tbl_match.group(1)
                existing_owner = self.service_tables.get(tbl_name)
                if existing_owner is None:
                    self.service_tables[tbl_name] = ms
                elif existing_owner != ms and existing_owner != "__SHARED__":
                    if tbl_name in CROSS_DB_SHARED_TABLES:
                        # Not a violation — independent copies in separate databases
                        self.service_tables[tbl_name] = "__SHARED__"
                        continue
                    err = {
                        "file": rel_path, "severity": "CRITICAL", "ms": ms,
                        "error": (
                            f"HARD_FK_CROSS_SERVICE: {ms} declares __tablename__ = '{tbl_name}' "
                            f"which is already owned by {existing_owner} — "
                            f"use HTTP or raw SQL text() to access cross-service data (Iron Wall ADR)"
                        )
                    }
                    self.graph["invariants_errors"].append(err)
                    self.errors_by_ms[ms] = self.errors_by_ms.get(ms, 0) + 1
                    self.service_tables[tbl_name] = "__SHARED__"
            self.model_files.append((file_path, ms))

        # N5. ENV_GETENV_CROSS_SERVICE (CRITICAL)
        # Inter-service client files must use settings.int_<svc>_url (injected via BaseSettings)
        # so configurations work across dev/staging/AWS without code changes.
        # Direct os.getenv() bypasses environment injection and breaks AWS Secrets Manager loading.
        is_client_file = "/infrastructure/clients/" in rel_path
        if is_client_file and not is_test:
            if re.search(r'os\.getenv\(|os\.environ(\[|\.get\()', content):
                err = {
                    "file": rel_path, "severity": "CRITICAL", "ms": ms,
                    "error": (
                        "ENV_GETENV_CROSS_SERVICE: Inter-service client uses os.getenv()/os.environ — "
                        "use settings.int_<service>_url for environment-injectable configuration "
                        "(Iron Wall ADR)"
                    )
                }
                self.graph["invariants_errors"].append(err)
                self.errors_by_ms[ms] = self.errors_by_ms.get(ms, 0) + 1

        # ── End Rev163 ─────────────────────────────────────────────────────────

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

        # 6. SQLAlchemy Auto-Reconnect Guard (Phase 4.2)
        if "database.py" in filename or "session.py" in filename:
            if "create_async_engine" in content and "pool_pre_ping=True" not in content:
                err = {"file": rel_path, "severity": "CRITICAL", "ms": ms, "error": "RESILIENCE_VIOLATION: create_async_engine lacks pool_pre_ping=True. Risk of Stale Connections during DB failover."}
                self.graph["invariants_errors"].append(err)
                self.errors_by_ms[ms] = self.errors_by_ms.get(ms, 0) + 1

        # 4. Cross-Service Import Violation Guard (Microservices Isolation)
        # CRITICAL: Direct module imports from other microservices break runtime isolation.
        # Services must communicate via HTTP only (not by importing each other's code).
        if ms in self.MICROSERVICES and not is_test:
            for imp_name, imp_module in imports.items():
                # Check for _service style imports (e.g. inventory_service.xxx)
                for other_ms in self.MICROSERVICES:
                    if other_ms == ms or other_ms == "common":
                        continue
                    # Match both 'other_service.xxx', 'other_app.xxx', and generic '[prefix]_app' patterns
                    other_app = other_ms.replace("_service", "_app")
                    generic_app = other_ms.split("_")[0] + "_app"
                    
                    if (f"{other_ms}." in imp_module or f"{other_app}." in imp_module or f"{generic_app}." in imp_module) and "common" not in imp_module:
                        # Track for graph
                        deps = self.inter_service_dependencies.get(ms, set())
                        deps.add(other_ms)
                        self.inter_service_dependencies[ms] = deps
                        # Report as CRITICAL violation
                        err = {
                            "file": rel_path,
                            "severity": "CRITICAL",
                            "ms": ms,
                            "error": (
                                f"CROSS_SERVICE_IMPORT_VIOLATION: '{ms}' directly imports from '{other_ms}' "
                                f"(module: {imp_module}). Use HTTP events instead."
                            )
                        }
                        self.graph["invariants_errors"].append(err)
                        self.errors_by_ms[ms] = self.errors_by_ms.get(ms, 0) + 1

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

        # Phase 3: CQRS Read-Only Invariant (Queries shouldn't mutate)
        if "/api/" in rel_path or "/endpoints/" in rel_path or "/routers/" in rel_path:
            if "@router.get" in source:
                if "db.commit()" in source or "session.commit()" in source or "db.add(" in source:
                    err = {"file": rel_path, "class": class_name, "method": node.name, "severity": "CRITICAL", "ms": ms, "error": "CQRS_QUERY_VIOLATION: GET endpoint performs database mutation (commit/add)."}
                    self.graph["invariants_errors"].append(err)
                    self.errors_by_ms[ms] = self.errors_by_ms.get(ms, 0) + 1

        # Phase 3: CQRS Atomic Handler Invariant (Commands must use UoW)
        # Excepciones inteligentes:
        # - auth_service: Handshakes que generan tokens no operan sobre la base de datos de transacciones de dominio fuerte, por lo que UoW es opcional.
        if class_node and "Handler" in class_node.name and node.name == "handle" and ms != "auth_service":
            if "self.session.add(" in source or "session.add(" in source or ".delete(" in source or "status =" in source:
                if "begin_nested()" not in source:
                    # Upgrade to CRITICAL: Phase 3 is completed, all Handlers must be strictly atomic
                    err = {"file": rel_path, "class": class_name, "method": node.name, "severity": "CRITICAL", "ms": ms, "error": "CQRS_ATOMICITY_VIOLATION: Command Handler mutates data without Unit of Work (begin_nested)."}
                    self.graph["invariants_errors"].append(err)
                    self.errors_by_ms[ms] = self.errors_by_ms.get(ms, 0) + 1

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
            
        # Write detailed execution log
        log_ptr = output_ptr.replace(".json", "_execution_log.txt")
        with open(log_ptr, "w", encoding="utf-8") as f:
            f.write("="*80 + "\n")
            f.write(" CODE GRAPH AUDITOR - EXECUTION LOG\n")
            f.write("="*80 + "\n\n")
            f.write(f"Total files scanned: {len(self.scanned_files_log)}\n\n")
            f.write("\n".join(sorted(self.scanned_files_log)))
            f.write("\n\n" + "="*80 + "\n")
            f.write(" AUDIT COMPLETED SUCCESSFULLY\n")
            f.write("="*80 + "\n")

class SchemaAuditor:
    """
    Audits the live Postgres schema against SQLAlchemy model definitions.
    Usage: python generate_code_graph.py --audit-schema
    Requires: CORE_DATABASE_URL in .env pointing to the target DB (use localhost:5433 for host access).
    """

    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.backend_dir = os.path.join(root_dir, "backend")

    def _setup_paths(self):
        """Add all microservice paths so models can be imported."""
        import sys
        dirs = [self.backend_dir]
        for item in os.listdir(self.backend_dir):
            p = os.path.join(self.backend_dir, item)
            if os.path.isdir(p) and not item.startswith("."):
                dirs.append(p)
        for d in dirs:
            if d not in sys.path:
                sys.path.insert(0, d)

    def _discover_models(self):
        """Import all model files and collect SQLAlchemy Table metadata."""
        from sqlalchemy.orm import DeclarativeBase
        self._setup_paths()

        # Import base to get metadata
        from common.infrastructure.models.base import Base
        
        # Walk all model files to trigger registration
        model_dirs = []
        for svc in os.listdir(self.backend_dir):
            svc_path = os.path.join(self.backend_dir, svc)
            if not os.path.isdir(svc_path):
                continue
            for sub in os.listdir(svc_path):
                sub_path = os.path.join(svc_path, sub)
                if sub == "models" and os.path.isdir(sub_path):
                    model_dirs.append((svc, sub_path))

        import importlib
        for svc, mdir in model_dirs:
            for f in os.listdir(mdir):
                if f.endswith(".py") and f != "__init__.py":
                    # Build module name relative to backend
                    app_folder = os.path.basename(os.path.dirname(mdir))
                    module_name = f"{app_folder}.models.{f[:-3]}"
                    try:
                        importlib.import_module(module_name)
                    except Exception:
                        pass
        return Base.metadata

    def run(self):
        import asyncio
        asyncio.run(self._run_async())

    async def _run_async(self):
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import inspect, text

        metadata = self._discover_models()

        # Get DB URL from settings
        from common.config import settings
        db_url = settings.DATABASE_URL
        print(f"\n{'='*80}")
        print(f"  SCHEMA AUDITOR — Comparing Models vs Live DB")
        print(f"  DB: {db_url.split('@')[-1] if '@' in db_url else db_url}")
        print(f"{'='*80}\n")

        engine = create_async_engine(db_url, echo=False)

        async with engine.connect() as conn:
            # Get live DB columns per table
            result = await conn.execute(text(
                "SELECT table_name, column_name "
                "FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name NOT LIKE 'alembic%' "
                "ORDER BY table_name, ordinal_position"
            ))
            rows = result.fetchall()

        await engine.dispose()

        db_schema: Dict[str, Set[str]] = {}
        for table_name, col_name in rows:
            db_schema.setdefault(table_name, set()).add(col_name)

        # Compare
        total_issues = 0
        tables_ok = 0
        tables_with_issues = 0

        model_tables = {t.name: {c.name for c in t.columns} for t in metadata.tables.values()}

        for table_name in sorted(model_tables.keys()):
            model_cols = model_tables[table_name]
            db_cols = db_schema.get(table_name, None)

            if db_cols is None:
                print(f"  [MISSING TABLE] {table_name}")
                print(f"     Model defines {len(model_cols)} columns but table does not exist in DB.")
                print(f"     Columns needed: {', '.join(sorted(model_cols))}")
                print()
                total_issues += 1
                tables_with_issues += 1
                continue

            missing_in_db = model_cols - db_cols
            extra_in_db = db_cols - model_cols

            if missing_in_db or extra_in_db:
                tables_with_issues += 1
                print(f"  [MISMATCH] {table_name}")
                if missing_in_db:
                    print(f"     Missing in DB : {', '.join(sorted(missing_in_db))}")
                    total_issues += len(missing_in_db)
                if extra_in_db:
                    print(f"     Extra in DB   : {', '.join(sorted(extra_in_db))}")
                print()
            else:
                tables_ok += 1

        # Tables in DB but not in models
        orphan_tables = set(db_schema.keys()) - set(model_tables.keys())
        if orphan_tables:
            print(f"  [ORPHAN TABLES] In DB but no model found:")
            for t in sorted(orphan_tables):
                print(f"     - {t}")
            print()

        print(f"{'='*80}")
        print(f"  RESULTS: {tables_ok} OK | {tables_with_issues} with issues | {total_issues} total column mismatches")
        print(f"{'='*80}")

        return total_issues


if __name__ == "__main__":
    import sys
    root = os.getcwd()

    if "--audit-schema" in sys.argv:
        auditor = SchemaAuditor(root)
        issues = auditor.run()
        sys.exit(1 if issues > 0 else 0)

    gen = CodeGraphGenerator(root)
    gen.scan()
    gen.print_report()
    gen.save(os.path.join(root, "code_graph.json"))
    
    critical_errors = [e for e in gen.graph["invariants_errors"] if e["severity"] == "CRITICAL"]
    if len(critical_errors) > 0:
        sys.exit(1)
