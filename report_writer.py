"""
Blast Radius Agent — Report Writer
====================================
Parses the AI's output into structured sections, pretty-prints to
the terminal with color coding, and saves reports to disk.
"""

import os
import re
from datetime import datetime
from config import OUTPUT_DIR, MODEL_NAME


# ── ANSI Color Codes ────────────────────────────────────────────────────────

class Colors:
    """ANSI escape codes for terminal coloring."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    MAGENTA = "\033[95m"

    BG_RED = "\033[41m"
    BG_YELLOW = "\033[43m"
    BG_CYAN = "\033[46m"
    BG_GREEN = "\033[42m"


# ── Section Parsing ──────────────────────────────────────────────────────────

SECTION_HEADERS = [
    "1. WHAT WAS DONE",
    "2. ROOT CAUSE / RISK ORIGIN",
    "3. IMPACTED MODULES",
    "4. RISK LEVEL",
    "5. SUGGESTED FIX / MITIGATION",
    "6. IMPACT CHAIN EXPLANATION",
]

SECTION_DISPLAY_NAMES = {
    "1. WHAT WAS DONE": "WHAT WAS DONE",
    "2. ROOT CAUSE / RISK ORIGIN": "ROOT CAUSE / RISK ORIGIN",
    "3. IMPACTED MODULES": "IMPACTED MODULES",
    "4. RISK LEVEL": "RISK LEVEL",
    "5. SUGGESTED FIX / MITIGATION": "SUGGESTED FIX / MITIGATION",
    "6. IMPACT CHAIN EXPLANATION": "IMPACT CHAIN",
}


def parse_sections(raw_output: str) -> dict[str, str]:
    """
    Parse the AI's output into named sections.

    Splits on ## markers (e.g., '## 1. WHAT WAS DONE').
    Falls back to returning the raw output as a single section.
    """
    sections: dict[str, str] = {}

    # Try to find each section using regex
    for i, header in enumerate(SECTION_HEADERS):
        # Build pattern to match this section header
        pattern = re.compile(
            r"##\s*" + re.escape(header) + r"\s*\n(.*?)(?=##\s*\d+\.|$)",
            re.DOTALL | re.IGNORECASE,
        )
        match = pattern.search(raw_output)
        if match:
            sections[header] = match.group(1).strip()

    # If we couldn't parse any sections, return the raw output
    if not sections:
        sections["RAW OUTPUT"] = raw_output.strip()

    return sections


def _detect_risk_level(risk_text: str) -> str:
    """Extract the risk level keyword from the risk section."""
    risk_upper = risk_text.upper()
    if "CRITICAL" in risk_upper:
        return "CRITICAL"
    elif "HIGH" in risk_upper:
        return "HIGH"
    elif "MEDIUM" in risk_upper:
        return "MEDIUM"
    elif "LOW" in risk_upper:
        return "LOW"
    return "UNKNOWN"


def _risk_color(level: str) -> str:
    """Return the ANSI color code for a risk level."""
    return {
        "CRITICAL": Colors.RED,
        "HIGH": Colors.YELLOW,
        "MEDIUM": Colors.CYAN,
        "LOW": Colors.GREEN,
        "UNKNOWN": Colors.WHITE,
    }.get(level, Colors.WHITE)


def _risk_emoji(level: str) -> str:
    """Return an emoji for the risk level."""
    return {
        "CRITICAL": "🔴",
        "HIGH": "🟠",
        "MEDIUM": "🟡",
        "LOW": "🟢",
        "UNKNOWN": "⚪",
    }.get(level, "⚪")


# ── Terminal Pretty-Print ────────────────────────────────────────────────────

def print_report(sections: dict[str, str], timestamp: str, files_used: list[str]):
    """Print a beautifully formatted report to the terminal."""

    c = Colors
    width = 64

    # ── Header Box ───────────────────────────────────────────────────
    print()
    print(f"{c.BOLD}{c.CYAN}╔{'═' * width}╗{c.RESET}")
    print(f"{c.BOLD}{c.CYAN}║{c.WHITE}{'BLAST RADIUS ANALYSIS REPORT':^{width}}{c.CYAN}║{c.RESET}")
    print(f"{c.BOLD}{c.CYAN}║{c.DIM}  Generated: {timestamp:<{width - 14}}{c.BOLD}{c.CYAN}║{c.RESET}")
    print(f"{c.BOLD}{c.CYAN}║{c.DIM}  Model: {MODEL_NAME:<{width - 10}}{c.BOLD}{c.CYAN}║{c.RESET}")
    if files_used:
        files_str = ", ".join(files_used)
        print(f"{c.BOLD}{c.CYAN}║{c.DIM}  Inputs: {files_str:<{width - 11}}{c.BOLD}{c.CYAN}║{c.RESET}")
    print(f"{c.BOLD}{c.CYAN}╚{'═' * width}╝{c.RESET}")

    # ── Sections ─────────────────────────────────────────────────────
    for header, content in sections.items():
        display_name = SECTION_DISPLAY_NAMES.get(header, header)

        # Special formatting for RISK LEVEL section
        if "RISK LEVEL" in header:
            risk_level = _detect_risk_level(content)
            risk_clr = _risk_color(risk_level)
            emoji = _risk_emoji(risk_level)

            print()
            print(f"  {c.BOLD}{c.WHITE}► {display_name}{c.RESET}")
            print(f"  {c.DIM}{'─' * (width - 2)}{c.RESET}")
            print(f"  {risk_clr}{c.BOLD}{emoji}  {risk_level}{c.RESET}")
            print()
            for line in content.splitlines():
                # Skip lines that just say the risk level
                stripped = line.strip()
                if stripped and stripped.upper() not in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
                    print(f"  {c.DIM}{line}{c.RESET}")
        else:
            print()
            print(f"  {c.BOLD}{c.WHITE}► {display_name}{c.RESET}")
            print(f"  {c.DIM}{'─' * (width - 2)}{c.RESET}")
            for line in content.splitlines():
                print(f"  {line}")

    print()
    print(f"  {c.DIM}{'─' * (width - 2)}{c.RESET}")
    print()


# ── Save Report to File ─────────────────────────────────────────────────────

def save_report(
    raw_output: str,
    sections: dict[str, str],
    timestamp: str,
    files_used: list[str],
) -> str:
    """
    Save the report to outputs/analysis_<timestamp>.txt

    Returns:
        The path to the saved file.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    safe_ts = timestamp.replace(":", "-").replace(" ", "_")
    filename = f"analysis_{safe_ts}.txt"
    filepath = os.path.join(OUTPUT_DIR, filename)

    lines: list[str] = []
    lines.append("=" * 66)
    lines.append("  BLAST RADIUS ANALYSIS REPORT")
    lines.append(f"  Generated: {timestamp}")
    lines.append(f"  Model: {MODEL_NAME}")
    if files_used:
        lines.append(f"  Inputs: {', '.join(files_used)}")
    lines.append("=" * 66)
    lines.append("")

    for header, content in sections.items():
        display_name = SECTION_DISPLAY_NAMES.get(header, header)
        lines.append(f"► {display_name}")
        lines.append("─" * 62)
        lines.append(content)
        lines.append("")

    lines.append("=" * 66)
    lines.append("  END OF REPORT")
    lines.append("=" * 66)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return filepath


# ── Main Parse + Save Entry Point ────────────────────────────────────────────

def parse_and_save(
    raw_output: str,
    files_used: list[str],
    save: bool = True,
    quiet: bool = False,
) -> str | None:
    """
    Parse the AI output, optionally save to disk, and optionally print.

    Args:
        raw_output: The raw string from the NVIDIA API.
        files_used: List of input file names that were used.
        save: Whether to save the report to disk.
        quiet: If True, skip terminal printing.

    Returns:
        Path to the saved file, or None if not saved.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sections = parse_sections(raw_output)

    if not quiet:
        print_report(sections, timestamp, files_used)

    saved_path = None
    if save:
        saved_path = save_report(raw_output, sections, timestamp, files_used)
        if not quiet:
            print(f"  💾 Report saved to: {Colors.CYAN}{saved_path}{Colors.RESET}")
            print()

    return saved_path
