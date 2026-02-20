# consolidate_repo.ps1
Write-Host "--- INICIANDO SPRING CLEANING & CONSOLIDATION ---" -ForegroundColor Cyan

# 1. Crear directorios destino
$dirs = @(
    "docs/architecture",
    "docs/audits",
    "infrastructure/aws/policies",
    "scripts/automation"
)
foreach ($d in $dirs) {
    if (-not (Test-Path $d)) { New-Item -ItemType Directory -Force -Path $d | Out-Null }
}

# 2. Mover Archivos de Arquitectura (.md)
$arch_files = @(
    "BACKEND_CONTEXT.md", "LOGGING_PROTOCOL.md", "CONTEXT_STATE.md", 
    "CONTEXT_UNIFICATION.md", "ARCHITECTURAL_DECISIONS.md", "AWS_MANAGEMENT.md",
    "MES_CORE.md"
)
foreach ($f in $arch_files) {
    if (Test-Path $f) { Move-Item -Path $f -Destination "docs/architecture/" -Force; Write-Host "Movido a docs/architecture: $f" -ForegroundColor Yellow }
}

# 3. Mover Auditorías
$audit_files = @("DOC_AUDITORIA_ESTADO.md")
foreach ($f in $audit_files) {
    if (Test-Path $f) { Move-Item -Path $f -Destination "docs/audits/" -Force; Write-Host "Movido a docs/audits: $f" -ForegroundColor Yellow }
}

# 4. Mover Políticas AWS (.json)
$aws_files = @("global.json", "policy.json", "s3-policy.json", "website.json")
foreach ($f in $aws_files) {
    if (Test-Path $f) { Move-Item -Path $f -Destination "infrastructure/aws/policies/" -Force; Write-Host "Movido a infrastructure/aws/policies: $f" -ForegroundColor Yellow }
}

# 5. Mover Scripts (.ps1, .py)
$script_files = @(
    "nuke_docker.ps1", "setup_demo.ps1", "generate_mock_jsons.py", 
    "debug_psycopg2.py", "run_wms_dev.py", "organize_root.ps1"
)
foreach ($f in $script_files) {
    if (Test-Path $f) { Move-Item -Path $f -Destination "scripts/automation/" -Force; Write-Host "Movido a scripts/automation: $f" -ForegroundColor Yellow }
}

# 6. Eliminar Basura
if (Test-Path "frontend.zip") { Remove-Item "frontend.zip" -Force; Write-Host "Eliminado: frontend.zip" -ForegroundColor Red }

# 7. Auto-movimiento del script actual
$current_script = "consolidate_repo.ps1"
if (Test-Path $current_script) {
    Move-Item -Path $current_script -Destination "scripts/automation/" -Force
    Write-Host "Movido a scripts/automation: $current_script" -ForegroundColor Yellow
}

Write-Host "--- CONSOLIDACIÓN COMPLETADA ---" -ForegroundColor Green