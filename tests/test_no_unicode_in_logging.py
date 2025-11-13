#!/usr/bin/env python3
"""
Test to prevent Unicode characters in logging statements.

Windows logging handlers silently fail when encountering Unicode characters
that can't be encoded in CP1252, causing log messages to disappear without
raising exceptions. This test enforces ASCII-only logging.
"""

import re
from pathlib import Path


def test_no_unicode_in_logging_statements():
    """
    Verify no logging statements contain ANY non-ASCII (Unicode) characters.

    This prevents silent logging failures on Windows where the logging
    handler drops messages with Unicode characters it can't encode.
    """
    # Build regex pattern to match logging calls
    # Matches: logging.info("..."), logging.debug(f"..."), etc.
    # Captures everything after the opening quote/paren
    logging_pattern = re.compile(
        r"logging\.(debug|info|warning|error|critical)\s*\((.+)\)", re.DOTALL
    )

    violations = []

    # Scan all Python files except tests and this file
    project_root = Path(__file__).parent.parent
    for py_file in project_root.glob("*.py"):
        if py_file.name == "test_no_unicode_in_logging.py":
            continue

        try:
            content = py_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Skip files with encoding issues
            continue

        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            # Check if this line contains a logging call
            match = logging_pattern.search(line)
            if match:
                log_content = match.group(2)  # The message part

                # Check every character in the logging message
                for char in log_content:
                    # Check if character is non-ASCII (ord > 127)
                    if ord(char) > 127:
                        violations.append(
                            {
                                "file": py_file.name,
                                "line": line_num,
                                "char": char,
                                "ord": ord(char),
                                "content": line.strip(),
                            }
                        )
                        break  # Only report first Unicode char per line

    # Report violations
    if violations:
        error_msg = "\n\nNon-ASCII (Unicode) characters found in logging statements:\n"
        error_msg += "=" * 80 + "\n"
        error_msg += "Windows logging handlers SILENTLY FAIL on Unicode characters!\n"
        error_msg += "This causes log messages to disappear without errors.\n"
        error_msg += "=" * 80 + "\n\n"

        for v in violations:
            error_msg += f"{v['file']}:{v['line']}\n"
            error_msg += f"  Character: '{v['char']}' (Unicode {v['ord']})\n"
            error_msg += f"  Line: {v['content']}\n\n"

        error_msg += "Fix: Replace Unicode with ASCII equivalents:\n"
        error_msg += "  ✓/✗ → [MATCH]/[MISMATCH] or OK/FAIL\n"
        error_msg += "  →/← → -> or <-\n"
        error_msg += "  💀 → [DEATH]\n"
        error_msg += "  ⚠️ → [WARNING]\n"
        error_msg += "  Any non-ASCII → ASCII equivalent\n"

        assert False, error_msg


if __name__ == "__main__":
    test_no_unicode_in_logging_statements()
    print("[OK] No Unicode in logging statements")
