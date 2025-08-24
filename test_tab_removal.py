#!/usr/bin/env python3
"""
Test script to verify Tab key handler and help text removal.
"""

import sys
import os

# Add the parent directory to sys.path so we can import the game
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from RogueSignalProtocol import UIRenderer

def test_tab_removal():
    """Test that Tab key references are removed from help."""
    print("Testing Tab Key Removal...")
    print("=" * 40)
    
    # Check help system
    ui_renderer = UIRenderer()
    help_sections = ui_renderer._get_help_sections()
    help_text = " ".join([text for text, _ in help_sections])
    
    print("Checking help system:")
    
    # Check for Tab references
    tab_references = [
        "Tab:" in help_text,
        "tab" in help_text.lower(),
        "Toggle patrol" in help_text,
        "patrol route visibility" in help_text
    ]
    
    has_tab_references = any(tab_references)
    
    if has_tab_references:
        print("  [FAIL] Help still contains Tab key references")
        if "Tab:" in help_text:
            print("    - Found 'Tab:' in help text")
        if "Toggle patrol" in help_text:
            print("    - Found 'Toggle patrol' in help text")
    else:
        print("  [OK] No Tab key references found in help")
    
    # Check that other interface commands are still there
    interface_commands = [
        "?: This help screen" in help_text,
        "ESC: Cancel" in help_text,
        "I: Open inventory" in help_text or "I:" in help_text
    ]
    
    print("\nChecking other interface commands still present:")
    for i, present in enumerate(interface_commands):
        commands = ["Help command (?)", "ESC command", "Inventory command (I)"]
        status = "[OK]" if present else "[MISSING]"
        print(f"  {status} {commands[i]}")
    
    success = not has_tab_references and all(interface_commands)
    
    if success:
        print(f"\n[SUCCESS] Tab key references removed, other commands preserved!")
    else:
        print(f"\n[PARTIAL] Some issues found with help system cleanup")
    
    return success

if __name__ == "__main__":
    test_tab_removal()