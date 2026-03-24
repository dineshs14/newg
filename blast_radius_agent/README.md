# 🔬 Blast Radius Analysis Agent

> AI-powered code change impact analysis using NVIDIA Nemotron API.  
> Paste your Jira ticket + GitHub PR diff → get a structured risk report.

---

## What It Does

This agent reads context from plain text files (Jira tickets, GitHub diffs, code snippets) and sends them to NVIDIA's free Nemotron API to produce a **Blast Radius Analysis Report** covering:

1. **What Was Done** — Summary of the code change
2. **Root Cause / Risk Origin** — Why the change introduces risk
3. **Impacted Modules** — Every file/module/service affected
4. **Risk Level** — LOW / MEDIUM / HIGH / CRITICAL with justification
5. **Suggested Fix / Mitigation** — Concrete steps to reduce blast radius
6. **Impact Chain** — Step-by-step propagation trace

Reports are generated as both **terminal output** and a **beautiful HTML report** that auto-opens in your browser.

---

## Quick Start

### Option A: One-command launcher (recommended)

```bash
cd blast_radius_agent
python run.py
```

Smart launcher behavior (no flags):
- Validates `inputs/jira.txt` and `inputs/github.txt`
- If both are filled, runs real analysis and opens the HTML report
- If missing/incomplete, falls back to demo mode and opens the HTML prototype

The launcher auto-installs dependencies first.

### Option A2: Build a Windows executable for demo

```bash
cd blast_radius_agent
build_demo_exe.bat
```

The build script creates an isolated local virtual environment (`.build-venv`) before packaging, so global Python packages do not interfere.

Then run:

```bash
dist\BlastRadiusDemo.exe
```

The executable uses the same smart behavior (check Jira + GitHub first, then run real analysis or demo fallback).
When using the executable, place your required files at `dist/inputs/jira.txt` and `dist/inputs/github.txt`.
Generated reports are saved under `dist/outputs/`.

### Option B: Manual setup

```bash
cd blast_radius_agent
pip install -r requirements.txt
python agent.py --demo --open
```

---

## Demo Mode 🎮

Try the agent instantly without any API key:

```bash
python agent.py --demo --open
```

This uses built-in mock data to generate a full report so you can see exactly what the output looks like before connecting to the real API.

---

## Full Setup (Real Analysis)

### 1. Set your NVIDIA API key

Get a free key at [build.nvidia.com](https://build.nvidia.com/)

```bash
# Option A: Environment variable
export NVIDIA_API_KEY=nvapi-XXXXXXXXXXXXXXXX

# Option B: .env file (Windows)
echo NVIDIA_API_KEY=nvapi-XXXXXXXXXXXXXXXX > .env
```

### 2. Fill in your context

Edit the input files with your ticket/PR details:

```bash
# Required: Jira ticket context
notepad inputs/jira.txt

# Required: GitHub PR / diff
notepad inputs/github.txt

# Optional: Code before & after the change
notepad inputs/code_before.txt
notepad inputs/code_after.txt

# Optional: Repository directory tree
notepad inputs/repo_structure.txt
```

### 3. Run the analysis

```bash
python agent.py --open
```

---

## CLI Options

| Flag | Description |
|------|-------------|
| `--demo` | Use mock data — no API key needed |
| `--open` | Auto-open the HTML report in your default browser |
| `--show-thinking` | Display the model's internal reasoning trace |
| `--dry-run` | Build and print the prompt without calling the API |
| `--list-inputs` | Show which input files are detected and their sizes |
| `--no-save` | Print report to terminal without saving to file |
| `--quiet` | Save report to file without terminal output |
| `--inputs <dir>` | Use a custom inputs directory |
| `--repo <path>` | Auto-detect git diff from a local repository |
| `--watch` | Re-run analysis when input files change |
| `--interval <sec>` | Watch interval in seconds (default: 60) |

### Examples

```bash
# Quick demo (no API key required)
python agent.py --demo --open

# Real analysis → opens in browser
python agent.py --open

# Show AI's chain-of-thought reasoning
python agent.py --show-thinking

# Preview the assembled prompt (no API call)
python agent.py --dry-run

# Check which input files are ready
python agent.py --list-inputs

# Auto-detect git diff from a repo
python agent.py --repo C:\Projects\my-app

# Watch mode — re-runs when inputs change
python agent.py --watch --demo

# Use a different inputs folder
python agent.py --inputs ./sprint42_inputs
```

---

## HTML Report

Every analysis generates a self-contained HTML file with:

- **Dark-themed glassmorphism design** — looks great on any screen
- **Color-coded risk badges** — instant visual risk assessment
- **Syntax-highlighted code blocks** — easy to read diffs and fixes
- **Responsive layout** — works on desktop and mobile
- **Print-friendly** — clean output when printed to PDF
- **Suggestion selector** — choose which AI fixes to apply in your project folder
- **Unselected export** — writes unselected suggestions to a timestamped `.txt` file

Reports are saved to `outputs/analysis_<timestamp>.html` alongside the `.txt` version.

### Applying Suggestions From The Web Report

1. Open the generated HTML report.
2. In **Apply Suggested Fixes**, select the suggestions you want to apply.
3. Click **Choose Project Folder** and pick your codebase root.
4. Click **Apply Selected + Save Unselected**.

Behavior:
- Selected suggestions are applied as exact `find` → `replace` edits in the chosen project folder.
- Unselected suggestions are saved as `blast_radius_unselected_<timestamp>.txt` in the same folder.

Note: This relies on structured output in **Section 5** (`File`, `Action`, `find`, `replace`).

---

## Watch Mode 👁️

Re-run automatically whenever your input files change:

```bash
python agent.py --watch
python agent.py --watch --interval 30     # Check every 30 seconds
python agent.py --watch --demo            # Watch with demo data
```

The first run auto-opens the browser. Subsequent runs save silently.

---

## Project Structure

```
blast_radius_agent/
│
├── run.py                # Cross-platform launcher (auto-installs deps)
├── agent.py              # Main CLI entry point
├── nvidia_client.py      # NVIDIA API wrapper (streaming + thinking)
├── prompt_builder.py     # Assembles prompt from input text files
├── report_writer.py      # Parses AI output → terminal report
├── html_report.py        # Generates beautiful HTML reports
├── demo_data.py          # Mock response for demo mode
├── config.py             # API key, model name, defaults
│
├── inputs/               # ← Put your context here
│   ├── jira.txt          # Jira ticket content
│   ├── github.txt        # GitHub PR / diff
│   ├── code_before.txt   # (optional) Original code
│   ├── code_after.txt    # (optional) Modified code
│   └── repo_structure.txt # (optional) Repo directory tree
│
├── outputs/              # ← Reports saved here
│   ├── analysis_*.txt    # Timestamped text reports
│   └── analysis_*.html   # Timestamped HTML reports
│
├── requirements.txt
├── .env.example
└── README.md
```

---

## Input File Format

### `jira.txt` (required)

```
TICKET ID: PROJ-1234
TITLE: Remove phone field from Address interface
STATUS: In Progress
PRIORITY: High
DESCRIPTION: 
For GDPR compliance, remove the phone number field...
```

### `github.txt` (required)

```
PR TITLE: Remove phone field from Address
PR NUMBER: #42
CHANGED FILES:
- src/types.ts
- src/components/CheckoutForm.tsx

DIFF:
diff --git a/src/types.ts b/src/types.ts
--- a/src/types.ts
+++ b/src/types.ts
@@ -5,7 +5,6 @@
   street: string;
   city: string;
-  phone: string;
 }
```

---

## How It Works

```
┌─────────────┐     ┌──────────────────┐     ┌────────────────┐
│  Input Files │ ──→ │  Prompt Builder  │ ──→ │  NVIDIA API    │
│  (jira.txt,  │     │  (assembles      │     │  (Nemotron     │
│   github.txt)│     │   structured     │     │   streaming +  │
│              │     │   prompt)        │     │   thinking)    │
└─────────────┘     └──────────────────┘     └───────┬────────┘
                                                      │
                    ┌──────────────────┐               │
                    │  Report Writer   │ ←─────────────┘
                    │  (TXT + HTML     │
                    │   reports)       │
                    └──────────────────┘
```

---

## Requirements

- **Python 3.10+**
- **NVIDIA API Key** (free tier at [build.nvidia.com](https://build.nvidia.com/)) — not needed for demo mode
- No GPU needed — runs via cloud API
- No Ollama — no local model downloads
- Works on **Windows, macOS, and Linux**

---

## Configuration

Edit `config.py` to change:

| Setting | Default | Description |
|---------|---------|-------------|
| `MODEL_NAME` | `nvidia/llama-3.3-nemotron-super-49b-v1` | NVIDIA model to use |
| `TEMPERATURE` | `0.6` | Creativity (lower = more focused) |
| `MAX_TOKENS` | `16384` | Max output tokens |
| `REASONING_BUDGET` | `16384` | Chain-of-thought token budget |
| `MAX_INPUT_FILE_SIZE_KB` | `50` | Warn if input file exceeds this |

---

## License

MIT — use freely for your team's code review workflow.
