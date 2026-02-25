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
            "invariants_errors": []
        }
        self.nodes_by_id = {}

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

        with open(file_path, "r", encoding="utf-8") as f:
            try:
                content = f.read()
                tree = ast.parse(content)
            except Exception:
                return

        imports = self._resolve_imports(tree)
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

        # Invariant Check: Entities in app/models must be MultiTenant
        if "app/models" in file_path.replace("\\", "/") and node_type == "Entity" and not is_multitenant:
            self.graph["invariants_errors"].append({
                "file": file_path,
                "class": class_name,
                "error": "Violation: Entity does not inherit from MultiTenantBase"
            })

        metadata = {
            "name": class_name,
            "file": os.path.relpath(file_path, self.root_dir),
            "microservice": self._get_ms(file_path),
            "is_multitenant": is_multitenant
        }
        self.add_node(node_id, node_type, metadata)
        
        # Analyze dependencies within the class
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._analyze_method(node_id, item, imports)

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
        return parts[1] if parts[0] == "backend" else "common"

    def scan(self):
        for root, _, files in os.walk(self.root_dir):
            if any(x in root for x in [".git", "venv", "node_modules", "alembic"]): continue
            for file in files: self.analyze_file(os.path.join(root, file))

    def generate_training_data(self, output_path: str):
        examples = [
            {
                "instruction": "Implement a new protected endpoint in WMS for stock adjustment.",
                "context": "Microservice: wms_service, Module: inventory_core",
                "response": "from common.security.subscription_guard import SubscriptionGuard\n\n@router.post('/adjust', dependencies=[Depends(SubscriptionGuard('inventory_core'))])\nasync def adjust_stock(...):"
            },
            {
                "instruction": "Create a new multitenant entity.",
                "context": "Multitenancy DNA",
                "response": "class NewEntity(MultiTenantBase, Base):\n    __tablename__ = 'new_entities'\n    name = Column(String)"
            },
            {
                "instruction": "Add audit logging to a sensitive operation.",
                "context": "Audit Traceability",
                "response": "await AuditService.log_change(\n    db=db, company_id=id, event_type='MANUAL_CHANGE', reason='...' \n)"
            }
        ]
        with open(output_path, "w", encoding="utf-8") as f:
            for ex in examples:
                f.write(json.dumps(ex) + "\n")

    def save(self, output_ptr: str):
        with open(output_ptr, "w", encoding="utf-8") as f:
            json.dump(self.graph, f, indent=4)

if __name__ == "__main__":
    root = r"c:\API\interno"
    gen = CodeGraphGenerator(root)
    gen.scan()
    gen.save(os.path.join(root, "code_graph.json"))
    gen.generate_training_data(os.path.join(root, "training_data.jsonl"))
    print("Code Knowledge Graph and Training Data generated successfully.")
