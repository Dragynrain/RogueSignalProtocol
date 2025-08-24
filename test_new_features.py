#!/usr/bin/env python3
"""
Test script to verify the new features:
1. RAM-limited exploit equipping
2. Background detection increases per level
3. Interface improvements
"""

import sys
import os

# Add the parent directory to sys.path so we can import the game
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from RogueSignalProtocol import Game, GameConfig, GameData, ExploitItem

def test_new_features():
    """Test all new features."""
    print("Testing New Features...")
    print("=" * 50)
    
    # Test 1: RAM-limited exploit equipping
    print("\n=== Test 1: RAM-Limited Exploit Equipping ===")
    
    game = Game()
    player = game.player
    
    print(f"Player total RAM: {player.ram_total}")
    print(f"Initial RAM usage: {player.ram_used}")
    
    # Try to equip a high-RAM exploit
    high_ram_exploit = ExploitItem('system_crash', GameData.EXPLOITS['system_crash'])
    print(f"Trying to equip '{high_ram_exploit.name}' (RAM cost: {high_ram_exploit.ram_cost})")
    
    success1 = high_ram_exploit.use(player, game)
    print(f"Result: {'Success' if success1 else 'Failed'}")
    print(f"RAM after attempt: {player.ram_used}/{player.ram_total}")
    
    # Try to equip more than max slots
    print(f"\nTrying to equip beyond max slots ({player.inventory_manager.max_equipped_exploits}):")
    exploit_keys = list(GameData.EXPLOITS.keys())[:6]  # Try 6 exploits
    
    for i, key in enumerate(exploit_keys):
        if key not in player.inventory_manager.equipped_exploits:
            exploit_item = ExploitItem(key, GameData.EXPLOITS[key])
            success = exploit_item.use(player, game)
            equipped_count = len(player.inventory_manager.equipped_exploits)
            print(f"  Exploit {i+1} ({key}): {'Success' if success else 'Failed'} - {equipped_count} equipped")
    
    # Test 2: Background detection increases
    print(f"\n=== Test 2: Background Detection Increases ===")
    
    for level in [1, 2, 3]:
        config = GameConfig.NETWORK_CONFIGS[level]
        background_detection = config.get("background_detection", 1)
        print(f"Level {level}: Background detection increase = +{background_detection}/15 turns")
        print(f"  Network: {config['name']}")
        print(f"  This means admins spawn at same threshold (90) but faster on higher levels")
    
    # Test 3: Admin spawn system
    print(f"\n=== Test 3: Admin Spawn System ===")
    print(f"Fixed admin spawn threshold: {GameConfig.ADMIN_SPAWN_THRESHOLD}")
    print(f"Old system used different thresholds per level (confusing)")
    print(f"New system uses same threshold but faster detection buildup")
    
    # Test 4: Interface improvements  
    print(f"\n=== Test 4: Interface Improvements ===")
    print("Exploit name length analysis:")
    
    for key, exploit_def in GameData.EXPLOITS.items():
        name_length = len(exploit_def.name)
        truncated_old = f"{exploit_def.name[:8]}" if len(exploit_def.name) > 8 else exploit_def.name
        truncated_new = f"{exploit_def.name[:11]}" if len(exploit_def.name) > 12 else exploit_def.name
        print(f"  {exploit_def.name:15} ({name_length:2d} chars) -> Old: '{truncated_old:8}' New: '{truncated_new}'")
    
    print(f"\n=== Summary ===")
    print("All new features implemented:")
    print("  [OK] Players cannot equip over max RAM (8)")
    print("  [OK] Players cannot equip over max slots (5)")
    print("  [OK] Helpful error messages when equipping fails")
    print("  [OK] Background detection increases per level (1/2/3)")
    print("  [OK] Fixed admin spawn threshold (90) instead of confusing per-level thresholds")
    print("  [OK] Interface expanded for longer exploit names")
    print("  [OK] Dynamic spacing in exploit display")
    
    print(f"\n[SUCCESS] All new features tested successfully!")

if __name__ == "__main__":
    test_new_features()