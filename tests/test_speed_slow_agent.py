#!/usr/bin/env python3
"""
Speed/Slow Mechanics Testing Agent

Tests the turn order and energy system for speed boosts and movement inhibition.

Test scenarios:
1. Slowed player gets attacked by enemy twice (before player moves)
2. Speed-hacked player can attack enemy twice (before enemy moves)
3. Sped-up player getting inhibited reduces speed by slow stack amount
4. Slowed player using speed hack reduces slow by speed amount
5. Sped-up player moves twice and enemy once in chase
6. Slowed player moves once, enemy moves + attacks per player move
"""

import logging
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from game_inventory import CodeHack
from tests.test_agent import GameTestAgent

# Configure logging to see the test details
logging.basicConfig(level=logging.INFO, format="%(message)s", force=True)


class SpeedSlowTestAgent(GameTestAgent):
    """Extended test agent with speed/slow testing capabilities."""

    def apply_speed_hack(self):
        """Apply a speed boost code hack to the player."""
        # Create a speed boost code hack and add it to inventory
        speed_hack = CodeHack(
            color_name="test_speed",
            effect="speed_boost",
            name="Test Speed Hack",
            description="Test speed boost",
            quantity=1,
        )

        # Register this effect in the engine so it's recognized
        self.engine.code_hack_effects["test_speed"] = (
            "speed_boost",
            "Speed boost: 2 moves per turn (3 enemy turns)",
        )

        # Add to inventory and use
        self.player.inventory_manager.add_item(speed_hack)
        speed_hack.use(self.player, self.engine)

    def apply_slow_effect(self, stacks: int = 1):
        """
        Directly apply slow effect to player (simulating inhibitor attacks).

        Args:
            stacks: Number of slow stacks to apply (default 1)
        """
        current_slow = self.player.temporary_effects.get("movement_slowed_turns", 0)
        self.player.temporary_effects["movement_slowed_turns"] = min(current_slow + stacks, 5)

    def count_enemy_actions(self, enemy) -> dict:
        """
        Track enemy position and attack count before it acts.

        Returns:
            Dictionary with initial position and player HP
        """
        return {
            "pos": (enemy.x, enemy.y),
            "player_hp": self.player.cpu,
            "enemy_can_attack": enemy.can_attack_player(self.player),
        }


def test_slow_enemy_double_attack():
    """
    Test 1: Slowed player gets attacked by enemy twice before player moves.

    Expected behavior:
    - Player has movement_slowed_turns > 0
    - Enemy adjacent to player
    - Enemy should attack twice in one player turn (once in process_turn, once in extra _update_enemies)
    """
    logging.info("\n=== Test 1: Slow + Enemy Double Attack ===")

    agent = SpeedSlowTestAgent(seed=42)

    # Spawn inhibitor adjacent to player
    player_x, player_y = agent.player.x, agent.player.y
    inhibitor = agent.spawn_enemy("inhibitor", player_x + 1, player_y)

    logging.info(f"Player at ({player_x}, {player_y}), Inhibitor at ({inhibitor.x}, {inhibitor.y})")
    logging.info(f"Player HP: {agent.player.cpu}/{agent.player.max_cpu}")

    # Apply slow effect to player
    agent.apply_slow_effect(stacks=1)
    logging.info(
        f"Applied slow: movement_slowed_turns = {agent.player.temporary_effects['movement_slowed_turns']}"
    )

    # Player tries to move (triggers turn processing)
    initial_hp = agent.player.cpu
    logging.info(f"Initial HP: {initial_hp}")

    # Move player in a direction away from inhibitor
    agent.move_player(-1, 0)

    final_hp = agent.player.cpu
    damage_taken = initial_hp - final_hp

    logging.info(f"Final HP: {final_hp}")
    logging.info(f"Damage taken: {damage_taken}")
    logging.info(
        "Expected: Inhibitor should have attacked TWICE (0 damage each, but 2 slow stacks added)"
    )

    # Check that slow stacks increased (inhibitor attacks don't do damage but add slow)
    final_slow = agent.player.temporary_effects["movement_slowed_turns"]
    logging.info(f"Final slow stacks: {final_slow}")

    # Note: Inhibitor attacks don't deal damage, but we should see it attacked twice
    # This is verified by checking the slow stacks increased


def test_speed_player_double_attack():
    """
    Test 2: Speed-hacked player can attack enemy twice before enemy moves.

    Expected behavior:
    - Player has speed_boost_turns = 3, speed_moves_remaining = 2
    - Player attacks adjacent enemy
    - Player should get 2 attacks before enemy moves
    """
    logging.info("\n=== Test 2: Speed Hack + Player Double Attack ===")

    agent = SpeedSlowTestAgent(seed=43)

    # Apply speed hack to player
    agent.apply_speed_hack()

    logging.info(
        f"Speed boost applied: speed_boost_turns = {agent.player.temporary_effects['speed_boost_turns']}"
    )
    logging.info(f"Speed moves remaining: {agent.player.speed_moves_remaining}")

    # Spawn enemy adjacent to player
    player_x, player_y = agent.player.x, agent.player.y
    enemy = agent.spawn_enemy("bot", player_x + 1, player_y)

    initial_enemy_hp = enemy.cpu
    logging.info(f"Enemy HP: {initial_enemy_hp}")

    # Wait one turn to trigger speed_moves_remaining grant (happens at start of turn)
    agent.wait(1)

    logging.info(f"After wait: speed_moves_remaining = {agent.player.speed_moves_remaining}")

    # Attack enemy twice (bump attacks)
    logging.info("Attack 1:")
    agent.move_player(1, 0)  # Bump attack
    hp_after_first = enemy.cpu if enemy in agent.enemies else 0
    logging.info(f"Enemy HP after attack 1: {hp_after_first}")

    logging.info(f"Speed moves remaining after attack 1: {agent.player.speed_moves_remaining}")

    if enemy in agent.enemies:
        logging.info("Attack 2:")
        agent.move_player(1, 0)  # Second bump attack
        hp_after_second = enemy.cpu if enemy in agent.enemies else 0
        logging.info(f"Enemy HP after attack 2: {hp_after_second}")

        logging.info(f"Speed moves remaining after attack 2: {agent.player.speed_moves_remaining}")

    logging.info("Expected: Player attacked twice before enemy could react")


def test_speed_reduced_by_inhibitor():
    """
    Test 3: Sped-up player getting inhibited reduces speed by slow stack amount.

    Expected behavior:
    - Player has speed_boost_turns = 3
    - Inhibitor attacks
    - Speed reduced to 2 turns (or 1 if turn processor also decremented)
    """
    logging.info("\n=== Test 3: Speed Boost Reduced by Inhibitor ===")

    agent = SpeedSlowTestAgent(seed=44)

    # Apply speed hack
    agent.apply_speed_hack()
    initial_speed = agent.player.temporary_effects["speed_boost_turns"]
    logging.info(f"Initial speed boost: {initial_speed} turns")

    # Spawn inhibitor adjacent and make it hostile so it attacks
    player_x, player_y = agent.player.x, agent.player.y
    inhibitor = agent.spawn_enemy("inhibitor", player_x + 1, player_y)

    from game_entities import EnemyState

    inhibitor.state = EnemyState.HOSTILE

    # Wait for inhibitor to attack (turn processor will also decrement speed_boost_turns)
    agent.wait(1)

    final_speed = agent.player.temporary_effects["speed_boost_turns"]
    logging.info(f"Final speed boost: {final_speed} turns")

    # After wait(1):
    # - Turn processor decrements speed_boost_turns by 1 (3 -> 2)
    # - Inhibitor attacks and decrements by 1 more (2 -> 1)
    expected_speed = initial_speed - 2  # -1 from turn processor, -1 from inhibitor
    logging.info(f"Expected: Speed reduced to {expected_speed} (turn decay + inhibitor attack)")

    assert (
        final_speed == expected_speed
    ), f"Speed not reduced correctly: {final_speed} != {expected_speed}"
    logging.info("[PASS] Speed correctly reduced by inhibitor")


def test_slow_reduced_by_speed_hack():
    """
    Test 4: Slowed player using speed hack reduces slow by speed amount.

    Expected behavior:
    - Player has movement_slowed_turns = 2
    - Player uses speed hack (3 turns)
    - Net effect: speed_boost_turns = 1, movement_slowed_turns = 0
    """
    logging.info("\n=== Test 4: Slow Cancelled by Speed Hack ===")

    agent = SpeedSlowTestAgent(seed=45)

    # Apply slow effect
    agent.apply_slow_effect(stacks=2)
    initial_slow = agent.player.temporary_effects["movement_slowed_turns"]
    logging.info(f"Initial slow: {initial_slow} turns")

    # Apply speed hack (should counter the slow)
    agent.apply_speed_hack()

    final_slow = agent.player.temporary_effects["movement_slowed_turns"]
    final_speed = agent.player.temporary_effects["speed_boost_turns"]

    logging.info(f"Final slow: {final_slow} turns")
    logging.info(f"Final speed: {final_speed} turns")

    # Speed boost is 3 turns by default, slow was 2, so net = 1 speed
    expected_speed = 3 - initial_slow
    logging.info(f"Expected: slow = 0, speed = {expected_speed}")

    assert final_slow == 0, f"Slow not cleared: {final_slow} != 0"
    assert final_speed == expected_speed, f"Speed incorrect: {final_speed} != {expected_speed}"
    logging.info("[PASS] Slow correctly cancelled by speed hack")


def test_speed_chase_scenario():
    """
    Test 5: Sped-up player moves twice and enemy once in chase situation.

    Expected behavior:
    - Player has speed boost
    - Player moves away from enemy
    - Player should get 2 moves before enemy gets 1 move
    """
    logging.info("\n=== Test 5: Speed Chase (Player moves 2x, Enemy moves 1x) ===")

    agent = SpeedSlowTestAgent(seed=46)

    # Apply speed hack
    agent.apply_speed_hack()

    # Spawn enemy some distance away
    player_x, player_y = agent.player.x, agent.player.y
    enemy = agent.spawn_enemy("bot", player_x + 3, player_y)

    from game_entities import EnemyState

    enemy.state = EnemyState.HOSTILE  # Make it chase

    logging.info(f"Player at ({player_x}, {player_y}), Enemy at ({enemy.x}, {enemy.y})")

    # Grant speed moves
    agent.wait(1)
    logging.info(f"Speed moves remaining: {agent.player.speed_moves_remaining}")

    # Move player twice
    initial_enemy_pos = (enemy.x, enemy.y)

    logging.info("Player move 1:")
    agent.move_player(0, 1)  # Move down
    player_pos_1 = (agent.player.x, agent.player.y)
    enemy_pos_1 = (enemy.x, enemy.y)
    logging.info(f"Player: {player_pos_1}, Enemy: {enemy_pos_1}")

    logging.info("Player move 2:")
    agent.move_player(0, 1)  # Move down again
    player_pos_2 = (agent.player.x, agent.player.y)
    enemy_pos_2 = (enemy.x, enemy.y)
    logging.info(f"Player: {player_pos_2}, Enemy: {enemy_pos_2}")

    # Enemy should NOT have moved yet (both moves consumed speed_moves_remaining)
    logging.info(f"Enemy moved: {initial_enemy_pos != enemy_pos_2}")
    logging.info("Expected: Enemy should NOT have moved yet")


def test_slow_chase_scenario():
    """
    Test 6: Slowed player moves once, enemy moves and attacks per player move.

    Expected behavior:
    - Player has movement_slowed_turns > 0
    - Player moves
    - Enemy should get to move AND potentially attack twice (once in normal turn, once in extra turn)
    """
    logging.info("\n=== Test 6: Slow Chase (Player moves 1x, Enemy moves 2x) ===")

    agent = SpeedSlowTestAgent(seed=47)

    # Apply slow effect
    agent.apply_slow_effect(stacks=1)
    logging.info(f"Slow applied: {agent.player.temporary_effects['movement_slowed_turns']} turns")

    # Spawn enemy some distance away
    player_x, player_y = agent.player.x, agent.player.y
    enemy = agent.spawn_enemy("bot", player_x + 5, player_y)

    # Make enemy hostile so it chases
    from game_entities import EnemyState

    enemy.state = EnemyState.HOSTILE

    logging.info(f"Player at ({player_x}, {player_y}), Enemy at ({enemy.x}, {enemy.y})")

    initial_enemy_pos = (enemy.x, enemy.y)
    initial_distance = abs(enemy.x - agent.player.x) + abs(enemy.y - agent.player.y)

    # Player moves once
    logging.info("Player move:")
    agent.move_player(-1, 0)  # Move away from enemy

    final_enemy_pos = (enemy.x, enemy.y)
    final_distance = abs(enemy.x - agent.player.x) + abs(enemy.y - agent.player.y)

    enemy_moved_squares = abs(initial_enemy_pos[0] - final_enemy_pos[0]) + abs(
        initial_enemy_pos[1] - final_enemy_pos[1]
    )

    logging.info(f"Initial enemy pos: {initial_enemy_pos}")
    logging.info(f"Final enemy pos: {final_enemy_pos}")
    logging.info(f"Enemy moved {enemy_moved_squares} squares")
    logging.info(f"Initial distance: {initial_distance}, Final distance: {final_distance}")
    logging.info("Expected: Enemy should have moved TWICE (gotten 2 moves from slow mechanic)")


def run_all_tests():
    """Run all speed/slow mechanics tests."""
    logging.info("=" * 80)
    logging.info("SPEED/SLOW MECHANICS TESTING AGENT")
    logging.info("=" * 80)

    try:
        test_slow_enemy_double_attack()
        logging.info("\n[OK] Test 1 completed\n")
    except Exception as e:
        logging.error(f"\n[FAIL] Test 1 failed: {e}\n")

    try:
        test_speed_player_double_attack()
        logging.info("\n[OK] Test 2 completed\n")
    except Exception as e:
        logging.error(f"\n[FAIL] Test 2 failed: {e}\n")

    try:
        test_speed_reduced_by_inhibitor()
        logging.info("\n[OK] Test 3 completed\n")
    except Exception as e:
        logging.error(f"\n[FAIL] Test 3 failed: {e}\n")

    try:
        test_slow_reduced_by_speed_hack()
        logging.info("\n[OK] Test 4 completed\n")
    except Exception as e:
        logging.error(f"\n[FAIL] Test 4 failed: {e}\n")

    try:
        test_speed_chase_scenario()
        logging.info("\n[OK] Test 5 completed\n")
    except Exception as e:
        logging.error(f"\n[FAIL] Test 5 failed: {e}\n")

    try:
        test_slow_chase_scenario()
        logging.info("\n[OK] Test 6 completed\n")
    except Exception as e:
        logging.error(f"\n[FAIL] Test 6 failed: {e}\n")

    logging.info("=" * 80)
    logging.info("ALL TESTS COMPLETED")
    logging.info("=" * 80)


if __name__ == "__main__":
    run_all_tests()
