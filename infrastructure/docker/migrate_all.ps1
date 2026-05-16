# InternoCore: Unified Migration Script (Microservices Mode)
# This script runs alembic migrations for all active microservices.

$services = @(
    "interno-auth-dev",
    "interno-master-data-dev",
    "interno-inventory-dev",
    "interno-wms-service-dev",
    "interno-hcm-dev"
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🚀 InternoCore Unified Migration Sweep" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

foreach ($service in $services) {
    Write-Host "`n>> Processing migrations for: $service" -ForegroundColor Yellow
    
    # Check if container is running
    $status = docker inspect -f '{{.State.Running}}' $service 2>$null
    
    if ($status -eq "true") {
        Write-Host "   Container is UP. Running Alembic..." -ForegroundColor Gray
        docker exec $service python -m alembic upgrade head
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ Migrations applied successfully." -ForegroundColor Green
        } else {
            Write-Host "   ❌ Migration failed for $service." -ForegroundColor Red
        }
    } else {
        Write-Host "   ⚠️  Container $service is NOT running. Skipping." -ForegroundColor DarkYellow
    }
}

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "🏁 Migration Sweep Complete." -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
