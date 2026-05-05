import os
import glob
import markdown
import re

ROOT_DIR = r"c:\API\interno"
HTML_FILE = os.path.join(ROOT_DIR, "docs", "DOCS_INTERNOCORE.html")

TARGET_FILES = [
    os.path.join(ROOT_DIR, "REPO_LOG.md"),
    os.path.join(ROOT_DIR, "FrontendIA.md"),
]

# Recolectar archivos de docs
for root, dirs, files in os.walk(os.path.join(ROOT_DIR, "docs")):
    for file in files:
        if file.endswith(".md"):
            TARGET_FILES.append(os.path.join(root, file))

# Recolectar SERVICE_LOG.md y otros .md importantes de los microservicios
for root, dirs, files in os.walk(os.path.join(ROOT_DIR, "backend")):
    if "venv" in root or "__pycache__" in root:
        continue
    for file in files:
        if file.endswith(".md"):
            TARGET_FILES.append(os.path.join(root, file))

# Recolectar archivos de frontend/docs
for root, dirs, files in os.walk(os.path.join(ROOT_DIR, "frontend")):
    if "node_modules" in root or "dist" in root:
        continue
    for file in files:
        if file.endswith(".md"):
            TARGET_FILES.append(os.path.join(root, file))

categories = {
    "Global Logs": [],
    "Project Phases": [],
    "Microservices": [],
    "Frontend": [],
    "General Docs": []
}

# Categorizar archivos
for file_path in TARGET_FILES:
    if not os.path.exists(file_path):
        continue
    
    rel_path = os.path.relpath(file_path, ROOT_DIR)
    
    if "REPO_LOG.md" in rel_path or "FrontendIA.md" in rel_path:
        categories["Global Logs"].append(file_path)
    elif "docs\\historial" in rel_path:
        categories["Project Phases"].append(file_path)
    elif "backend\\" in rel_path:
        categories["Microservices"].append(file_path)
    elif "frontend\\" in rel_path:
        categories["Frontend"].append(file_path)
    else:
        categories["General Docs"].append(file_path)

html_content = ""

for cat_name, files in categories.items():
    if not files:
        continue
        
    cat_html = ""
    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                md_text = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, "r", encoding="latin-1") as f:
                    md_text = f.read()
            except Exception:
                continue
        except Exception:
            continue
            
        rel_path = os.path.relpath(file_path, ROOT_DIR)
        file_name = os.path.basename(file_path)
        
        # Convertir a HTML
        html_rendered = markdown.markdown(md_text, extensions=['fenced_code', 'tables'])
        
        # Sub-acordeón para cada archivo
        cat_html += f"""
        <details class="doc-sub-accordion">
            <summary>{file_name} <span class="path-badge">{rel_path}</span></summary>
            <div class="doc-content">
                {html_rendered}
            </div>
        </details>
        """
    
    # Contenedor para la categoría
    html_content += f"""
    <div class="category-group">
        <h3 class="category-title">{cat_name}</h3>
        {cat_html}
    </div>
    """

# Leer HTML original
with open(HTML_FILE, "r", encoding="utf-8") as f:
    base_html = f.read()

# CSS para el acordeón y categorías
doc_css = """
        /* --- Documentation Hub --- */
        .category-group {
            margin-bottom: 3rem;
            padding: 2rem;
            background: rgba(255, 255, 255, 0.01);
            border-radius: 20px;
            border: 1px solid var(--glass-border);
        }
        .category-title {
            font-size: 1.8rem;
            color: var(--primary);
            margin-bottom: 2rem;
            text-transform: uppercase;
            letter-spacing: 2px;
            border-bottom: 2px solid var(--primary-glow);
            padding-bottom: 0.5rem;
        }
        .doc-sub-accordion {
            background: var(--bg-card);
            border: 1px solid var(--glass-border);
            border-radius: 12px;
            margin-bottom: 0.75rem;
            overflow: hidden;
        }
        .doc-sub-accordion summary {
            padding: 1rem 1.5rem;
            font-size: 1rem;
            font-weight: 600;
            color: #fff;
            cursor: pointer;
            list-style: none;
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(255, 255, 255, 0.02);
        }
        .doc-sub-accordion summary:hover {
            background: rgba(0, 209, 255, 0.05);
            color: var(--primary);
        }
        .path-badge {
            font-size: 0.7rem;
            color: var(--text-dim);
            font-family: monospace;
            background: rgba(255,255,255,0.05);
            padding: 2px 8px;
            border-radius: 4px;
        }
        .doc-content {
            padding: 2rem;
            border-top: 1px solid var(--glass-border);
            font-size: 0.95rem;
            color: var(--text-dim);
            line-height: 1.8;
            max-height: 600px;
            overflow-y: auto;
        }
        .doc-content h1, .doc-content h2, .doc-content h3 {
            color: #fff;
            margin: 1.5rem 0 1rem 0;
            font-family: 'Outfit', sans-serif;
            -webkit-text-fill-color: initial;
            background: none;
        }
        .doc-content pre { background: #010409; padding: 1.5rem; border-radius: 8px; overflow-x: auto; border: 1px solid var(--glass-border); }
        .doc-content code { background: rgba(255, 255, 255, 0.1); padding: 0.2rem 0.4rem; border-radius: 4px; }
        .doc-content table { width: 100%; border-collapse: collapse; margin: 1rem 0; }
        .doc-content th, .doc-content td { padding: 0.75rem; border: 1px solid var(--glass-border); }
"""

# Inyectar CSS
if "/* --- Documentation Hub --- */" not in base_html:
    base_html = base_html.replace("</style>", doc_css + "\n    </style>")

# Inyectar Link en Sidebar
sidebar_link = '<li><a href="#doc-hub"><i class="fas fa-book"></i> Documentation Hub</a></li>'
if sidebar_link not in base_html:
    base_html = base_html.replace('<li><a href="#stack"><i class="fas fa-code-branch"></i> Core Stack</a></li>', 
                                  '<li><a href="#stack"><i class="fas fa-code-branch"></i> Core Stack</a></li>\n                ' + sidebar_link)

# Generar la sección completa
new_section = f"""
            <!-- Documentation Hub -->
            <section id="doc-hub" class="visible">
                <div class="badge">Knowledge Base</div>
                <h2>Documentation Hub</h2>
                <p class="lead">
                    Archivo consolidado de diseño arquitectónico y bitácoras operacionales de InternoCore, organizado por categorías estratégicas.
                </p>
                {html_content}
            </section>
"""

# Remover sección antigua si existe
if '<section id="doc-hub"' in base_html:
    import re
    base_html = re.sub(r'<!-- Documentation Hub -->.*?</section>', '', base_html, flags=re.DOTALL)

# Inyectar sección antes de Conclusion
base_html = base_html.replace('<!-- Conclusion -->', new_section + '\n            <!-- Conclusion -->')

# Ajustar threshold del IntersectionObserver para secciones largas
base_html = base_html.replace('const options = { threshold: 0.15 };', 'const options = { threshold: 0.01 };')

with open(HTML_FILE, "w", encoding="utf-8") as f:
    f.write(base_html)

print("DOCS_INTERNOCORE.html updated successfully with all Markdown documentation.")
