"""FlowMesh Master E2E Demonstration Showcase (Delegates to scripts/demo_e2e_showcase.py)."""
import runpy
from pathlib import Path

if __name__ == "__main__":
    target = Path(__file__).resolve().parent / "scripts" / "demo_e2e_showcase.py"
    runpy.run_path(str(target), run_name="__main__")
