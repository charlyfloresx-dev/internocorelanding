$authUrl = "http://localhost:8001"
$wmsUrl = "http://localhost:8002"

# --- 1. LOGIN DE USUARIO ---
Write-Host "🔐 [PASO 1] Iniciando sesión..." -ForegroundColor Cyan
$loginBody = @{
    email    = "admin@interno.com"
    password = "admin123456"
} | ConvertTo-Json

try {
    $userTokenResponse = Invoke-RestMethod -Method Post `
        -Uri "$authUrl/api/v1/auth/login" `
        -Body $loginBody `
        -ContentType "application/json"

    $userToken = $userTokenResponse.data.access_token
    $availableCompanies = $userTokenResponse.data.companies
    
    Write-Host "✅ Login exitoso!" -ForegroundColor Green
    Write-Host "🎫 User Token: $($userToken.Substring(0, 20))..." -ForegroundColor Gray
    Write-Host "🏢 Empresas encontradas: $($availableCompanies.Count)" -ForegroundColor Gray
}
catch {
    Write-Host "❌ Error en Login: $($_.Exception.Message)" -ForegroundColor Red
    return
}

# --- 2. SELECCIÓN DE EMPRESA ---
if ($availableCompanies.Count -eq 0) {
    Write-Host "❌ No hay empresas asociadas." -ForegroundColor Red
    return
}

$selectedCompanyId = $availableCompanies[0].company_id
if (-not $selectedCompanyId) { $selectedCompanyId = $availableCompanies[0].id }
$companyName = $availableCompanies[0].company_name
if (-not $companyName) { $companyName = $availableCompanies[0].name }

Write-Host "🏢 [PASO 2] Seleccionando: $companyName ($selectedCompanyId)" -ForegroundColor Cyan

$selectBody = @{ company_id = [string]$selectedCompanyId } | ConvertTo-Json
$selectCompanyHeaders = @{ 
    "Authorization" = "Bearer $userToken"
    "Content-Type"  = "application/json"
}

try {
    $finalTokenResponse = Invoke-RestMethod -Method Post `
        -Uri "$authUrl/api/v1/auth/select-company/$selectedCompanyId" `
        -Headers $selectCompanyHeaders `
        -Body $selectBody

    $finalToken = $finalTokenResponse.data.access_token
    Write-Host "✅ Empresa seleccionada!" -ForegroundColor Green
    Write-Host "🎫 Final Token (con Company ID): $($finalToken.Substring(0, 20))..." -ForegroundColor Gray
}
catch {
    Write-Host "❌ Error al seleccionar empresa." -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        Write-Host "Detalle: $($reader.ReadToEnd())" -ForegroundColor Yellow
    }
    return
}

# --- 3. CONSUMO DE WMS ---
Write-Host "📦 [PASO 3] Sincronizando en WMS..." -ForegroundColor Cyan

$payload = @{
    products = @(
        @{
            id = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
            sku = "IPHONE-13-PRO"
            name = "iPhone 13 Pro"
            versions = @( @{ version_number = 1 } )
        }
    )
} | ConvertTo-Json -Depth 5

$wmsHeaders = @{ 
    "Authorization" = "Bearer $finalToken"
    "Content-Type"  = "application/json"
}

try {
    $response = Invoke-RestMethod -Method Post `
        -Uri "$wmsUrl/api/v1/inventory/sync-initial" `
        -Headers $wmsHeaders `
        -Body $payload

    Write-Host "🚀 Sincronización Exitosa para $companyName" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 5 | Write-Host
}
catch {
    Write-Host "❌ Error en WMS: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        Write-Host "Detalle WMS: $($reader.ReadToEnd())" -ForegroundColor Yellow
    }
}
