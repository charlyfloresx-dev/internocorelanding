Write-Host "--- 1. Deteniendo todos los contenedores ---" -ForegroundColor Cyan
docker stop $(docker ps -aq) 2>$null

Write-Host "--- 2. Eliminando contenedores, redes y huérfanos ---" -ForegroundColor Cyan
# El flag -v borra los volúmenes (la base de datos se reseteará) [cite: 2026-01-20]
docker-compose down -v --remove-orphans

Write-Host "--- 3. Eliminando TODAS las imágenes (Limpieza profunda) ---" -ForegroundColor Yellow
# Esto obliga a que mañana el 'apt-get' se ejecute desde cero sin caché corrupta [cite: 2026-01-20]
docker rmi -f $(docker images -aq) 2>$null

Write-Host "--- 4. Limpiando volúmenes residuales ---" -ForegroundColor Yellow
docker volume prune -f

Write-Host "--- 5. Limpiando redes residuales ---" -ForegroundColor Yellow
docker network prune -f

Write-Host "--- 6. RESET MAESTRO DE CACHÉ DE BUILD ---" -ForegroundColor Red
# Esto elimina cualquier rastro del error 100 de apt-get [cite: 2026-01-20]
docker builder prune -a -f

Write-Host "`n✅ SISTEMA LIMPIO. Mañana empezamos desde cero." -ForegroundColor Green