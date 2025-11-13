#!/usr/bin/env python3
"""
Test suite to ensure all logging statements use ASCII-safe characters.

Prevents UnicodeEncodeError on Windows console (CP1252 encoding) by catching
non-ASCII characters in logging calls during testing instead of at runtime.
"""

import os
import re

import pytest


class TestLoggingASCIISafety:
    """Test that all logging statements are ASCII-safe for cross-platform compatibility."""

    def _find_python_files(self):
        """Find all Python source files in the project."""
        python_files = []
        exclude_dirs = {".venv", "venv", "__pycache__", ".git", "build", "dist", ".pytest_cache"}

        for root, dirs, files in os.walk("."):
            # Remove excluded directories from traversal
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for file in files:
                if file.endswith(".py"):
                    python_files.append(os.path.join(root, file))

        return python_files

    def _extract_logging_calls(self, file_path):
        """
        Extract logging call strings from a Python file.

        Returns list of (line_number, logging_string) tuples.
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            pytest.skip(f"Could not read {file_path}: {e}")
            return []

        # Pattern to match logging calls: logging.debug/info/warning/error/critical
        # Captures the string argument (f-strings, regular strings, etc.)
        pattern = r'logging\.(debug|info|warning|error|critical)\s*\(\s*[rf]?["\']([^"\']*)["\']'

        violations = []
        for match in re.finditer(pattern, content):
            log_string = match.group(2)
            # Find line number by counting newlines up to this position
            line_num = content[: match.start()].count("\n") + 1

            # Check if string contains non-ASCII characters
            try:
                log_string.encode("ascii")
            except UnicodeEncodeError:
                violations.append((line_num, log_string, file_path))

        return violations

    def test_all_logging_statements_are_ascii_safe(self):
        """
        Verify that all logging statements can be encoded in ASCII.

        This prevents UnicodeEncodeError when logging to Windows console
        or ASCII-only log files.
        """
        python_files = self._find_python_files()
        assert len(python_files) > 0, "No Python files found in project"

        all_violations = []

        for file_path in python_files:
            violations = self._extract_logging_calls(file_path)
            all_violations.extend(violations)

        if all_violations:
            error_msg = "Found non-ASCII characters in logging statements:\n"
            for line_num, log_string, file_path in all_violations[:10]:  # Show first 10
                # Show problematic characters
                non_ascii = [c for c in log_string if ord(c) > 127]
                error_msg += f"\n  {file_path}:{line_num}"
                error_msg += f"\n    String: {repr(log_string)}"
                error_msg += f"\n    Non-ASCII chars: {non_ascii}\n"

            if len(all_violations) > 10:
                error_msg += f"\n... and {len(all_violations) - 10} more violations"

            pytest.fail(error_msg)

    def test_no_unicode_arrows_in_logging(self):
        """
        Specifically check for common Unicode arrow characters (→, ←, ↑, ↓).

        These were previously used and caused Windows console crashes.
        Use ASCII alternatives: ->, <-, ^, v
        """
        python_files = self._find_python_files()
        arrow_violations = []

        unicode_arrows = ["→", "←", "↑", "↓", "⇒", "⇐", "⇑", "⇓"]

        for file_path in python_files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        if "logging." in line:
                            for arrow in unicode_arrows:
                                if arrow in line:
                                    arrow_violations.append(
                                        (file_path, line_num, line.strip(), arrow)
                                    )
            except Exception:
                continue

        if arrow_violations:
            error_msg = "Found Unicode arrows in logging statements:\n"
            for file_path, line_num, line, arrow in arrow_violations[:5]:
                error_msg += f"\n  {file_path}:{line_num}"
                error_msg += f"\n    Contains: {repr(arrow)}"
                error_msg += f"\n    Line: {line}\n"

            pytest.fail(error_msg)

    def test_no_emojis_in_logging(self):
        """
        Check for emojis in logging statements.

        Emojis cannot be encoded in CP1252 (Windows console) or ASCII.
        Use text descriptions instead: [DEATH], [SUCCESS], [ERROR], etc.
        """
        python_files = self._find_python_files()
        emoji_violations = []

        # Common emojis that might appear in logging
        common_emojis = ["💀", "✅", "❌", "🎮", "🔥", "⚠️", "🚨", "🏆", "💡"]

        for file_path in python_files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        if "logging." in line:
                            for emoji in common_emojis:
                                if emoji in line:
                                    emoji_violations.append(
                                        (file_path, line_num, line.strip(), emoji)
                                    )
            except Exception:
                continue

        if emoji_violations:
            error_msg = "Found emojis in logging statements:\n"
            for file_path, line_num, line, emoji in emoji_violations[:5]:
                error_msg += f"\n  {file_path}:{line_num}"
                error_msg += f"\n    Contains: {emoji}"
                error_msg += f"\n    Line: {line}\n"

            error_msg += "\nReplace with ASCII: 💀 -> [DEATH], ✅ -> [OK], ❌ -> [FAIL]"
            pytest.fail(error_msg)
