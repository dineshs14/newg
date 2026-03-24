# 🔬 Blast Radius Analysis Agent

> **Enterprise-Grade AI-Powered Code Impact Analysis**  
> Real-world CI/CD pipeline with live NVIDIA Nemotron inference, interactive approvals, and auto-generated PRs.

---

## What It Does

The Blast Radius Agent is an **AI-powered code impact analyzer** that understands the ripple effects of code changes across your entire codebase. Using NVIDIA's Nemotron API, it:

1. **Analyzes code changes** — Reads Jira tickets + GitHub diffs
2. **Identifies blast radius** — Maps all impacted modules and services
3. **Assesses risk** — Rates changes as LOW / MEDIUM / HIGH / CRITICAL
4. **Suggests mitigations** — Provides concrete fixes for each impact
5. **Generates PRs** — Creates candidate pull requests with diffs
6. **Enables approvals** — Interactive UI for reviewing & approving changes
7. **Patches code** — Auto-applies approved changes to codebase
8. **Produces artifacts** — HTML reports, JSON metadata, PR text files

---

## Key Features

### ✅ Live AI Inference
- Connects to NVIDIA Nemotron API for real analysis (not mock data)
- Supports chain-of-thought reasoning for deeper impact analysis
- Streaming responses for fast feedback

### 🎨 Beautiful HTML Reports
- Modern, responsive dark-mode UI
- Professional typography and gradients
- Smooth animations and hover effects
- Print-optimized layouts

### ✔️ Interactive Approval Workflow
- Checkbox-based approval system in HTML
- Preview changes before applying
- Approval log tracking
- Export approvals as JSON

### 🔧 Smart Code Patching
- Safe file modification with backup/rollback
- Unified diff application
- Path traversal protection
- Syntax validation

### 📝 Auto-Generated PRs
- Candidate PR text files with embedded diffs
- Structured JSON metadata
- Risk assessment summary
- Testing recommendations
- Links to original tickets

---

## Real-World Workflow

### One Executable Entry Point

Use the single launcher file on any laptop:

```bash
python run.py --open
```

`run.py` auto-creates `.venv`, installs dependencies, and forwards all args to `agent.py`.

### Step 1: Set Your NVIDIA API Key

Get a **free** key at [build.nvidia.com](https://build.nvidia.com/):

```bash
# Option A: Environment variable
export NVIDIA_API_KEY=nvapi-XXXXXXXXXXXXXXXX

# Option B: Create .env file
echo "NVIDIA_API_KEY=nvapi-XXXXXXXXXXXXXXXX" > .env
```

### Step 2: Prepare Context

Create input files in the `inputs/` directory:

```bash
# inputs/jira.txt — Jira ticket description
KS-107: Remove phone field for GDPR compliance
...description and requirements...

# inputs/github.txt — Git diff or PR description
diff --git a/src/types.ts b/src/types.ts
...unified diff...

# Optional: inputs/code_before.txt, code_after.txt, repo_structure.txt
```

### Step 3: Run Analysis

```bash
# Live analysis with NVIDIA API
python run.py --open

# Or demo mode (no API key)
python run.py --demo --open
```

### Step 4: Review HTML Report

- Opens automatically in your browser
- Interactive approval checkboxes
- Risk assessment with visual badges
- Suggested fixes and testing notes

### Step 5: Approve & Apply

In the HTML report:

1. **Review** each proposed change
2. **Tick checkbox** to approve changes
3. **Export Approvals** to save `approvals.json`
4. **Run apply command** to patch codebase:

```bash
python run.py --apply --approvals approvals.json --project-root demo-project-repo --no-confirm
```

5. **Review generated PR** in `demo-project-repo/outputs/candidate_pr.txt`

### Step 6: Merge PR

The generated `candidate_pr.txt` contains:
- Complete PR description
- Risk assessment
- Embedded diffs for each file
- Testing recommendations
- Merge notes

---

## CLI Commands

```bash
# Live analysis (requires NVIDIA_API_KEY)
python agent.py

# Demo mode (no API key)
python agent.py --demo

# Save & auto-open HTML report
python agent.py --demo --open

# Show internal reasoning
python agent.py --show-thinking

# Preview prompt without API call
python agent.py --dry-run

# List detected input files
python agent.py --list-inputs

# Custom inputs directory
python agent.py --inputs ./my_context

# Auto-detect git diff from repo
python agent.py --repo /path/to/project

# Watch mode (re-run on file changes)
python agent.py --watch

# Quiet mode (save only, no terminal output)
python agent.py --quiet
```

---

## Project Structure

```
e:\Gitrad\
├── agent.py                 # Main CLI orchestrator
├── prompt_builder.py        # Assembles structured prompts
├── nvidia_client.py         # NVIDIA API wrapper
├── html_report.py           # Beautiful HTML report generator
├── pr_generator.py          # PR text/JSON generation
├── code_patcher.py          # Safe file patching with rollback
├── approval_handler.py      # Process user approvals
├── config.py                # Configuration & settings
├── requirements.txt         # Python dependencies
├── .env                     # NVIDIA API key (create this)
│
├── inputs/                  # Input context files
│   ├── jira.txt            # Jira ticket description
│   ├── github.txt          # Git diff / PR description
│   ├── code_before.txt     # Code snippets (optional)
│   ├── code_after.txt      # Code changes (optional)
│   └── repo_structure.txt  # Project structure (optional)
│
└── outputs/                 # Generated artifacts
    ├── analysis_<timestamp>.html    # Beautiful HTML report
    ├── candidate_pr.txt             # PR description with diffs
    └── candidate_pr.json            # Structured PR metadata
```

---

## Configuration

Edit `.env` to customize behavior:

```bash
# NVIDIA API
NVIDIA_API_KEY=nvapi-...
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1

# Approval mode
APPROVAL_MODE=browser      # 'browser' | 'cli' | 'auto'

# Code patching
AUTO_APPLY_CHANGES=false   # Safety: require confirmation before patching

# PR output
PR_FORMAT=text             # 'text' | 'json' | 'both'

# Demo mode
DEMO_MODE=false            # Use mock data instead of API
```

---

## Installation

### Requirements
- Python 3.11+
- Windows / macOS / Linux

### Setup

```bash
# Clone or download
cd blast-radius-agent

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set API key
echo "NVIDIA_API_KEY=nvapi-..." > .env

# Run
python run.py --demo --open
```

---

## Troubleshooting

### Error: NVIDIA_API_KEY is not set

```bash
# Set environment variable
export NVIDIA_API_KEY=nvapi-YOUR_KEY_HERE

# Or create .env file
echo "NVIDIA_API_KEY=nvapi-YOUR_KEY_HERE" > .env
```

### Error: No input files found

Make sure `inputs/jira.txt` and `inputs/github.txt` exist:

```bash
# List input files
python agent.py --list-inputs

# Create example inputs
echo "Ticket: KS-107" > inputs/jira.txt
echo "diff ..." > inputs/github.txt
```

### HTML Report Won't Open

The report is still generated. Check:

```bash
# Find the HTML file
ls outputs/*.html

# Open manually in browser
# On Windows: start outputs\analysis_*.html
# On macOS: open outputs/analysis_*.html
# On Linux: xdg-open outputs/analysis_*.html
```

---

## Performance Notes

- **Demo mode:** Instant (uses mock data)
- **Live API:** 10-30 seconds (depends on API response time)
- **Code patching:** < 1 second (per file)
- **Report generation:** < 2 seconds

---

## API Costs

- **NVIDIA Nemotron:** FREE tier available at [build.nvidia.com](https://build.nvidia.com/)
- No credit card required for free inference API

---

## License

This project uses the NVIDIA Nemotron API for inference.  
Always follow NVIDIA's terms of service and rate limits.

---

Made with ❤️ for developers who care about code quality.
