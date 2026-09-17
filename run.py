"""One-command launcher for URLShield AI."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
REQUIRED_MODULES = {
    "pandas": "pandas",
    "numpy": "numpy",
    "sklearn": "scikit-learn",
    "joblib": "joblib",
    "streamlit": "streamlit",
    "plotly": "plotly",
}


def ensure_dependencies() -> None:
    missing = [package for module, package in REQUIRED_MODULES.items() if importlib.util.find_spec(module) is None]
    if missing:
        print(f"Installing missing packages: {', '.join(missing)}")
        subprocess.run([sys.executable, "-m", "pip", "install", *missing], check=True)


def main() -> None:
    ensure_dependencies()
    print("Training URLShield AI model...")
    subprocess.run([sys.executable, "train_model.py"], cwd=ROOT, check=True)
    print("Starting URLShield AI at http://localhost:8501")
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
