# Script de Modo Offline - Interno Moments
# Este script libera el puerto 53 y activa el servidor DNS local.

Write-Host "--- Activando MODO OFFLINE ---" -ForegroundColor Cyan

# 1. Liberar el puerto 53
Write-Host "Deteniendo servicio SharedAccess para liberar el puerto 53..." -ForegroundColor Yellow
Stop-Service -Name "SharedAccess" -Force -ErrorAction SilentlyContinue

# 2. Lanzar el servidor DNS en segundo plano (job)
Write-Host "Lanzando Servidor DNS para momentos.com..." -ForegroundColor Green
$dnsJob = Start-Job -ScriptBlock { 
    python c:\API\interno\scripts\dns_server.py 
}

Write-Host "--------------------------------------------------------"
Write-Host "✅ SISTEMA LISTO PARA PRUEBAS OFFLINE" -ForegroundColor Green
Write-Host "1. Configura el DNS de tu celular a la IP de esta PC."
Write-Host "2. Entra a https://momentos.com en tu celular."
Write-Host "--------------------------------------------------------"
Write-Host "Presiona cualquier tecla para DETENER la prueba y RESTAURAR Windows..." -ForegroundColor Magenta

# Esperar entrada del usuario
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# 3. Restaurar Servicios
Write-Host "`nRestaurando sistema..." -ForegroundColor Yellow
Stop-Job $dnsJob
Remove-Job $dnsJob
Start-Service -Name "SharedAccess" -ErrorAction SilentlyContinue

Write-Host "✅ Windows restaurado a la normalidad. Modo Online activo." -ForegroundColor Green
