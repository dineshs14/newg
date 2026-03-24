#!/usr/bin/env python3
"""
Blast Radius Agent — Main Entry Point
=======================================
CLI that ties together prompt building, NVIDIA API calls,
and report generation. Works on Windows, Mac, and Linux.

Usage:
    python agent.py                     # Basic run
    python agent.py --demo              # Demo with mock data (no API key)
    python agent.py --show-thinking     # Show AI reasoning trace
    python agent.py --dry-run           # Preview prompt, no API call
    python agent.py --list-inputs       # Show detected input files
    python agent.py --no-save           # Print only, don't save
    python agent.py --quiet             # Save only, no terminal output
    python agent.py --inputs ./my_dir   # Custom inputs directory
    python agent.py --repo ./my-project # Auto-detect git diff
    python agent.py --watch             # Re-run every 60s on file changes
"""

import argparse
import os
import subprocess
import sys
import time
import hashlib
import webbrowser

# Ensure the script's directory is in the path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prompt_builder import build_prompt, list_inputs
from nvidia_client import call_nvidia
from report_writer import parse_and_save, parse_sections, Colors
from html_report import save_html_report
from demo_data import DEMO_RESPONSE


def get_default_inputs_dir() -> str:
    """Return the default inputs directory relative to this script."""
    app_dir = os.environ.get("BLAST_RADIUS_APP_DIR", "").strip()
    if app_dir:
        return os.path.join(app_dir, "inputs")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "inputs")


def auto_detect_git_diff(repo_path: str, inputs_dir: str) -> bool:
    """
    Run `git diff HEAD` in the given repo and write output to github.txt.

    Returns True if diff was written successfully.
    """
    try:
        result = subprocess.run(
            ["git", "diff", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            print(f"  ⚠ git diff failed: {result.stderr.strip()}")
            return False

        diff_output = result.stdout.strip()
        if not diff_output:
            for branch in ["main", "master"]:
                result = subprocess.run(
                    ["git", "diff", branch],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0 and result.stdout.strip():
                    diff_output = result.stdout.strip()
                    break

        if not diff_output:
            print("  ⚠ No git diff output found (no changes detected).")
            return False

        log_result = subprocess.run(
            ["git", "log", "--oneline", "-5"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10,
        )
        recent_commits = log_result.stdout.strip() if log_result.returncode == 0 else ""

        branch_result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10,
        )
        current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"

        github_path = os.path.join(inputs_dir, "github.txt")
        with open(github_path, "w", encoding="utf-8") as f:
            f.write(f"AUTO-DETECTED GIT DIFF\n")
            f.write(f"Repository: {os.path.abspath(repo_path)}\n")
            f.write(f"Branch: {current_branch}\n")
            f.write(f"\nRecent Commits:\n{recent_commits}\n")
            f.write(f"\nDIFF:\n{diff_output}\n")

        print(f"  ✓ Git diff written to {github_path}")
        return True

    except FileNotFoundError:
        print("  ✖ git is not installed or not in PATH.")
        return False
    except subprocess.TimeoutExpired:
        print("  ✖ git diff timed out.")
        return False


# ── Commands ─────────────────────────────────────────────────────────────────


def cmd_list_inputs(inputs_dir: str):
    """Print a listing of all input files and their status."""
    c = Colors
    print()
    print(f"  {c.BOLD}📁 Input Files ({inputs_dir}){c.RESET}")
    print(f"  {'─' * 56}")

    info = list_inputs(inputs_dir)
    for key, data in info.items():
        status = f"{c.GREEN}✓ Found{c.RESET}" if data["exists"] else f"{c.RED}✗ Missing{c.RESET}"
        size = f"({data['size_kb']:.1f} KB)" if data["exists"] else ""
        req = f"{c.DIM}(required){c.RESET}" if data["required"] else f"{c.DIM}(optional){c.RESET}"
        print(f"  {status}  {data['filename']:<22} {size:<14} {req}")

    print()


def cmd_dry_run(inputs_dir: str):
    """Build and display the prompt without calling the API."""
    c = Colors
    prompt, files_used, warnings = build_prompt(inputs_dir)

    if warnings:
        print()
        for w in warnings:
            print(f"  {c.YELLOW}{w}{c.RESET}")

    print()
    print(f"  {c.BOLD}{c.CYAN}── DRY RUN: ASSEMBLED PROMPT ─────────────────────────────{c.RESET}")
    print(f"  {c.DIM}Files used: {', '.join(files_used) if files_used else 'none'}{c.RESET}")
    print(f"  {c.DIM}Prompt length: {len(prompt):,} characters{c.RESET}")
    print(f"  {c.DIM}{'─' * 56}{c.RESET}")
    print()
    print(prompt)
    print()
    print(f"  {c.DIM}{'─' * 56}{c.RESET}")
    print(f"  {c.GREEN}✓ Dry run complete. No API call made.{c.RESET}")
    print()


def cmd_analyze(
    inputs_dir: str,
    show_thinking: bool,
    save: bool,
    quiet: bool,
    demo: bool,
    open_browser: bool,
):
    """Run the full analysis pipeline."""
    c = Colors
    from datetime import datetime

    # Build prompt
    if not quiet:
        print()
        print(f"  {c.BOLD}{c.CYAN}━━━ BLAST RADIUS AGENT ━━━{c.RESET}")
        if demo:
            print(f"  {c.MAGENTA}🎮 DEMO MODE — using mock data, no API call{c.RESET}")
        print()

    prompt, files_used, warnings = build_prompt(inputs_dir)

    if warnings and not quiet:
        for w in warnings:
            print(f"  {c.YELLOW}{w}{c.RESET}")
        print()

    if not quiet:
        print(f"  📄 Input files: {', '.join(files_used) if files_used else 'none'}")
        print(f"  📏 Prompt size: {len(prompt):,} characters")
        print()

    # Get response (demo or real)
    if demo:
        response = DEMO_RESPONSE
        if not quiet:
            print(f"  {c.GREEN}✓ Using demo response (no API call){c.RESET}")
            print()
    else:
        response = call_nvidia(prompt, show_thinking=show_thinking)

    if not response:
        print(f"  {c.RED}✖ No response from API. Aborting.{c.RESET}")
        sys.exit(1)

    # Parse, print, and save TXT
    saved_txt = parse_and_save(
        raw_output=response,
        files_used=files_used,
        save=save,
        quiet=quiet,
    )

    # Save HTML + open in browser
    if save or open_browser:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sections = parse_sections(response)

        html_path = save_html_report(
            sections=sections,
            timestamp=timestamp,
            files_used=files_used,
            is_demo=demo,
        )

        if not quiet:
            print(f"  🌐 HTML report: {c.CYAN}{html_path}{c.RESET}")
            print()

        if open_browser:
            # file:// URL works cross-platform
            url = f"file:///{html_path.replace(os.sep, '/')}"
            if not quiet:
                print(f"  🚀 Opening report in browser...")
            webbrowser.open(url)

    if quiet and saved_txt:
        print(saved_txt)


# ── Watch Mode ───────────────────────────────────────────────────────────────


def _hash_inputs(inputs_dir: str) -> str:
    """Hash all input file contents to detect changes."""
    hasher = hashlib.md5()
    for filename in sorted(os.listdir(inputs_dir)):
        filepath = os.path.join(inputs_dir, filename)
        if os.path.isfile(filepath):
            try:
                with open(filepath, "rb") as f:
                    hasher.update(f.read())
            except Exception:
                pass
    return hasher.hexdigest()


def cmd_watch(inputs_dir: str, interval: int, demo: bool):
    """Watch input files and re-run analysis when they change."""
    c = Colors

    print()
    print(f"  {c.BOLD}{c.CYAN}━━━ BLAST RADIUS AGENT — WATCH MODE ━━━{c.RESET}")
    print(f"  {c.DIM}Monitoring: {inputs_dir}{c.RESET}")
    print(f"  {c.DIM}Interval: every {interval} seconds{c.RESET}")
    if demo:
        print(f"  {c.MAGENTA}🎮 DEMO MODE active{c.RESET}")
    print(f"  {c.DIM}Press Ctrl+C to stop{c.RESET}")
    print()

    last_hash = None
    run_count = 0

    try:
        while True:
            current_hash = _hash_inputs(inputs_dir)

            if current_hash != last_hash:
                last_hash = current_hash
                run_count += 1

                from datetime import datetime
                now = datetime.now().strftime("%H:%M:%S")

                print(f"  {c.YELLOW}⟳ [{now}] Change detected (run #{run_count}){c.RESET}")
                print()

                try:
                    cmd_analyze(
                        inputs_dir=inputs_dir,
                        show_thinking=False,
                        save=True,
                        quiet=False,
                        demo=demo,
                        open_browser=(run_count == 1),  # Only open browser on first run
                    )
                except SystemExit:
                    pass  # Don't exit on API errors in watch mode
                except Exception as e:
                    print(f"  {c.RED}✖ Error during analysis: {e}{c.RESET}")

                print(f"  {c.DIM}⏳ Waiting for next change...{c.RESET}")
                print()
            else:
                # Show a heartbeat every 5 intervals
                if run_count == 0:
                    from datetime import datetime
                    now = datetime.now().strftime("%H:%M:%S")
                    print(f"\r  {c.DIM}⏳ [{now}] Waiting for input changes...{c.RESET}", end="")

            time.sleep(interval)

    except KeyboardInterrupt:
        print()
        print(f"\n  {c.GREEN}✓ Watch mode stopped. {run_count} analysis run(s) completed.{c.RESET}")
        print()


# ── Main ─────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="🔬 Blast Radius Analysis Agent — Powered by NVIDIA Nemotron",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python agent.py --demo                 # Quick demo (no API key needed)
  python agent.py --demo --open          # Demo + auto-open in browser
  python agent.py                        # Run real analysis
  python agent.py --show-thinking        # Show AI reasoning
  python agent.py --dry-run              # Preview prompt only
  python agent.py --list-inputs          # Check input files
  python agent.py --repo ./my-project    # Auto-detect git diff
  python agent.py --watch                # Re-run on input changes
  python agent.py --watch --demo         # Watch mode with demo data
        """,
    )

    parser.add_argument(
        "--inputs", type=str, default=None,
        help="Path to the inputs directory (default: ./inputs)",
    )
    parser.add_argument(
        "--demo", action="store_true",
        help="Use mock data instead of calling the API (no API key needed)",
    )
    parser.add_argument(
        "--show-thinking", action="store_true",
        help="Display the model's internal reasoning trace",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Build and print the prompt without calling the API",
    )
    parser.add_argument(
        "--list-inputs", action="store_true",
        help="List detected input files and their status",
    )
    parser.add_argument(
        "--no-save", action="store_true",
        help="Print report to terminal without saving to file",
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Save report without printing to terminal",
    )
    parser.add_argument(
        "--open", action="store_true",
        help="Auto-open the HTML report in your default browser",
    )
    parser.add_argument(
        "--repo", type=str, default=None,
        help="Path to a git repo — auto-runs git diff and writes github.txt",
    )
    parser.add_argument(
        "--watch", action="store_true",
        help="Watch input files and re-run analysis on changes (every 60s)",
    )
    parser.add_argument(
        "--interval", type=int, default=60,
        help="Watch interval in seconds (default: 60)",
    )

    args = parser.parse_args()

    # Resolve inputs directory
    inputs_dir = args.inputs if args.inputs else get_default_inputs_dir()
    inputs_dir = os.path.abspath(inputs_dir)

    # Ensure inputs directory exists
    os.makedirs(inputs_dir, exist_ok=True)

    # Auto-detect git diff if --repo is specified
    if args.repo:
        repo_path = os.path.abspath(args.repo)
        if not os.path.isdir(repo_path):
            print(f"  ✖ Repository path not found: {repo_path}")
            sys.exit(1)
        if not os.path.isdir(os.path.join(repo_path, ".git")):
            print(f"  ✖ Not a git repository: {repo_path}")
            sys.exit(1)
        print(f"  🔍 Auto-detecting git diff from: {repo_path}")
        auto_detect_git_diff(repo_path, inputs_dir)

    # Handle commands
    if args.list_inputs:
        cmd_list_inputs(inputs_dir)
    elif args.dry_run:
        cmd_dry_run(inputs_dir)
    elif args.watch:
        cmd_watch(
            inputs_dir=inputs_dir,
            interval=args.interval,
            demo=args.demo,
        )
    else:
        cmd_analyze(
            inputs_dir=inputs_dir,
            show_thinking=args.show_thinking,
            save=not args.no_save,
            quiet=args.quiet,
            demo=args.demo,
            open_browser=args.open,
        )


if __name__ == "__main__":
    main()
