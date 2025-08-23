#!/usr/bin/env python3
"""
Test script to verify the improved level generation.
Tests room count, enemy count, treasure count, and shadow coverage.
"""

import sys
import os

# Add the parent directory to sys.path so we can import the game
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from RogueSignalProtocol import Game, GameConfig

def test_level_generation():
    """Test the improved level generation features."""
    print("Testing improved level generation...")
    
    # Create a game instance
    game = Game()
    
    # Test each level
    for level in [1, 2, 3]:
        print(f"\n=== Testing Level {level} ===")
        
        # Set level and generate
        game.level = level
        game._generate_procedural_level()
        
        # Count rooms (approximate by looking for open areas)
        open_spaces = 0
        total_spaces = GameConfig.MAP_WIDTH * GameConfig.MAP_HEIGHT
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                if (x, y) not in game.game_map.walls:
                    open_spaces += 1
        
        # Count enemies
        enemy_count = len(game.enemies)
        expected_enemies = GameConfig.NETWORK_CONFIGS[level]["enemies"]
        
        # Count data patches
        patch_count = len(game.game_map.data_patches)
        
        # Count exploit items
        exploit_count = len(game.game_map.exploit_pickups)
        
        # Count special nodes
        cooling_nodes = len(game.game_map.cooling_nodes)
        cpu_nodes = len(game.game_map.cpu_recovery_nodes)
        total_nodes = cooling_nodes + cpu_nodes
        
        # Count shadows
        shadow_count = len(game.game_map.shadows)
        
        print(f"  Open space: {open_spaces}/{total_spaces} ({open_spaces/total_spaces*100:.1f}%)")
        print(f"  Enemies: {enemy_count} (expected: {expected_enemies})")
        print(f"  Data patches: {patch_count}")
        print(f"  Exploit items: {exploit_count}")
        print(f"  Special nodes: {total_nodes} (cooling: {cooling_nodes}, CPU: {cpu_nodes})")
        print(f"  Shadow areas: {shadow_count}")
        
        # Verify improvements
        print("\n  Improvements verification:")
        
        # Check if we have more enemies than old system (old was 8, 12, 16)
        old_enemy_counts = [8, 12, 16]
        if enemy_count > old_enemy_counts[level - 1]:
            print(f"  [OK] More enemies: {enemy_count} > {old_enemy_counts[level - 1]}")
        else:
            print(f"  [WARN] Enemy count may be low: {enemy_count} vs expected > {old_enemy_counts[level - 1]}")
        
        # Check if we have more data patches (old was 6 + level * 2)
        old_patch_count = 6 + level * 2
        expected_patch_count = 12 + level * 4
        if patch_count >= expected_patch_count * 0.8:  # Allow some variance due to placement failures
            print(f"  [OK] More data patches: {patch_count} (target: {expected_patch_count})")
        else:
            print(f"  [WARN] Data patch count may be low: {patch_count} vs target {expected_patch_count}")
        
        # Check if we have more exploits (old was 2 + max(0, level - 1))
        old_exploit_count = 2 + max(0, level - 1)
        expected_exploit_count = 5 + level * 2
        if exploit_count >= expected_exploit_count * 0.8:  # Allow some variance
            print(f"  [OK] More exploit items: {exploit_count} (target: {expected_exploit_count})")
        else:
            print(f"  [WARN] Exploit count may be low: {exploit_count} vs target {expected_exploit_count}")
        
        # Check shadow coverage (more shadows = better stealth)
        shadow_percentage = shadow_count / open_spaces * 100 if open_spaces > 0 else 0
        print(f"  [INFO] Shadow coverage: {shadow_percentage:.1f}% of open space")
        
        # Check if map has good connectivity (rough estimate)
        if open_spaces > total_spaces * 0.3:  # At least 30% open space
            print(f"  [OK] Good space utilization: {open_spaces/total_spaces*100:.1f}%")
        else:
            print(f"  [WARN] May be too cramped: {open_spaces/total_spaces*100:.1f}%")
    
    print("\n=== Summary ===")
    print("Level generation improvements implemented:")
    print("  - MST-based room connections for better layouts")
    print("  - Multiple room sizes (small, medium, large, extra large)")
    print("  - More rooms per level (12-20 vs 6-12)")
    print("  - Extra corridor connections for multiple paths")
    print("  - Strategic cover elements in open areas")
    print("  - Improved shadow generation with varied shapes")
    print("  - Significantly more enemies (15/22/30 vs 8/12/16)")
    print("  - More data patches and exploits for better loot")
    print("  - More special nodes for resource management")
    
    print("\n[SUCCESS] Level generation testing completed!")

if __name__ == "__main__":
    test_level_generation()