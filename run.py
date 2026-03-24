#!/usr/bin/env python3
"""
One-file launcher for Blast Radius Agent.

Usage:
  python run.py                # Live analysis
  python run.py --demo         # Demo analysis
  python run.py --open         # Open report in browser
  python run.py --apply --approvals outputs/approvals.json --project-root demo-project-repo --no-confirm

This launcher:
- ensures virtualenv exists
- installs dependencies
- forwards all CLI args to agent.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VENV_DIR = ROOT / ".venv"
AGENT = ROOT / "agent.py"
REQ = ROOT / "requirements.txt"


def _venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, cwd=str(ROOT))
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def _ensure_venv() -> Path:
    py = _venv_python()
    if py.exists():
        return py

    print("[setup] Creating virtual environment...")
    _run([sys.executable, "-m", "venv", str(VENV_DIR)])
    return _venv_python()


def _ensure_deps(py: Path) -> None:
    if not REQ.exists():
        return

    print("[setup] Installing dependencies...")
    _run([str(py), "-m", "pip", "install", "--upgrade", "pip"])
    _run([str(py), "-m", "pip", "install", "-r", str(REQ)])


def main() -> None:
    if not AGENT.exists():
        raise SystemExit("agent.py not found")

    py = _ensure_venv()
    _ensure_deps(py)

    args = sys.argv[1:]
    print(f"[run] python agent.py {' '.join(args)}")
    _run([str(py), str(AGENT), *args])


if __name__ == "__main__":
    main()
