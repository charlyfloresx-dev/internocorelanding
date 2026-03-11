import sys
import urllib.request
import time

# Configuración de servicios y puertos
SERVICES = [
    {"name": "Auth Service", "url": "http://localhost:8001/health"},
    {"name": "WMS Service", "url": "http://localhost:8002/health"},
    {"name": "Master Data Service", "url": "http://localhost:8003/health"},
]

def check_service(service):
    """Realiza un ping al endpoint de salud del servicio."""
    try:
        # Timeout corto para fail-fast
        with urllib.request.urlopen(service["url"], timeout=5) as response:
            if response.getcode() == 200:
                print(f"✅ {service['name']} is healthy (HTTP 200).")
                return True
            else:
                print(f"❌ {service['name']} returned status {response.getcode()}.")
                return False
    except Exception as e:
        print(f"❌ {service['name']} check failed: {e}")
        return False

def main():
    print("🚀 Starting Deployment Smoke Test...")
    all_healthy = True
    
    for service in SERVICES:
        if not check_service(service):
            all_healthy = False
    
    if all_healthy:
        print("\n✅ SYSTEM STATUS: OPERATIONAL")
        sys.exit(0)
    else:
        print("\n❌ SYSTEM STATUS: DEGRADED OR FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()