import requests

services = {
    "auth": "http://localhost:8001/health",
    "subscription": "http://localhost:8002/health",
    "master-data": "http://localhost:8003/health",
    "tickets": "http://localhost:8004/health",
    "mes": "http://localhost:8005/health",
    "inventory": "http://localhost:8006/health",
    "wms": "http://localhost:8007/health",
    "currency": "http://localhost:8008/api/v1/currencies/active-rate", # Check real endpoint
    "notification": "http://localhost:8010/health"
}

for name, url in services.items():
    try:
        resp = requests.get(url, timeout=2)
        print(f"✅ {name}: {resp.status_code}")
    except Exception as e:
        print(f"❌ {name}: {str(e)}")
