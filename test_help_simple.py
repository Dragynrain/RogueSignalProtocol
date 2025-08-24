#!/usr/bin/env python3
"""
Simple test to verify help system has symbol explanations.
"""

import sys
import os

# Add the parent directory to sys.path so we can import the game
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from RogueSignalProtocol import UIRenderer

def test_help_symbols():
    """Test that help system includes symbol explanations."""
    print("Testing Help System Symbol Explanations...")
    print("=" * 50)
    
    # Create UI renderer to get help sections
    ui_renderer = UIRenderer()
    help_sections = ui_renderer._get_help_sections()
    
    # Convert to text for checking
    help_text = " ".join([text for text, _ in help_sections])
    
    print("\nChecking for symbol explanations:")
    
    checks = [
        ("MAP SYMBOLS section", "MAP SYMBOLS:" in help_text),
        ("ITEMS & PICKUPS section", "ITEMS & PICKUPS:" in help_text),
        ("Player symbol (@)", "@: Player character" in help_text),
        ("Data patches (!)", "!: Data patches" in help_text),
        ("Exploit programs (&)", "&: Exploit programs" in help_text),
        ("Cooling nodes (~)", "~: Cooling nodes" in help_text),
        ("CPU recovery (+)", "+: CPU recovery" in help_text),
        ("Updated enemy symbols", "S: Scanner" in help_text),
        ("Updated enemy symbols", "P: Patrol" in help_text),
        ("Updated enemy symbols", "B: Bot" in help_text),
    ]
    
    all_passed = True
    for check_name, passed in checks:
        status = "[OK]" if passed else "[FAIL]"
        print(f"  {status} {check_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print(f"\n[SUCCESS] Help system includes comprehensive symbol explanations!")
        print("Players can now press '?' in-game to see all symbols explained.")
    else:
        print(f"\n[WARNING] Some symbol explanations may be missing!")
    
    return all_passed

if __name__ == "__main__":
    test_help_symbols()