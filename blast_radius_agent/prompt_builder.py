"""
Blast Radius Agent — Prompt Builder
=====================================
Reads all input text files and assembles a structured prompt
for the NVIDIA Nemotron model.
"""

import os
from config import INPUT_FILES, REQUIRED_FILES, OPTIONAL_FILES, MAX_INPUT_FILE_SIZE_KB


def _read_file(filepath: str) -> str | None:
    """Read a file and return its contents, or None if it doesn't exist."""
    if not os.path.isfile(filepath):
        return None
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return None


def _check_file_size(filepath: str, key: str) -> list[str]:
    """Return warnings if a file exceeds the size limit."""
    warnings = []
    if os.path.isfile(filepath):
        size_kb = os.path.getsize(filepath) / 1024
        if size_kb > MAX_INPUT_FILE_SIZE_KB:
            warnings.append(
                f"  ⚠ {key} ({INPUT_FILES[key]}) is {size_kb:.1f} KB "
                f"(limit: {MAX_INPUT_FILE_SIZE_KB} KB). "
                f"Content will be truncated to avoid token limits."
            )
    return warnings


def _truncate_if_needed(content: str, max_chars: int = 50000) -> str:
    """Truncate content with a notice if it exceeds max_chars."""
    if len(content) > max_chars:
        return (
            content[:max_chars]
            + "\n\n[... TRUNCATED — file exceeded size limit. "
            + "Provide a shorter excerpt for best results. ...]"
        )
    return content


def list_inputs(inputs_dir: str) -> dict[str, dict]:
    """
    List all input files, their status, and sizes.

    Returns:
        Dict mapping file key to {path, exists, size_kb, filename}
    """
    result = {}
    for key, filename in INPUT_FILES.items():
        filepath = os.path.join(inputs_dir, filename)
        exists = os.path.isfile(filepath)
        size_kb = os.path.getsize(filepath) / 1024 if exists else 0
        result[key] = {
            "path": filepath,
            "exists": exists,
            "size_kb": round(size_kb, 2),
            "filename": filename,
            "required": key in REQUIRED_FILES,
        }
    return result


def build_prompt(inputs_dir: str) -> tuple[str, list[str], list[str]]:
    """
    Read input files and assemble the master prompt.

    Args:
        inputs_dir: Path to the directory containing input text files.

    Returns:
        Tuple of (prompt_string, list_of_files_used, list_of_warnings)
    """

    files_used: list[str] = []
    warnings: list[str] = []

    # ── Read each input file ─────────────────────────────────────────────

    contents: dict[str, str] = {}

    for key, filename in INPUT_FILES.items():
        filepath = os.path.join(inputs_dir, filename)

        # Check file sizes
        warnings.extend(_check_file_size(filepath, key))

        raw = _read_file(filepath)

        if raw is not None and raw.strip():
            # Check if it's still a template (has placeholder markers)
            if "[Paste" in raw and raw.strip().count("\n") < 5:
                if key in REQUIRED_FILES:
                    contents[key] = f"No {key} context provided. (Template file not filled in.)"
                    warnings.append(f"  ⚠ {filename} appears to still be a template. Please fill it in.")
                continue

            contents[key] = _truncate_if_needed(raw.strip())
            files_used.append(filename)
        else:
            if key in REQUIRED_FILES:
                contents[key] = f"No {key} context provided."

    # ── Build the prompt ─────────────────────────────────────────────────

    sections: list[str] = []

    sections.append(
        "You are a senior software engineer performing blast radius analysis.\n"
        "\n"
        "You are given context from a Jira ticket and a GitHub PR/commit.\n"
        "Your job is to:\n"
        "  1. Understand what code change was made\n"
        "  2. Identify ALL modules / files / services that may be impacted\n"
        "  3. Assess the risk level (LOW / MEDIUM / HIGH / CRITICAL)\n"
        "  4. Provide specific, actionable guidance\n"
        "\n"
        "Think deeply about the impact chain — how does one change ripple through the system?"
    )

    # Jira context
    jira = contents.get("jira", "No Jira context provided.")
    sections.append(
        f"── JIRA CONTEXT ──────────────────────────────────────────────────────────────\n"
        f"{jira}"
    )

    # GitHub context
    github = contents.get("github", "No GitHub context provided.")
    sections.append(
        f"── GITHUB PR / DIFF ──────────────────────────────────────────────────────────\n"
        f"{github}"
    )

    # Optional: code before
    if "code_before" in contents:
        sections.append(
            f"── ORIGINAL CODE (before change) ─────────────────────────────────────────────\n"
            f"{contents['code_before']}"
        )

    # Optional: code after
    if "code_after" in contents:
        sections.append(
            f"── MODIFIED CODE (after change) ──────────────────────────────────────────────\n"
            f"{contents['code_after']}"
        )

    # Optional: repo structure
    if "repo_structure" in contents:
        sections.append(
            f"── REPOSITORY STRUCTURE ──────────────────────────────────────────────────────\n"
            f"{contents['repo_structure']}"
        )

    # Output format instructions
    sections.append(
        "── OUTPUT FORMAT ─────────────────────────────────────────────────────────────\n"
        "Respond with EXACTLY these 6 sections using the headers shown below.\n"
        "Be specific — name actual files, functions, and line numbers when possible.\n"
        "\n"
        "## 1. WHAT WAS DONE\n"
        "[Concise summary of the code change — what was added, removed, or modified]\n"
        "\n"
        "## 2. ROOT CAUSE / RISK ORIGIN\n"
        "[Why this change introduces risk, or what underlying problem it solves]\n"
        "\n"
        "## 3. IMPACTED MODULES\n"
        "[List EVERY file, module, service, or API affected — with a one-line reason per item]\n"
        "\n"
        "## 4. RISK LEVEL\n"
        "[Choose exactly one: LOW / MEDIUM / HIGH / CRITICAL]\n"
        "[Provide a 2-3 sentence justification]\n"
        "\n"
        "## 5. SUGGESTED FIX / MITIGATION\n"
        "[Concrete, numbered steps or code snippets to reduce the blast radius]\n"
        "\n"
        "## 6. IMPACT CHAIN EXPLANATION\n"
        "[Step-by-step trace: how does the change propagate through the system?\n"
        " Show the dependency chain from the changed file outward.]"
    )

    prompt = "\n\n".join(sections)
    return prompt, files_used, warnings
