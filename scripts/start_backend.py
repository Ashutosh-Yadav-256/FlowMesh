import sys
from pathlib import Path
import uvicorn

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "apps" / "api"))
sys.path.insert(0, str(ROOT / "packages" / "ai-scripting"))
sys.path.insert(0, str(ROOT / "packages" / "data-transform"))
sys.path.insert(0, str(ROOT / "packages" / "auth"))
sys.path.insert(0, str(ROOT / "packages" / "workflow-schema"))
sys.path.insert(0, str(ROOT / "packages" / "state-store"))
sys.path.insert(0, str(ROOT / "packages" / "connector-sdk"))
sys.path.insert(0, str(ROOT / "packages" / "search-engine"))
sys.path.insert(0, str(ROOT / "services" / "workflow-engine"))
sys.path.insert(0, str(ROOT / "services" / "event-router"))
sys.path.insert(0, str(ROOT / "services" / "incident-manager"))
sys.path.insert(0, str(ROOT / "connectors"))
sys.path.insert(0, str(ROOT))

from app.main import app

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
