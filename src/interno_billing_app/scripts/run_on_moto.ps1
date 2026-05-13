# Script to run INTERNO POS on Motorola Moto g04s
# Last Updated: 2026-05-12

$DEVICE_ID = "adb-ZL7324NDXD-e2sm8j._adb-tls-connect._tcp"
$LOCAL_IP = "192.168.1.146"

Write-Host "--- Launching INTERNO POS on Moto g04s ---" -ForegroundColor Cyan
Write-Host "Local IP: $LOCAL_IP" -ForegroundColor Yellow
Write-Host "Backend URL should be: http://$LOCAL_IP:8000" -ForegroundColor Yellow
Write-Host ""

# Ensure we are in the right directory
if (!(Test-Path "pubspec.yaml")) {
    Write-Host "Error: Run this script from the src/interno_billing_app directory." -ForegroundColor Red
    exit
}

Write-Host "Step 1: Fetching dependencies..." -ForegroundColor Gray
flutter pub get

Write-Host "Step 2: Checking device connection..." -ForegroundColor Gray
$devices = flutter devices | Select-String $DEVICE_ID
if ($devices) {
    Write-Host "Device detected: Moto g04s" -ForegroundColor Green
} else {
    Write-Host "Warning: Device $DEVICE_ID not detected by flutter devices." -ForegroundColor Yellow
    Write-Host "Attempting to run anyway (it might be using a different ID)..." -ForegroundColor Gray
}

Write-Host "Step 3: Running application..." -ForegroundColor Gray
flutter run -d $DEVICE_ID --debug
