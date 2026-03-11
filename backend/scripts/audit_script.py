import os
import re
import json
import ast
from pathlib import Path

def read_file_safe(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        try:
            with open(path, 'r', encoding='utf-8-sig') as f:
                return f.read()
        except:
             with open(path, 'r', encoding='latin-1', errors='replace') as f:
                 return f.read()

def main():
    base_dir = Path(r"c:\API\interno")
    backend_dir = base_dir / "backend"
    
    # 1. Check for root pollution
    pollution_issues = []
    
    services = [d for d in os.listdir(backend_dir) if (backend_dir / d).is_dir() and d.endswith('_service')]
    
    for root_dir in [backend_dir] + [backend_dir / s for s in services]:
        if not root_dir.exists(): continue
        for f in os.listdir(root_dir):
            if f.endswith('.py') and os.path.isfile(root_dir / f) and f != '__init__.py':  # Let's ignore __init__.py
                pollution_issues.append(f"{root_dir.name}/{f}")
                    
    # 2. Duplicate models and Governance (Inheritance)
    model_paths = {} # name -> list of paths
    governance_issues = []
    
    for service in services:
        models_dir = backend_dir / service / "app" / "models"
        if not models_dir.exists():
            continue
            
        for root, dirs, files in os.walk(models_dir):
            for f in files:
                if f.endswith('.py') and f != '__init__.py':
                    path = Path(root) / f
                    
                    name = f[:-3].lower()
                    if name not in model_paths:
                        model_paths[name] = []
                    model_paths[name].append(str(path))
                    
                    content = read_file_safe(path)
                            
                    try:
                        tree = ast.parse(content)
                        has_multitenant = False
                        is_model = False
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ClassDef):
                                is_model = True
                                for base in node.bases:
                                    if isinstance(base, ast.Name) and base.id == 'MultiTenantBase':
                                        has_multitenant = True
                                    elif isinstance(base, ast.Attribute) and base.attr == 'MultiTenantBase':
                                        has_multitenant = True
                        
                        if is_model and not has_multitenant:
                            governance_issues.append(str(path))
                    except:
                        pass
                        
    duplicates = {name: paths for name, paths in model_paths.items() if len(paths) > 1}
    
    # 3. Read REPO_LOG.md
    repo_log_path = base_dir / "REPO_LOG.md"
    content = read_file_safe(repo_log_path)
        
    fase_7_info = "Content not found"
    fase_matches = list(re.finditer(r'(?i)(fase\s*7)', content))
    if fase_matches:
        start_idx = fase_matches[0].start()
        # extract till next markdown header
        rest = content[start_idx:]
        end_idx = rest.find('\n#')
        if end_idx != -1:
            fase_7_info = rest[:end_idx]
        else:
            fase_7_info = rest[:2000]
    else:
        fase_matches = list(re.finditer(r'(?i)(phase\s*7)', content))
        if fase_matches:
            start_idx = fase_matches[0].start()
            rest = content[start_idx:]
            end_idx = rest.find('\n#')
            if end_idx != -1:
                fase_7_info = rest[:end_idx]
            else:
                fase_7_info = rest[:2000]
    
    # 4. Check migrations cross-reference
    # The prompt asks: "confirma si las migraciones de Alembic en master_data_service y wms_service coinciden con lo documentado."
    # Let's check alembic/versions in those services
    def count_migrations(srv):
        p = backend_dir / srv / "alembic" / "versions"
        if not p.exists(): return 0
        return len([x for x in os.listdir(p) if x.endswith('.py')])
    
    mds_mig = count_migrations("master_data_service")
    wms_mig = count_migrations("wms_service")
    
    doc_discrepancy = []
    
    # Check code_graph.json
    graph_path = base_dir / "code_graph.json"
    content = read_file_safe(graph_path)
    invariants_errors = []
    try:
        data = json.loads(content)
        invariants_errors = data.get("invariants_errors", [])
    except Exception as e:
        invariants_errors = [f"Error reading code graph: {e}"]
        
    out = []
    out.append("================ REPORT ================")
    for service in services:
        out.append(f"\nSERVICIO: {service}")
        
        # Discrepancy logic for specific services mentioned in prompt
        if service == 'master_data_service':
            if str(mds_mig) in fase_7_info or 'master_data' in fase_7_info.lower():
                out.append(f"DISCREPANCIA: REPO_LOG documenta Fase 7. Código tiene {mds_mig} migraciones de Alembic. Revisión manual: {mds_mig > 0}")
            else:
                out.append(f"DISCREPANCIA: REPO_LOG no detalla claramente migraciones para master_data_service en Fase 7, o el código tiene {mds_mig} y no está alineado.")
        elif service == 'wms_service':
            if str(wms_mig) in fase_7_info or 'wms_service' in fase_7_info.lower():
                 out.append(f"DISCREPANCIA: REPO_LOG documenta Fase 7. Código tiene {wms_mig} migraciones de Alembic. Revisión manual: {wms_mig > 0}")
            else:
                 out.append(f"DISCREPANCIA: REPO_LOG no detalla claramente migraciones para wms_service en Fase 7, o el código tiene {wms_mig} y no está alineado.")
        else:
             out.append("DISCREPANCIA: N/A - Fase 7 focus is mainly master_data/wms")
        
        service_zombies = []
        for name, paths in duplicates.items():
            for p in paths:
                if service in p:
                    service_zombies.append((name, paths))
        if service_zombies:
            out.append("ZOMBIE CODE: ")
            for name, paths in service_zombies:
                out.append(f"  - {name} duplicado en: {', '.join([Path(x).as_posix() for x in paths])}")
        else:
            out.append("ZOMBIE CODE: Ninguno")
            
        svc_gov = [p for p in governance_issues if service in p]
        if svc_gov:
            out.append("ESTADO DE GOBERNANZA: FAILED - Faltan MultiTenantBase en:")
            for p in svc_gov:
                out.append(f"  - {Path(p).as_posix()}")
        else:
            out.append("ESTADO DE GOBERNANZA: PASSED")

    out.append("\n================ RESUMEN ROOT POLLUTION ================")
    out.append("\n".join(pollution_issues) if pollution_issues else "Ninguno")
    
    out.append("\n================ INVARIANTS ERRORS DE CODE GRAPH ================")
    if invariants_errors:
        for err in invariants_errors:
            out.append(str(err))
    else:
        out.append("No reportados en invariants_errors list")

    with open(backend_dir / 'scripts' / 'audit_report.txt', 'w', encoding='utf-8') as f:
        f.write("\n".join(out))

if __name__ == '__main__':
    main()
