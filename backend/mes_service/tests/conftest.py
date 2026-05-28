import sys
import os
from dotenv import load_dotenv

# ── Path resolution ────────────────────────────────────────────────────────────
_service_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_backend_root = os.path.abspath(os.path.join(_service_root, ".."))
_repo_root    = os.path.abspath(os.path.join(_backend_root, ".."))

for _p in [_service_root, _backend_root]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Load root .env before importing common (which validates config at import time)
load_dotenv(os.path.join(_repo_root, ".env"), override=False)
