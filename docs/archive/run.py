import sys
import uvicorn
import os

# Add the backend/wms_service directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend", "wms_service"))
# Add the backend directory to allow importing 'common'
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True, reload_dirs=["backend/wms_service/app"])
