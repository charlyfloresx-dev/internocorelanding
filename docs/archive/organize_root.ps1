# organize_root.ps1

Write-Host "--- INICIANDO REORGANIZACIÓN DE RAÍZ ---" -ForegroundColor Cyan

# 1. Creación de Estructura de Directorios
$dirs = @(
    "docs",
    "docs/logs_archive",
    "scripts",
    "infrastructure/aws/policies",
    "assets/builds"
)

foreach ($d in $dirs) {
    if (-not (Test-Path $d)) {
        New-Item -ItemType Directory -Force -Path $d | Out-Null
        Write-Host "Creado directorio: $d" -ForegroundColor Green
    }
}

# 2. Mover Documentación a /docs
$docs_files = @(
    "ARCHITECTURAL_DECISIONS.md",
    "BACKEND_CONTEXT.md",
    "CONTEXT_STATE.md",
    "CONTEXT_UNIFICATION.md",
    "LOGGING_PROTOCOL.md",
    "DOC_AUDITORIA_ESTADO.md",
    "INTERNOCORE_MASTER.md"
)

# Mover también versiones anteriores de INTERNOCORE_MASTER si existen
$master_versions = Get-ChildItem -Path . -Filter "INTERNOCORE_MASTER*.md" -ErrorAction SilentlyContinue
foreach ($m in $master_versions) {
    if ($docs_files -notcontains $m.Name) {
        $docs_files += $m.Name
    }
}

foreach ($file in $docs_files) {
    if (Test-Path $file) {
        Move-Item -Path $file -Destination "docs/" -Force
        Write-Host "Movido a /docs: $file" -ForegroundColor Yellow
    }
}

# 3. Mover Scripts a /scripts (Raíz)
$scripts_files = @(
    "nuke_docker.ps1",
    "setup_demo.ps1",
    "generate_mock_jsons.py",
    "debug_psycopg2.py",
    "run_wms_dev.py"
)

foreach ($file in $scripts_files) {
    if (Test-Path $file) {
        Move-Item -Path $file -Destination "scripts/" -Force
        Write-Host "Movido a /scripts: $file" -ForegroundColor Yellow
    }
}

# 4. Limpieza de Configuración y Basura
# Frontend Zip
if (Test-Path "frontend.zip") {
    Move-Item -Path "frontend.zip" -Destination "assets/builds/" -Force
    Write-Host "Movido frontend.zip a assets/builds/" -ForegroundColor Yellow
}

# AWS Policies
$policy_files = @("global.json", "policy.json", "s3-policy.json", "website.json")
foreach ($file in $policy_files) {
    if (Test-Path $file) {
        Move-Item -Path $file -Destination "infrastructure/aws/policies/" -Force
        Write-Host "Movido a policies: $file" -ForegroundColor Yellow
    }
}

# Entities.py (Eliminación)
if (Test-Path "entities.py") {
    Remove-Item -Path "entities.py" -Force
    Write-Host "ELIMINADO: entities.py" -ForegroundColor Red
}

Write-Host "--- REORGANIZACIÓN COMPLETADA ---" -ForegroundColor Green