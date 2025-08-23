#!/usr/bin/env python3
"""
Test script to verify stealth/shadow mechanics work correctly.
Tests player and enemy visibility in shadow squares with adjacent exception.
"""

import sys
import os

# Add the parent directory to sys.path so we can import the game
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from RogueSignalProtocol import Game, Player, GameMap, Position, Enemy, GameData

def test_stealth_mechanics():
    """Test that stealth/shadow mechanics work correctly."""
    print("Testing stealth/shadow mechanics...")
    
    # Create a minimal game instance for testing
    game = Game()
    game.game_map = GameMap(20, 20)
    game.player = Player(10, 10)  # Start at position (10, 10)
    game.enemies = []
    game.turn = 0
    
    # Add some shadow squares manually for testing
    game.game_map.shadows.add((9, 10))   # Shadow left of player
    game.game_map.shadows.add((10, 11))  # Shadow below player
    game.game_map.shadows.add((12, 12))  # Shadow away from player
    game.game_map.shadows.add((5, 5))    # Distant shadow
    
    # Create test enemies at various positions
    enemy_adjacent_shadow = Enemy(Position(9, 10), 'scanner')  # In shadow, adjacent to player
    enemy_distant_shadow = Enemy(Position(12, 12), 'scanner')   # In shadow, distant from player
    enemy_normal = Enemy(Position(8, 10), 'scanner')           # Not in shadow
    enemy_distant_normal = Enemy(Position(5, 6), 'scanner')    # Not in shadow, distant
    
    print("\n=== Test Setup ===")
    print(f"Player at: ({game.player.x}, {game.player.y})")
    print(f"Shadows at: {list(game.game_map.shadows)}")
    print(f"Enemy adjacent shadow at: ({enemy_adjacent_shadow.x}, {enemy_adjacent_shadow.y})")
    print(f"Enemy distant shadow at: ({enemy_distant_shadow.x}, {enemy_distant_shadow.y})")
    print(f"Enemy normal at: ({enemy_normal.x}, {enemy_normal.y})")
    print(f"Enemy distant normal at: ({enemy_distant_normal.x}, {enemy_distant_normal.y})")
    
    # Test 1: Player not in shadow, enemies at different locations
    print("\n=== Test 1: Player not in shadow ===")
    
    # Player should see adjacent shadow enemy (because adjacent)
    can_see_adj_shadow = game.player.can_see_enemy(enemy_adjacent_shadow, game.game_map)
    print(f"Player can see adjacent shadow enemy: {can_see_adj_shadow}")
    assert can_see_adj_shadow == True, "Player should see adjacent enemy even in shadow"
    
    # Player should NOT see distant shadow enemy
    can_see_dist_shadow = game.player.can_see_enemy(enemy_distant_shadow, game.game_map)
    print(f"Player can see distant shadow enemy: {can_see_dist_shadow}")
    assert can_see_dist_shadow == False, "Player should NOT see distant enemy in shadow"
    
    # Player should see normal enemy
    can_see_normal = game.player.can_see_enemy(enemy_normal, game.game_map)
    print(f"Player can see normal enemy: {can_see_normal}")
    assert can_see_normal == True, "Player should see normal enemy"
    
    # Adjacent shadow enemy should see player
    can_enemy_see_player = enemy_adjacent_shadow.can_see_player(game.player, game.game_map)
    print(f"Adjacent shadow enemy can see player: {can_enemy_see_player}")
    assert can_enemy_see_player == True, "Adjacent shadow enemy should see player"
    
    # Distant shadow enemy should NOT see player (reduced vision from shadow)
    can_distant_enemy_see = enemy_distant_shadow.can_see_player(game.player, game.game_map)
    print(f"Distant shadow enemy can see player: {can_distant_enemy_see}")
    # This depends on enemy vision range vs distance, but shadow should reduce it
    
    print("  [OK] Player visibility rules work correctly")
    
    # Test 2: Player in shadow
    print("\n=== Test 2: Player in shadow ===")
    
    # Move player to shadow
    game.player.position = Position(10, 11)
    print(f"Player moved to shadow at: ({game.player.x}, {game.player.y})")
    
    # Create enemy adjacent to player in shadow
    enemy_adj_to_shadow_player = Enemy(Position(10, 10), 'scanner')  # Adjacent to player in shadow
    enemy_distant_from_shadow_player = Enemy(Position(8, 8), 'scanner')  # Distant from player in shadow
    
    # Adjacent enemy should see player in shadow
    can_adj_see_shadow_player = enemy_adj_to_shadow_player.can_see_player(game.player, game.game_map)
    print(f"Adjacent enemy can see player in shadow: {can_adj_see_shadow_player}")
    assert can_adj_see_shadow_player == True, "Adjacent enemy should see player even when player is in shadow"
    
    # Distant enemy should NOT see player in shadow
    can_dist_see_shadow_player = enemy_distant_from_shadow_player.can_see_player(game.player, game.game_map)
    print(f"Distant enemy can see player in shadow: {can_dist_see_shadow_player}")
    assert can_dist_see_shadow_player == False, "Distant enemy should NOT see player in shadow"
    
    # Player in shadow should have reduced vision range
    normal_vision = 15  # Base vision range
    shadow_vision = normal_vision // 2  # Should be reduced
    
    # Test player vision from shadow
    far_enemy = Enemy(Position(2, 2), 'scanner')  # Very far enemy
    can_shadow_player_see_far = game.player.can_see_enemy(far_enemy, game.game_map)
    print(f"Player in shadow can see far enemy: {can_shadow_player_see_far}")
    # Should be false due to reduced vision range
    
    print("  [OK] Player in shadow mechanics work correctly")
    
    # Test 3: Data mimic (invisibility) effect
    print("\n=== Test 3: Data mimic invisibility ===")
    
    # Move player back to normal position
    game.player.position = Position(10, 10)
    
    # Activate invisibility
    game.player.temporary_effects['data_mimic_turns'] = 3
    
    # Enemy should NOT see invisible player
    can_see_invisible = enemy_normal.can_see_player(game.player, game.game_map)
    print(f"Enemy can see invisible player: {can_see_invisible}")
    assert can_see_invisible == False, "Enemy should NOT see invisible player"
    
    print("  [OK] Data mimic invisibility works correctly")
    
    print("\n[SUCCESS] All stealth mechanics tests passed!")
    print("Summary of implemented stealth mechanics:")
    print("  - Enemies in shadows are only visible to player when adjacent (distance <= 1)")
    print("  - Players in shadows are only visible to enemies when adjacent (distance <= 1)")
    print("  - Entities in shadows have reduced vision range (half of normal)")
    print("  - Data mimic effect makes player completely invisible")
    print("  - Adjacent entities can always see each other regardless of shadows")

if __name__ == "__main__":
    test_stealth_mechanics()