#!/usr/bin/env python3
"""
Balance data export tool for Rogue Signal Protocol.
Extracts balance values into a separate JSON file for easy modding.
"""

import json
from data_loading import DataLoader


def export_balance_data():
    """Export current balance configuration to a separate file."""
    try:
        # Load the current balance configuration
        balance = DataLoader.get_balance_config()
        item_effects = DataLoader.get_item_effects()
        
        # Create a comprehensive balance export
        export_data = {
            "balance_config": balance,
            "item_effects": item_effects,
            "metadata": {
                "description": "Exported balance configuration for modding",
                "export_version": "1.0",
                "compatible_game_version": "1.1+"
            }
        }
        
        # Write to balance export file
        with open('balance_export.json', 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print("Balance data exported to balance_export.json")
        print(f"Exported {len(balance)} balance sections and {len(item_effects)} item effects")
        
        # Show summary of what was exported
        print("\nExported sections:")
        for section_name, section_data in balance.items():
            if isinstance(section_data, dict):
                print(f"  {section_name}: {len(section_data)} settings")
            else:
                print(f"  {section_name}: 1 setting")
        
        return True
        
    except Exception as e:
        print(f"Failed to export balance data: {e}")
        return False


def import_balance_data():
    """Import balance configuration from balance_export.json back to game_data.json"""
    try:
        # Load the balance export
        with open('balance_export.json', 'r', encoding='utf-8') as f:
            export_data = json.load(f)
        
        # Load current game data
        game_data = DataLoader.load_game_data()
        
        # Update balance sections
        if 'balance_config' in export_data:
            game_data['balance'] = export_data['balance_config']
        
        if 'item_effects' in export_data:
            game_data['item_effects'] = export_data['item_effects']
        
        # Write back to game_data.json
        with open('game_data.json', 'w', encoding='utf-8') as f:
            json.dump(game_data, f, indent=2, ensure_ascii=False)
        
        print("Balance data imported back to game_data.json")
        return True
        
    except FileNotFoundError:
        print("balance_export.json not found. Run with --export first.")
        return False
    except Exception as e:
        print(f"Failed to import balance data: {e}")
        return False


def show_balance_summary():
    """Show a summary of current balance values."""
    try:
        balance = DataLoader.get_balance_config()
        
        print("=== Current Balance Configuration ===")
        print()
        
        # Player stats
        player_stats = balance.get('player_stats', {})
        print("PLAYER STATS:")
        for stat, value in player_stats.items():
            print(f"  {stat}: {value}")
        print()
        
        # Combat values
        combat = balance.get('combat', {})
        if combat:
            print("COMBAT:")
            for setting, value in combat.items():
                print(f"  {setting}: {value}")
            print()
        
        # Code patches
        code_patches = balance.get('code_patches', {})
        if code_patches:
            print("CODE PATCHES:")
            for setting, value in code_patches.items():
                print(f"  {setting}: {value}")
            print()
        
        # Temporary effects
        temp_effects = balance.get('temporary_effects', {})
        if temp_effects:
            print("TEMPORARY EFFECTS:")
            for effect, value in temp_effects.items():
                print(f"  {effect}: {value}")
        
        return True
        
    except Exception as e:
        print(f"Failed to show balance summary: {e}")
        return False


def main():
    """Main function with command line options."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python export_balance.py [--export|--import|--summary]")
        print()
        print("Options:")
        print("  --export   Export current balance to balance_export.json")
        print("  --import   Import balance from balance_export.json to game_data.json")
        print("  --summary  Show current balance configuration")
        sys.exit(1)
    
    option = sys.argv[1]
    
    if option == "--export":
        success = export_balance_data()
    elif option == "--import":
        success = import_balance_data()
    elif option == "--summary":
        success = show_balance_summary()
    else:
        print(f"Unknown option: {option}")
        success = False
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()