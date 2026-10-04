"""Launch from any working directory with repository config and private .env."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from check_config import main

if __name__ == '__main__':
    if main() != 0:
        raise SystemExit(1)
    os.chdir(ROOT)
    os.execv(sys.executable, [sys.executable, '-m', 'streamlit', 'run', str(ROOT / 'app.py')])
