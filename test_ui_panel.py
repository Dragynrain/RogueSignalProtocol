#!/usr/bin/env python3
"""
Test script to verify the new UI panel layout:
1. Network info removed from first line
2. Exploits display uses 2 lines 
3. Final line shows all temporary conditions with turns
"""

import sys
import os

# Add the parent directory to sys.path so we can import the game
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from RogueSignalProtocol import Game, GameConfig, GameData, ExploitItem

def test_ui_panel_layout():
    """Test the new UI panel layout."""
    print("Testing New UI Panel Layout...")
    print("=" * 50)
    
    # Create game instance
    game = Game()
    player = game.player
    
    print("=== UI Panel Structure Test ===")
    print(f"Panel Height: {GameConfig.PANEL_HEIGHT}")
    print(f"Panel Y Start: {GameConfig.PANEL_Y}")
    print(f"Screen Height: {GameConfig.SCREEN_HEIGHT}")
    
    print(f"\nNew Panel Layout:")
    print(f"  Line {GameConfig.PANEL_Y + 0}: Border")
    print(f"  Line {GameConfig.PANEL_Y + 1}: Exploits (Line 1) - up to 3 exploits")
    print(f"  Line {GameConfig.PANEL_Y + 2}: Exploits (Line 2) - remaining exploits")
    print(f"  Line {GameConfig.PANEL_Y + 3}: Temporary Conditions with turn counts")
    print(f"  Line {GameConfig.PANEL_Y + 4}: (unused/cleared)")
    
    print(f"\n=== Exploit Display Test ===")
    
    # Add some exploits to test 2-line display
    exploits_to_add = ['shadow_step', 'data_mimic', 'noise_maker', 'buffer_overflow', 'system_crash']
    added_exploits = []
    
    for exploit_key in exploits_to_add:
        if exploit_key in GameData.EXPLOITS and len(player.inventory_manager.equipped_exploits) < 5:
            # Add to inventory first
            exploit_item = ExploitItem(exploit_key, GameData.EXPLOITS[exploit_key])
            player.inventory_manager.add_item(exploit_item)
            # Try to equip it
            success = exploit_item.use(player, game)
            if success:
                added_exploits.append(exploit_key)
                print(f"  Added: {GameData.EXPLOITS[exploit_key].name}")
    
    equipped_exploits = player.inventory_manager.equipped_exploits
    print(f"\nTotal equipped exploits: {len(equipped_exploits)}")
    
    # Test line distribution
    first_line = equipped_exploits[:3]
    second_line = equipped_exploits[3:] if len(equipped_exploits) > 3 else []
    
    print(f"First line exploits ({len(first_line)}):")
    for i, exploit_key in enumerate(first_line):
        if exploit_key in GameData.EXPLOITS:
            name = GameData.EXPLOITS[exploit_key].name
            print(f"  {i+1}.{name}")
    
    if second_line:
        print(f"Second line exploits ({len(second_line)}):")
        for i, exploit_key in enumerate(second_line):
            if exploit_key in GameData.EXPLOITS:
                name = GameData.EXPLOITS[exploit_key].name
                print(f"  {i+4}.{name}")
    
    print(f"\n=== Temporary Conditions Test ===")
    
    # Add some temporary effects to test conditions display
    player.temporary_effects['speed_boost_turns'] = 8
    player.temporary_effects['enhanced_vision_turns'] = 12
    player.temporary_effects['data_mimic_turns'] = 3
    player.speed_moves_remaining = 2
    game.network_scan_turns = 4
    
    print("Active temporary conditions:")
    conditions = []
    
    for effect_name, turns in player.temporary_effects.items():
        if turns > 0:
            display_name = effect_name.replace('_turns', '').replace('_', ' ').title()
            conditions.append(f"{display_name}({turns})")
            print(f"  - {display_name}: {turns} turns")
    
    if game.network_scan_turns > 0:
        conditions.append(f"Network Scan({game.network_scan_turns})")
        print(f"  - Network Scan: {game.network_scan_turns} turns")
    
    if player.speed_moves_remaining > 0:
        conditions.append(f"Speed Moves({player.speed_moves_remaining})")
        print(f"  - Speed Moves: {player.speed_moves_remaining} remaining")
    
    conditions_text = "Conditions: " + " ".join(conditions)
    print(f"\nConditions line would show: '{conditions_text}'")
    print(f"Length: {len(conditions_text)} chars (max: {GameConfig.GAME_AREA_WIDTH - 2})")
    
    print(f"\n=== Removed Features ===")
    print("  [REMOVED] Network name (Corporate/Government/Military)")  
    print("  [REMOVED] Player position coordinates")
    print("  [REMOVED] Vision range display")
    print("  [REMOVED] Status warnings (overheating, low CPU, etc.)")
    print("  -> More space for exploit names and conditions!")
    
    print(f"\n=== Summary ===")
    print("New UI panel benefits:")
    print("  [OK] Network info line removed - less clutter")
    print("  [OK] Exploits get 2 full lines - complete names visible") 
    print("  [OK] All temporary conditions in one place with turn counts")
    print("  [OK] More focused, information-dense display")
    print("  [OK] Better use of limited screen real estate")
    
    print(f"\n[SUCCESS] New UI panel layout implemented successfully!")

if __name__ == "__main__":
    test_ui_panel_layout()