---
description: Run Interno Billing App on Physical Android Device
---

This workflow guides you through deploying and running **INTERNO POS** on a physical Android device (e.g., Moto g04s) for industrial testing.

### 1. Prerequisites
- **USB Debugging:** Enabled on the device (Developer Options).
- **USB Connection:** Device connected via USB and authorized.
- **Same Network:** Phone and Computer must be on the same Wi-Fi.

### 2. Verify Connection
Run this command to ensure the device is detected:
```powershell
flutter devices
```

### 3. Configure API IP
The app needs to connect to the backend running on your computer. 
1. Get your Local IP:
   ```powershell
   ipconfig | findstr "IPv4"
   ```
2. In the app's **Login Screen**, ensure you enter the correct URL:
   `http://<YOUR_IP>:8000` (e.g., `http://192.168.1.146:8000`)

### 4. Run the Application
// turbo
Execute the following to start the app in debug mode on your specific device (moto g04s):
```powershell
cd interno_billing_app; flutter pub get; flutter run -d adb-ZL7324NDXD-e2sm8j._adb-tls-connect._tcp --debug
```

### 5. Troubleshooting
- **Connection Refused:** Ensure the Monolith is running (`docker ps`) and your Windows Firewall allows port 8000.
- **Not Found:** If `flutter` is not recognized, ensure Flutter SDK is in your PATH.
- **Build Failure:** Run `flutter clean` then `flutter pub get`.

---
**Status:** 🚀 Mobile Deployment Protocol Ready — 2026-05-09
