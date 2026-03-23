"""
Blast Radius Agent — Configuration
===================================
Stores NVIDIA API credentials, model settings, and defaults.
Set your API key via environment variable NVIDIA_API_KEY or .env file.
"""

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv is optional

# ── NVIDIA API Settings ─────────────────────────────────────────────────────
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "")

# ── Model Configuration ─────────────────────────────────────────────────────
MODEL_NAME = "nvidia/llama-3.3-nemotron-super-49b-v1"

# ── Generation Defaults ─────────────────────────────────────────────────────
TEMPERATURE = 0.6
TOP_P = 0.95
MAX_TOKENS = 16384
REASONING_BUDGET = 16384  # Chain-of-thought token budget

# ── File Size Limits ─────────────────────────────────────────────────────────
MAX_INPUT_FILE_SIZE_KB = 50  # Warn if any input file exceeds this

# ── Input File Names ─────────────────────────────────────────────────────────
INPUT_FILES = {
    "jira": "jira.txt",
    "github": "github.txt",
    "code_before": "code_before.txt",
    "code_after": "code_after.txt",
    "repo_structure": "repo_structure.txt",
}

# Required files (will show a placeholder if missing)
REQUIRED_FILES = {"jira", "github"}

# Optional files (silently omitted if missing)
OPTIONAL_FILES = {"code_before", "code_after", "repo_structure"}

# ── Output Directory ─────────────────────────────────────────────────────────
OUTPUT_DIR = "outputs"
