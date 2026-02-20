# --- 1. Limpieza Profunda de Residuos ---
Write-Host "--- 1. Limpiando contenedores y volúmenes actuales ---" -ForegroundColor Cyan
# Detiene todo y borra volúmenes (-v) para limpiar la DB y carpetas corruptas
docker-compose down -v --remove-orphans

# Borra a la fuerza contenedores bloqueados en estado 'Created' o 'Exited'
Write-Host "--- Eliminando residuos de contenedores previos ---" -ForegroundColor Yellow
$containers = "auth-service-api", "interno-frontend", "interno-db"
foreach ($c in $containers) {
    docker rm -f $c 2>$null
}

# --- 2. Construcción y Despliegue ---
Write-Host "--- 2. Construyendo imágenes desde cero ---" -ForegroundColor Cyan
# Usamos -d para que corra en segundo plano
docker-compose up --build -d

# --- 3. Verificación de Salud con Reintentos ---
Write-Host "--- 3. Verificando que el backend esté RUNNING ---" -ForegroundColor Yellow
$retryCount = 0
$maxRetries = 10
$isRunning = $false

while ($retryCount -lt $maxRetries -and -not $isRunning) {
    $status = docker inspect -f '{{.State.Running}}' auth-service-api 2>$null
    if ($status -eq "true") {
        $isRunning = $true
        Write-Host "✅ Backend está encendido." -ForegroundColor Green
    } else {
        Write-Host "Wait... Reintento $($retryCount + 1)/$maxRetries" -ForegroundColor Gray
        Start-Sleep -Seconds 5
        $retryCount++
    }
}

if (-not $isRunning) {
    Write-Host "❌ ERROR: El contenedor no arrancó. Revisa 'docker logs auth-service-api'" -ForegroundColor Red
    exit
}

# --- 4. Población de Datos (Seed) ---
Write-Host "--- 4. Poblando la base de datos real ---" -ForegroundColor Cyan
# Intentamos ejecutar el seed
docker exec -it auth-service-api python /app/seed_db.py

# --- FINALIZACIÓN ---
Write-Host "`n--- PROCESO COMPLETADO ---" -ForegroundColor Green
Write-Host "Verifica el estado con: docker ps" -ForegroundColor Gray
Write-Host "Accede a: http://localhost" -ForegroundColor White