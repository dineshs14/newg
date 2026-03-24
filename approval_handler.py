"""
Blast Radius Agent — Approval Handler
======================================
Processes approved code changes from the HTML report and orchestrates patching.
"""

import json
import os
from pathlib import Path
from typing import Optional
from code_patcher import CodePatcher


class ApprovalHandler:
    """Handle user approvals from HTML and apply changes."""

    def __init__(self, project_root: str = "."):
        """Initialize approval handler."""
        self.project_root = Path(project_root).resolve()
        self.patcher = CodePatcher(str(self.project_root))
        self.approvals: dict = {}

    def load_approvals(self, approvals_json: str) -> bool:
        """
        Load approvals from JSON structure.

        Expected format:
        {
            "ticket_id": "KS-107",
            "approved_changes": [
                {
                    "file": "src/types.ts",
                    "operation": "modify",
                    "diff": "..."
                },
                ...
            ]
        }
        """
        try:
            if isinstance(approvals_json, str) and approvals_json.strip().startswith("{"):
                self.approvals = json.loads(approvals_json)
            else:
                # Try to load from file
                with open(approvals_json, "r") as f:
                    self.approvals = json.load(f)
            return True
        except Exception as e:
            print(f"  ✗ Failed to load approvals: {e}")
            return False

    def set_approvals(self, approvals: dict):
        """Directly set approvals dictionary."""
        self.approvals = approvals

    def preview_changes(self) -> str:
        """Return a human-readable preview of approved changes."""
        if not self.approvals or "approved_changes" not in self.approvals:
            return "No approved changes found."

        lines = []
        lines.append(f"📋 Approved Changes for {self.approvals.get('ticket_id', 'Unknown')}")
        lines.append("─" * 60)

        for i, change in enumerate(self.approvals.get("approved_changes", []), 1):
            filepath = change.get("file", "unknown")
            operation = change.get("operation", "unknown")
            lines.append(f"\n{i}. {operation.upper()}: {filepath}")

            if operation == "modify" and "diff" in change:
                diff_lines = change["diff"].split("\n")[:5]  # Show first 5 lines
                for line in diff_lines:
                    lines.append(f"   {line}")
                if len(change["diff"].split("\n")) > 5:
                    lines.append(f"   ... ({len(change['diff'].split(chr(10))) - 5} more lines)")

        lines.append("\n" + "─" * 60)
        return "\n".join(lines)

    def apply_all_changes(self, confirm: bool = True) -> tuple[bool, str]:
        """
        Apply all approved changes to the codebase.

        Returns:
            (success, message)
        """
        if not self.approvals or "approved_changes" not in self.approvals:
            return False, "No approved changes to apply."

        print("\n" + "─" * 60)
        print(self.preview_changes())
        print("─" * 60 + "\n")

        if confirm:
            response = input("  ❓ Apply these changes? (yes/no): ").strip().lower()
            if response != "yes":
                return False, "Changes not applied (user cancelled)."

        results = []
        for change in self.approvals.get("approved_changes", []):
            filepath = change.get("file")
            operation = change.get("operation")
            content = change.get("content")
            diff = change.get("diff")

            success, msg = self.patcher.apply_change(
                filepath=filepath,
                operation=operation,
                content=content,
                unified_diff=diff,
                confirm=False,  # Already confirmed above
            )

            results.append((success, msg))
            print(f"  {msg}")

            if not success:
                if not confirm:
                    # Non-interactive mode: keep processing remaining changes.
                    continue
                # Ask to rollback
                rollback = input("    Continue with next change? (yes/no): ").strip().lower()
                if rollback != "yes":
                    self.patcher.rollback()
                    return False, "Operation aborted. Changes rolled back."

        applied_count = len([r for r in results if r[0]])
        return True, f"✓ Applied {applied_count}/{len(results)} change(s)."

    def save_approved_state(self, output_file: str = "approvals.json"):
        """Save the current approvals state to a JSON file."""
        try:
            output_path = self.project_root / output_file
            with open(output_path, "w") as f:
                json.dump(self.approvals, f, indent=2)
            return True, f"✓ Approvals saved to {output_path}"
        except Exception as e:
            return False, f"✗ Failed to save approvals: {e}"

    def get_change_summary(self) -> dict:
        """Get summary of changes."""
        return {
            "ticket_id": self.approvals.get("ticket_id"),
            "total_approved": len(self.approvals.get("approved_changes", [])),
            "patcher_summary": self.patcher.get_summary(),
        }
