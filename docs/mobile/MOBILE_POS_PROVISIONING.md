# InternoCore: Mobile POS Provisioning & Setup Guide

This guide details the industrial provisioning flow (Zero-Trust) and the technical setup required to deploy the Mobile POS application on an Android Emulator or physical device.

## 1. Zero-Trust Provisioning Flow (QR Handshake)

The Mobile POS application follows an industrial "Handshake" protocol to eliminate manual configuration friction for operators.

### How it works:
1.  **Web Admin Login**: An administrator logs into the InternoCore web portal.
2.  **Generate Link QR**: From the User Menu, select **"Vincular POS"**.
3.  **Scan from Mobile**: The Mobile app, when in a clean state or triggered via "Setup Mode", scans the QR.
4.  **Auto-Provisioning**: The app automatically configures:
    *   `baseUrl`: Target API server.
    *   `accessToken`: Inherited session token.
    *   `companyId`: Current tenant context.
    *   `warehouseId`: Default operational warehouse.

## 2. Technical Setup: Android Emulator (AVD)

To test the application locally, follow these steps to prepare the Android Virtual Device.

### Installation (via Android Studio)
1.  Open **Android Studio**.
2.  Navigate to **Virtual Device Manager**.
3.  Click **Create Device** and select a modern profile (e.g., Pixel 7/8).
4.  **System Image**: Select "UpsideDownCake" (API 34) or "VanillaIceCream" (API 35).
5.  **Name**: Assign a name (e.g., `Interno_POS_Emu`).

### Launching via Terminal (PowerShell)
```powershell
# List available AVDs
& "C:\Users\$env:USERNAME\AppData\Local\Android\Sdk\tools\bin\avdmanager.list" avd

# Start the emulator
& "C:\Users\$env:USERNAME\AppData\Local\Android\Sdk\emulator\emulator.exe" -avd Interno_POS_Emu
```

## 3. Running the App
1.  Ensure the emulator is active.
2.  Navigate to the app directory: `cd C:\API\interno\interno_billing_app`.
3.  Verify the device is detected: `flutter devices`.
4.  Run the app: `flutter run`.

> [!IMPORTANT]
> **Network Tip**: If your backend is running on `localhost:8000`, the emulator must use the special IP **`http://10.0.2.2:8000`** to reach the host machine.

## 4. Simulating Scans in the Emulator

Since the emulator lacks a physical camera for scanning your monitor, use these methods:

### Method A: Virtual Scene
Enable **"VirtualScene"** in the emulator's camera settings. You can navigate the 3D scene using WASD to find posters with barcodes.

### Method B: ADB Injection (Fastest for Handshake)
To simulate a QR scan result without using the camera, use the following `adb` command:
```powershell
adb shell am broadcast -a com.google.zxing.client.android.SCAN --es SCAN_RESULT "YOUR_QR_JSON_DATA"
```

## 5. Production Build (APK)
To generate the final installer for ruggedized industrial devices or real smartphones:
```powershell
flutter build apk --release
```
**Output Path**: `build\app\outputs\flutter-apk\app-release.apk`
