# Script de Arranque Automatico para Interno Core Kiosk
# Detecta la IP local y levanta el ecosistema Docker.

Write-Host "--- Detectando IP local ---" -ForegroundColor Cyan

# 1. Buscar IP de Wi-Fi
$lanIp = (Get-NetIPAddress -InterfaceAlias 'Wi-Fi' -AddressFamily IPv4 -ErrorAction SilentlyContinue).IPAddress

if (-not $lanIp) {
    Write-Host "No se detecto Wi-Fi, intentando Ethernet..." -ForegroundColor Yellow
    $lanIp = (Get-NetIPAddress -InterfaceAlias 'Ethernet' -AddressFamily IPv4 -ErrorAction SilentlyContinue).IPAddress
}

if (-not $lanIp) {
    Write-Host "No se detecto red LAN. Usando localhost." -ForegroundColor Red
    $lanIp = "localhost"
} else {
    Write-Host "IP Detectada: $lanIp" -ForegroundColor Green
}

# 2. Configurar variable de entorno
$env:CORE_KIOSK_LAN_IP = $lanIp

# 3. Levantar Docker
Write-Host "Levantando Microservicios..." -ForegroundColor Magenta
docker compose -f ../docker/docker-compose.kiosk.yml up -d

Write-Host "--------------------------------------------------------"
Write-Host "Ecosistema Listo." -ForegroundColor Green
Write-Host "IP de Red: $lanIp"
Write-Host "--------------------------------------------------------"
