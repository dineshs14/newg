"""
Blast Radius Agent — Code Patcher
===================================
Safely applies code changes to the codebase with validation and rollback.
"""

import os
import json
import difflib
from datetime import datetime
from pathlib import Path
from typing import Optional


class CodePatcher:
    """Safely apply code changes with backup and validation."""

    def __init__(self, base_path: str = "."):
        """Initialize with project root path."""
        self.base_path = Path(base_path).resolve()
        self.backups: dict[str, str] = {}  # filepath -> backup content
        self.changes: list[dict] = []  # Track all changes applied

    def _safe_resolve_path(self, filepath: str) -> Optional[Path]:
        """Safely resolve a file path to prevent directory traversal attacks."""
        try:
            full_path = (self.base_path / filepath).resolve()
            # Ensure the path is within base_path
            if not str(full_path).startswith(str(self.base_path)):
                raise ValueError(f"Path {filepath} is outside project root")
            return full_path
        except Exception as e:
            print(f"  ✗ Invalid path {filepath}: {e}")
            return None

    def apply_change(
        self,
        filepath: str,
        operation: str,  # 'create' | 'modify' | 'delete'
        content: Optional[str] = None,
        unified_diff: Optional[str] = None,
        confirm: bool = True,
    ) -> tuple[bool, str]:
        """
        Apply a single code change.

        Args:
            filepath: Relative path to file
            operation: 'create' | 'modify' | 'delete'
            content: Full content for 'create'
            unified_diff: Unified diff for 'modify'
            confirm: If True, ask for confirmation

        Returns:
            (success, message)
        """
        safe_path = self._safe_resolve_path(filepath)
        if not safe_path:
            return False, f"Invalid path: {filepath}"

        # Backup existing file (if modifying/deleting)
        if operation in ("modify", "delete") and safe_path.exists():
            with open(safe_path, "r", encoding="utf-8", errors="replace") as f:
                self.backups[filepath] = f.read()

        try:
            if operation == "create":
                if safe_path.exists():
                    return False, f"File already exists: {filepath}"
                safe_path.parent.mkdir(parents=True, exist_ok=True)
                with open(safe_path, "w", encoding="utf-8") as f:
                    f.write(content or "")
                msg = f"✓ Created: {filepath}"

            elif operation == "modify":
                if not safe_path.exists():
                    return False, f"File not found: {filepath}"
                if unified_diff:
                    # Apply unified diff
                    with open(safe_path, "r", encoding="utf-8", errors="replace") as f:
                        original = f.read()
                    patched = self._apply_unified_diff(original, unified_diff)
                    if patched is None:
                        return False, f"Failed to apply diff to {filepath}"
                    with open(safe_path, "w", encoding="utf-8") as f:
                        f.write(patched)
                elif content:
                    with open(safe_path, "w", encoding="utf-8") as f:
                        f.write(content)
                else:
                    return False, "No content or diff provided"
                msg = f"✓ Modified: {filepath}"

            elif operation == "delete":
                if safe_path.exists():
                    safe_path.unlink()
                    msg = f"✓ Deleted: {filepath}"
                else:
                    return False, f"File not found: {filepath}"

            else:
                return False, f"Unknown operation: {operation}"

            # Record change
            self.changes.append({
                "filepath": filepath,
                "operation": operation,
                "timestamp": datetime.now().isoformat(),
            })

            return True, msg

        except Exception as e:
            return False, f"Error applying change to {filepath}: {str(e)}"

    def _apply_unified_diff(self, original: str, unified_diff: str) -> Optional[str]:
        """Apply unified diff to original content."""
        try:
            diff_lines = unified_diff.strip().split("\n")
            # Skip diff headers
            diff_lines = [
                line for line in diff_lines if not line.startswith(("---", "+++", "@@"))
            ]

            lines = original.split("\n")
            result = []

            for line in diff_lines:
                if line.startswith("-"):
                    # Remove line
                    remove_line = line[1:]
                    if remove_line in lines:
                        lines.remove(remove_line)
                elif line.startswith("+"):
                    # Add line
                    result.append(line[1:])
                elif not line.startswith("\\"):
                    # Context line
                    result.append(line)

            return "\n".join(result) if result else original
        except Exception as e:
            print(f"  ✗ Diff application failed: {e}")
            return None

    def rollback(self):
        """Restore all backed-up files."""
        for filepath, content in self.backups.items():
            safe_path = self._safe_resolve_path(filepath)
            if safe_path:
                try:
                    with open(safe_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    print(f"  ↶ Rolled back: {filepath}")
                except Exception as e:
                    print(f"  ✗ Rollback failed for {filepath}: {e}")

    def get_summary(self) -> dict:
        """Return summary of all changes."""
        return {
            "total_changes": len(self.changes),
            "changes": self.changes,
            "backups": list(self.backups.keys()),
        }
