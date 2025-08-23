#!/usr/bin/env python3
"""
Test script to verify Speed Data Patch (speed_boost) mechanics.
Tests that player gets 2 moves before enemies move when speed boost is active.
"""

import sys
import os

# Add the parent directory to sys.path so we can import the game
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from RogueSignalProtocol import Game, Player, GameMap, Position

def test_speed_boost_mechanics():
    """Test that speed boost allows 2 moves before enemy turn."""
    print("Testing Speed Data Patch mechanics...")
    
    # Create a minimal game instance for testing
    game = Game()
    game.game_map = GameMap(50, 50)  # Create a 50x50 map
    game.player = Player(10, 10)  # Start at position (10, 10)
    game.enemies = []  # No enemies for this test
    game.turn = 0
    
    # Test 1: Normal movement (no speed boost)
    print("\nTest 1: Normal movement without speed boost")
    initial_turn = game.turn
    initial_pos = (game.player.x, game.player.y)
    
    # Move once
    game.move_player(1, 0)  # Move right
    turn_after_one_move = game.turn
    pos_after_one_move = (game.player.x, game.player.y)
    
    print(f"  Initial: turn={initial_turn}, pos={initial_pos}")
    print(f"  After 1 move: turn={turn_after_one_move}, pos={pos_after_one_move}")
    print(f"  Speed moves remaining: {game.player.speed_moves_remaining}")
    
    # Verify turn incremented after one move
    assert turn_after_one_move == initial_turn + 1, "Turn should increment after one move without speed boost"
    print("  [OK] Turn incremented correctly after one move")
    
    # Test 2: Movement with speed boost
    print("\nTest 2: Movement with speed boost")
    
    # Activate speed boost
    game.player.temporary_effects['speed_boost_turns'] = 5
    game.player.speed_moves_remaining = 0  # Reset counter
    
    initial_turn = game.turn
    initial_pos = (game.player.x, game.player.y)
    
    # First move with speed boost
    game.move_player(1, 0)  # Move right
    turn_after_first_speed_move = game.turn
    pos_after_first_speed_move = (game.player.x, game.player.y)
    speed_moves_after_first = game.player.speed_moves_remaining
    
    print(f"  Initial with speed boost: turn={initial_turn}, pos={initial_pos}")
    print(f"  After 1st speed move: turn={turn_after_first_speed_move}, pos={pos_after_first_speed_move}")
    print(f"  Speed moves remaining: {speed_moves_after_first}")
    
    # Turn should NOT increment after first speed move
    assert turn_after_first_speed_move == initial_turn, "Turn should NOT increment after first speed boost move"
    assert speed_moves_after_first == 1, "Should have 1 speed move remaining"
    print("  [OK] Turn did not increment after first speed move")
    print("  [OK] Speed moves remaining is correct")
    
    # Second move with speed boost
    game.move_player(0, 1)  # Move down
    turn_after_second_speed_move = game.turn
    pos_after_second_speed_move = (game.player.x, game.player.y)
    speed_moves_after_second = game.player.speed_moves_remaining
    
    print(f"  After 2nd speed move: turn={turn_after_second_speed_move}, pos={pos_after_second_speed_move}")
    print(f"  Speed moves remaining: {speed_moves_after_second}")
    
    # Turn should increment after second speed move
    assert turn_after_second_speed_move == initial_turn + 1, "Turn should increment after second speed boost move"
    assert speed_moves_after_second == 0, "Should have 0 speed moves remaining"
    print("  [OK] Turn incremented after second speed move")
    print("  [OK] Speed moves remaining reset to 0")
    
    # Test 3: Verify next move grants speed moves again
    print("\nTest 3: Verify speed boost continues to work")
    
    # Third move (should grant 2 moves again)
    initial_turn = game.turn
    game.move_player(-1, 0)  # Move left
    turn_after_third = game.turn
    speed_moves_after_third = game.player.speed_moves_remaining
    
    print(f"  After 3rd speed move: turn={turn_after_third}")
    print(f"  Speed moves remaining: {speed_moves_after_third}")
    
    # Turn should NOT increment, and we should have 1 speed move remaining
    assert turn_after_third == initial_turn, "Turn should NOT increment on first move of new speed boost cycle"
    assert speed_moves_after_third == 1, "Should have 1 speed move remaining after third move"
    print("  [OK] Speed boost continues to work correctly")
    
    print("\n[SUCCESS] All tests passed! Speed Data Patch mechanics work correctly.")
    print("   - Player gets 2 moves before enemy turn when speed boost is active")
    print("   - Normal movement works correctly when speed boost is not active")
    print("   - Speed boost persists across multiple cycles")

if __name__ == "__main__":
    test_speed_boost_mechanics()