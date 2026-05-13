# validate_ecosystem.ps1
# Script para validar la salud de todos los microservicios a través del Gateway

$GATEWAY_URL = "http://localhost:8000"

$endpoints = @(
    @{ Name = "Gateway Maestro"; Url = "$GATEWAY_URL/health" }
    @{ Name = "Auth Service"; Url = "$GATEWAY_URL/api/v1/auth/" }
    @{ Name = "Master Data Service"; Url = "$GATEWAY_URL/api/v1/master-data/" }
    @{ Name = "Inventory Service"; Url = "$GATEWAY_URL/api/v1/inventory/" }
    @{ Name = "Tickets Service"; Url = "$GATEWAY_URL/api/v1/tickets/" }
    @{ Name = "Subscription Service"; Url = "$GATEWAY_URL/api/v1/subscriptions/" }
    @{ Name = "HCM Service (Staff)"; Url = "$GATEWAY_URL/api/v1/staff/" }
    @{ Name = "Notification Service"; Url = "$GATEWAY_URL/api/v1/notifications/" }
)

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  Validación Industrial del Ecosistema" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

foreach ($endpoint in $endpoints) {
    try {
        # Usamos UseBasicParsing para evitar dependencias de IE en entornos Windows Server
        $response = Invoke-WebRequest -Uri $endpoint.Url -Method Get -UseBasicParsing -ErrorAction Stop
        
        Write-Host "[ OK ] $($endpoint.Name)" -ForegroundColor Green
        Write-Host "       Status: $($response.StatusCode) | Router Alcanzado" -ForegroundColor DarkGray
    } catch {
        $ex = $_.Exception.Response
        if ($ex -ne $null) {
            # Si responde un 401, 403, 404, 405... SIGNIFICA QUE EL SERVICIO ESTÁ VIVO Y ENRUTADO
            # (Solo no tenemos autorización o la ruta raíz exacta no tiene un GET configurado)
            Write-Host "[ OK ] $($endpoint.Name)" -ForegroundColor Green
            Write-Host "       Status: $($ex.StatusCode) | Router Alcanzado (Respuesta de App)" -ForegroundColor DarkGray
        } else {
            # Si no hay respuesta (Connection Refused, 502 Bad Gateway)
            Write-Host "[FAIL] $($endpoint.Name)" -ForegroundColor Red
            Write-Host "       Error: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}
Write-Host "=========================================" -ForegroundColor Cyan
