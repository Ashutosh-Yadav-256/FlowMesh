"""
FlowMesh API Gateway Package
Auto-discovers and registers monorepo packages, services, and connectors into sys.path.
"""
import sys
from pathlib import Path

_current = Path(__file__).resolve().parent
for _candidate in (_current.parent, _current.parent.parent, _current.parent.parent.parent):
    _packages = _candidate / "packages"
    if _packages.is_dir():
        for _pkg in _packages.iterdir():
            if _pkg.is_dir() and str(_pkg) not in sys.path:
                sys.path.insert(0, str(_pkg))
        _services = _candidate / "services"
        if _services.is_dir():
            for _srv in _services.iterdir():
                if _srv.is_dir() and str(_srv) not in sys.path:
                    sys.path.insert(0, str(_srv))
        _connectors = _candidate / "connectors"
        if _connectors.is_dir() and str(_connectors) not in sys.path:
            sys.path.insert(0, str(_connectors))
        break
