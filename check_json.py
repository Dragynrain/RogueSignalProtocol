#!/usr/bin/env python3
"""
Quick JSON integrity checker for Rogue Signal Protocol data files.
Run this after making changes to verify files are still valid.
"""

import json
import sys
import os
from pathlib import Path


def check_json_file(filepath):
    """Check if a JSON file is valid and readable."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return True, f"OK - {len(data) if isinstance(data, (dict, list)) else 1} items"
    except FileNotFoundError:
        return False, "File not found"
    except json.JSONDecodeError as e:
        return False, f"JSON syntax error: {e}"
    except Exception as e:
        return False, f"Error: {e}"


def main():
    """Check all JSON files in the project."""
    json_files = [
        'game_data.json',
        'game_config.json', 
        'story_content.json',
        'user_settings.json'
    ]
    
    print("Checking JSON file integrity...")
    print("=" * 40)
    
    all_valid = True
    
    for filename in json_files:
        if os.path.exists(filename):
            is_valid, message = check_json_file(filename)
            status = "PASS" if is_valid else "FAIL"
            print(f"{filename:<20} {status:<4} {message}")
            if not is_valid:
                all_valid = False
        else:
            print(f"{filename:<20} SKIP File not found")
    
    print("=" * 40)
    if all_valid:
        print("All JSON files are valid!")
        sys.exit(0)
    else:
        print("Some JSON files have errors. Please fix them before running the game.")
        sys.exit(1)


if __name__ == "__main__":
    main()