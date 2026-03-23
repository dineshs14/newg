#!/usr/bin/env python3
"""
🔬 Blast Radius Agent — Cross-Platform Launcher
=================================================
Single file you can give to ANYONE on any OS.
It checks for Python, installs deps, and runs the agent.

Works on: Windows, macOS, Linux.

Usage:
    python run.py              # Auto-install deps + run demo
    python run.py --demo       # Run with mock data (no API key)
    python run.py --open       # Auto-open HTML report in browser
    python run.py --watch      # Monitor for changes every 60s

    All flags from agent.py are forwarded automatically.
"""

import os
import sys
import subprocess
import platform


# ── Paths ────────────────────────────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REQUIREMENTS = os.path.join(SCRIPT_DIR, "requirements.txt")
AGENT_PY = os.path.join(SCRIPT_DIR, "agent.py")
VENV_DIR = os.path.join(SCRIPT_DIR, ".venv")


# ── Color helpers (work on modern terminals) ─────────────────────────────────

def _supports_color() -> bool:
    """Check if the terminal supports ANSI colors."""
    if platform.system() == "Windows":
        # Enable VT processing on Windows 10+
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            return True
        except Exception:
            return os.environ.get("WT_SESSION") is not None  # Windows Terminal
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


USE_COLOR = _supports_color()


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


def info(msg: str):
    print(f"  {_c('96', '●')} {msg}")


def ok(msg: str):
    print(f"  {_c('92', '✓')} {msg}")


def warn(msg: str):
    print(f"  {_c('93', '⚠')} {msg}")


def fail(msg: str):
    print(f"  {_c('91', '✖')} {msg}")


# ── Python Check ─────────────────────────────────────────────────────────────

def check_python():
    """Verify Python version >= 3.10."""
    major, minor = sys.version_info[:2]
    if major < 3 or (major == 3 and minor < 10):
        fail(f"Python 3.10+ required. You have {major}.{minor}.")
        fail("Download: https://www.python.org/downloads/")
        sys.exit(1)
    ok(f"Python {major}.{minor} detected")


# ── Dependency Installation ──────────────────────────────────────────────────

def install_deps():
    """Install requirements.txt if not already installed."""
    if not os.path.exists(REQUIREMENTS):
        warn("requirements.txt not found — skipping install")
        return

    # Quick check: try importing openai
    try:
        import openai  # noqa: F401
        ok("Dependencies already installed")
        return
    except ImportError:
        pass

    info("Installing dependencies...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", REQUIREMENTS, "--quiet"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        ok("Dependencies installed successfully")
    else:
        warn("pip install had warnings — trying anyway")
        if result.stderr:
            for line in result.stderr.strip().split("\n")[:3]:
                print(f"    {_c('2', line)}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    os_name = platform.system()
    os_emoji = {"Windows": "🪟", "Darwin": "🍎", "Linux": "🐧"}.get(os_name, "💻")

    print()
    print(f"  {_c('1;96', '━━━ BLAST RADIUS AGENT LAUNCHER ━━━')}")
    print(f"  {_c('2', f'{os_emoji} {os_name} • Python {sys.version_info.major}.{sys.version_info.minor}')}")
    print()

    # Step 1: Check Python
    check_python()

    # Step 2: Install dependencies
    install_deps()

    # Step 3: Verify agent.py exists
    if not os.path.exists(AGENT_PY):
        fail(f"agent.py not found at: {AGENT_PY}")
        sys.exit(1)
    ok("Agent found")

    # Step 4: Forward all CLI args to agent.py
    args = sys.argv[1:]

    # If no args at all, default to --demo --open for first-time users
    if not args:
        info("No flags specified — running demo with browser open")
        args = ["--demo", "--open"]

    print()
    info(f"Running: python agent.py {' '.join(args)}")
    print()

    # Run agent.py with same Python interpreter
    result = subprocess.run(
        [sys.executable, AGENT_PY] + args,
        cwd=SCRIPT_DIR,
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
