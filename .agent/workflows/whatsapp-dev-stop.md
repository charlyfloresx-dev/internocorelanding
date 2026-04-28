# InternoCore: WhatsApp Dev Stop Protocol

Usa este flujo para detener todos los servicios de desarrollo de notificaciones y liberar los puertos.

## Detener Todo (One-Click)
Este comando buscará y terminará los procesos de Uvicorn y Localtunnel.
// turbo
```powershell
# Detener Uvicorn
Get-Process | Where-Object { $_.ProcessName -eq "uvicorn" -or $_.CommandLine -like "*app.main:app*" } | Stop-Process -Force -ErrorAction SilentlyContinue

# Detener Localtunnel (Node)
Get-Process | Where-Object { $_.ProcessName -eq "node" -and $_.CommandLine -like "*localtunnel*" } | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host "--- Entorno de WhatsApp Detenido y Puertos Liberados ---" -ForegroundColor Green
```

## Método Manual
Si el comando anterior no funciona, simplemente ve a las terminales activas y presiona:
*   **Ctrl + C** en la terminal de Uvicorn.
*   **Ctrl + C** en la terminal de Localtunnel.

## Verificación
Para asegurarte de que el puerto 8000 está libre:
```powershell
netstat -ano | findstr :8000
```
*(Si no sale nada, el puerto está libre).*
