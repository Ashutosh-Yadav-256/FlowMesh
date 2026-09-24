"""FlowMesh Database & Demo Seeder Entrypoint (Delegates to scripts/seed_demo.py)."""
import runpy
from pathlib import Path

if __name__ == "__main__":
    target = Path(__file__).resolve().parent / "scripts" / "seed_demo.py"
    runpy.run_path(str(target), run_name="__main__")
