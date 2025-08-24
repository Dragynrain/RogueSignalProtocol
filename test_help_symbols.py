#!/usr/bin/env python3
"""
Test script to verify the help system includes symbol explanations.
"""

import sys
import os

# Add the parent directory to sys.path so we can import the game
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from RogueSignalProtocol import UIRenderer

def test_help_symbols():
    """Test that help system includes symbol explanations."""
    print("Testing Help System Symbol Explanations...")
    print("=" * 60)
    
    # Create UI renderer to get help sections
    ui_renderer = UIRenderer()
    help_sections = ui_renderer._get_help_sections()
    
    # Display help content
    current_section = None
    for text, color in help_sections:
        if text.endswith(":") and not text.startswith("  "):
            current_section = text
            print(f"\n{current_section}")
            print("-" * len(current_section))
        elif text.strip():
            print(f"{text}")
        elif current_section:
            # Empty line, move to next section
            pass
    
    print(f"\n" + "=" * 60)
    print("Help System Verification:")
    
    # Check for key sections
    help_text = " ".join([text for text, _ in help_sections])
    
    checks = [
        ("MAP SYMBOLS", "MAP SYMBOLS:" in help_text),
        ("ITEMS & PICKUPS", "ITEMS & PICKUPS:" in help_text),
        ("Player symbol (@)", "Player character" in help_text),
        ("Data patches (!)", "Data patches" in help_text and "!" in help_text),
        ("Exploit programs (&)", "Exploit programs" in help_text and "&" in help_text),
        ("Cooling nodes (~)", "Cooling nodes" in help_text and "~" in help_text),
        ("CPU recovery (+)", "CPU recovery" in help_text and "+" in help_text),
        ("Updated enemy symbols", "S: Scanner" in help_text),
    ]
    
    all_passed = True
    for check_name, passed in checks:
        status = "[OK]" if passed else "[FAIL]"
        print(f"  {status} {check_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print(f"\n[SUCCESS] Help system includes comprehensive symbol explanations!")
    else:
        print(f"\n[WARNING] Some symbol explanations may be missing!")
    
    return all_passed

if __name__ == "__main__":
    test_help_symbols()