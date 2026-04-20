import requests
import json

def test_login():
    url = "http://localhost:8001/api/v1/auth/login"
    data = {"email": "charly@interno.com", "password": "charly123"}
    try:
        r = requests.post(url, json=data)
        print(f"Status: {r.status_code}")
        print(json.dumps(r.json(), indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_login()
