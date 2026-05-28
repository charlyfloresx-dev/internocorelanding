"""
Kiosk Auth Flow — Phase 153
Tests:
  1. Classic RFID flow (no company_id, backward compat)
  2. Classic PIN flow (no company_id, backward compat)
  3. Company-bound kiosk flow: admin provisions a company → kiosk login with company_id
  4. internal_id_pattern validation: set regex, test valid + invalid IDs
"""
import sys
import requests
import json
import jwt
import os

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_URL = os.getenv("API_URL", "http://localhost:8000/api/v1/auth")
ADMIN_MASTER_KEY = os.getenv("CORE_ADMIN_MASTER_KEY", "ROTATED_MASTER_KEY_GOD_MODE")
ADMIN_EMAIL = "charly@interno.com"
ADMIN_PASS = "charly123"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _print_token(token: str, label: str):
    decoded = jwt.decode(token, options={"verify_signature": False})
    print(f"  ✓ {label}")
    print(f"    Name:        {decoded.get('full_name')}")
    print(f"    Internal ID: {decoded.get('internal_id')}")
    print(f"    Company ID:  {decoded.get('cid')}")
    print(f"    Supervisor:  {decoded.get('is_supervisor')}")
    print(f"    WarehouseID: {decoded.get('wid')}")
    print(f"    Perms:       {decoded.get('permissions')}")


def admin_login_get_company() -> tuple[str, str, str]:
    """Logs in as admin → returns (admin_jwt, company_id, company_name) for the first company."""
    r = requests.post(f"{BASE_URL}/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
    r.raise_for_status()
    data = r.json()["data"]

    if "selection_token" in data:
        sel_token = data["selection_token"]
        company = next((c for c in data["companies"] if "Tijuana" in c["company_name"]), data["companies"][0])
        company_id = company["company_id"]
        company_name = company["company_name"]
        r2 = requests.post(
            f"{BASE_URL}/select-company",
            json={"company_id": company_id},
            headers={"Authorization": f"Bearer {sel_token}"},
        )
        r2.raise_for_status()
        admin_jwt = r2.json()["data"]["access_token"]
    else:
        admin_jwt = data["access_token"]
        company_id = data["company_id"]
        company_name = data.get("company_name", "")

    return admin_jwt, company_id, company_name


# ─── Test 1: Classic RFID (no company_id) ─────────────────────────────────────

def test_rfid_flow(rfid_tag: str):
    print(f"\n[1] RFID FLOW — tag: {rfid_tag}")
    payload = {"identity_identifier": rfid_tag, "access_method": "RFID_SCAN"}
    try:
        r = requests.post(f"{BASE_URL}/collaborator-login", json=payload)
        r.raise_for_status()
        data = r.json()["data"]

        if data.get("selection_token"):
            company = data["companies"][0]
            print(f"    Discovery: auto-selecting {company['company_name']}")
            r2 = requests.post(
                f"{BASE_URL}/select-company",
                json={"company_id": company["company_id"]},
                headers={"Authorization": f"Bearer {data['selection_token']}"},
            )
            r2.raise_for_status()
            token = r2.json()["data"]["access_token"]
        else:
            token = data["access_token"]

        _print_token(token, "RFID OK")
    except Exception as e:
        print(f"  ✗ ERR: {e}")
        if "r" in dir() and hasattr(r, "text"):
            print(f"    Response: {r.text[:200]}")


# ─── Test 2: Classic PIN (no company_id) ──────────────────────────────────────

def test_pin_flow(internal_id: str, pin: str):
    print(f"\n[2] PIN FLOW — id: {internal_id} pin: {pin}")
    payload = {"internal_id": internal_id, "identity_identifier": pin, "access_method": "PIN_PAD"}
    try:
        r = requests.post(f"{BASE_URL}/collaborator-login", json=payload)
        r.raise_for_status()
        data = r.json()["data"]

        if data.get("selection_token"):
            company = data["companies"][0]
            print(f"    Discovery: auto-selecting {company['company_name']}")
            r2 = requests.post(
                f"{BASE_URL}/select-company",
                json={"company_id": company["company_id"]},
                headers={"Authorization": f"Bearer {data['selection_token']}"},
            )
            r2.raise_for_status()
            token = r2.json()["data"]["access_token"]
        else:
            token = data["access_token"]

        _print_token(token, "PIN OK")
    except Exception as e:
        print(f"  ✗ ERR: {e}")
        if "r" in dir() and hasattr(r, "text"):
            print(f"    Response: {r.text[:200]}")


# ─── Test 3: Company-bound kiosk flow ─────────────────────────────────────────

def test_company_bound_kiosk(internal_id: str, pin: str):
    """Admin provisions kiosk → collaborator logs in WITH company_id."""
    print(f"\n[3] COMPANY-BOUND KIOSK FLOW — id: {internal_id} pin: {pin}")

    # Step A: admin login to discover company_id
    try:
        admin_jwt, company_id, company_name = admin_login_get_company()
        print(f"    Admin provisioned company: {company_name} ({company_id[:8]}...)")
    except Exception as e:
        print(f"  ✗ ERR getting company: {e}")
        return

    # Step B: collaborator login WITH company_id (kiosk sends it)
    payload = {
        "internal_id": internal_id,
        "identity_identifier": pin,
        "access_method": "PIN_PAD",
        "company_id": company_id,
    }
    try:
        r = requests.post(f"{BASE_URL}/collaborator-login", json=payload)
        r.raise_for_status()
        data = r.json()["data"]
        token = data.get("access_token") or (
            # If still multi-company (shouldn't happen when company_id supplied)
            requests.post(
                f"{BASE_URL}/select-company",
                json={"company_id": company_id},
                headers={"Authorization": f"Bearer {data['selection_token']}"},
            ).json()["data"]["access_token"]
            if data.get("selection_token") else None
        )
        if token:
            _print_token(token, f"Company-bound login OK (cid={company_id[:8]}...)")
        else:
            print(f"  ✗ No token in response: {r.text[:200]}")
    except Exception as e:
        print(f"  ✗ ERR: {e}")
        if "r" in dir() and hasattr(r, "text"):
            print(f"    Response: {r.text[:200]}")


# ─── Test 4: internal_id_pattern validation ───────────────────────────────────

def test_id_pattern_validation():
    """Sets a regex on the company, then tests valid and invalid IDs."""
    print(f"\n[4] INTERNAL ID PATTERN VALIDATION")

    # Get admin JWT + company_id
    try:
        admin_jwt, company_id, company_name = admin_login_get_company()
        print(f"    Company: {company_name}")
    except Exception as e:
        print(f"  ✗ ERR getting admin token: {e}")
        return

    # Set pattern via PATCH /companies/my/id-pattern
    pattern = r"^\d{3,6}$"  # Only 3–6 digit IDs
    try:
        r = requests.patch(
            f"{BASE_URL.replace('/auth', '')}/companies/my/id-pattern",
            json={"internal_id_pattern": pattern},
            headers={"Authorization": f"Bearer {admin_jwt}"},
        )
        r.raise_for_status()
        print(f"    Pattern set: {pattern}")
    except Exception as e:
        print(f"  ✗ ERR setting pattern: {e}")
        if "r" in dir() and hasattr(r, "text"):
            print(f"    Response: {r.text[:300]}")
        return

    # Test 4a: valid ID (e.g. "301" → 3 digits, matches ^\d{3,6}$)
    valid_id = "301"
    payload = {
        "internal_id": valid_id,
        "identity_identifier": "1234",
        "access_method": "PIN_PAD",
        "company_id": company_id,
    }
    r_valid = requests.post(f"{BASE_URL}/collaborator-login", json=payload)
    if r_valid.status_code in (200, 401):  # 200 = OK, 401 = wrong PIN but pattern passed
        print(f"  ✓ Valid ID '{valid_id}' passed pattern (HTTP {r_valid.status_code})")
    else:
        print(f"  ✗ Valid ID '{valid_id}' unexpectedly rejected (HTTP {r_valid.status_code}): {r_valid.text[:200]}")

    # Test 4b: invalid ID format ("ABC-001" → letters, shouldn't match ^\d{3,6}$)
    invalid_id = "ABC-001"
    payload["internal_id"] = invalid_id
    r_invalid = requests.post(f"{BASE_URL}/collaborator-login", json=payload)
    if r_invalid.status_code == 422:
        print(f"  ✓ Invalid ID '{invalid_id}' correctly rejected (422)")
        resp_data = r_invalid.json()
        print(f"    Detail: {resp_data.get('detail') or resp_data.get('message')}")
    else:
        print(f"  ✗ Expected 422 for '{invalid_id}', got HTTP {r_invalid.status_code}: {r_invalid.text[:200]}")

    # Cleanup: clear pattern
    try:
        requests.patch(
            f"{BASE_URL.replace('/auth', '')}/companies/my/id-pattern",
            json={"internal_id_pattern": None},
            headers={"Authorization": f"Bearer {admin_jwt}"},
        )
        print(f"    Pattern cleared.")
    except Exception:
        pass


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("      INTERNO CORE — KIOSK AUTH FLOW SUITE (Phase 153)")
    print("=" * 70)

    # 1. Classic RFID (backward compat)
    test_rfid_flow("2327559684")

    # 2. Classic PIN (backward compat)
    test_pin_flow("003709A", "1234")

    # 3. Company-bound kiosk login
    test_company_bound_kiosk("301", "1234")

    # 4. Pattern validation
    test_id_pattern_validation()

    print("\n" + "=" * 70)
    print("  DONE")
    print("=" * 70)
