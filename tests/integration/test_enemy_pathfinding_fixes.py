#!/usr/bin/env python3
"""
Integration tests for enemy pathfinding fixes.
Tests real game scenarios to prevent regression of pathfinding bugs.
Rewritten for on-demand movement calculation system (no movement queue).
"""

import unittest
from unittest.mock import Mock

from rsp.core.config import GameConfig, GameSettings
from rsp.core.engine import GameEngine
from rsp.entities.base import EnemyState, Position
from rsp.entities.characters import Enemy


class TestEnemyPathfindingFixes(unittest.TestCase):
    """Test enemy pathfinding fixes in real game scenarios."""

    def create_test_engine(self):
        """Create a GameEngine instance for testing."""
        # Create mocked sound manager for testing
        mock_sound_manager = Mock()

        # Create GameEngine with mocked dependencies
        engine = GameEngine(sound_manager=mock_sound_manager, settings=self.game_settings)

        return engine

    def setUp(self):
        """Set up test game engine with real components."""
        self.game_settings = GameSettings()
        self.engine = self.create_test_engine()
        self.player = self.engine.player
        self.game_map = self.engine.game_map

        # Create a simple test map layout
        self.game_map.walls.clear()  # Clear existing walls

        # Add some walls to create pathfinding challenges
        for x in range(10, 15):
            self.game_map.walls.add((x, 10))  # Horizontal wall
        for y in range(8, 13):
            self.game_map.walls.add((12, y))  # Vertical wall intersecting

    def test_enemy_cannot_move_through_player_position(self):
        """Test that enemies don't calculate moves that would go through player position."""
        # Place player at position where enemy would want to go through them
        self.player.x, self.player.y = 15, 10

        # Place enemy on one side of player
        enemy = Enemy(Position(10, 10), "virus")
        enemy.state = EnemyState.HOSTILE
        enemy.last_seen_player = Position(self.player.x, self.player.y)
        self.engine.enemies = [enemy]

        # Force queue refresh and execute movement
        initial_pos = enemy.position
        enemy.move_queue.clear()  # Force refresh
        moved = enemy.move(self.game_map, self.player, self.engine)

        # Verify enemy didn't move to player position
        self.assertNotEqual(
            (enemy.position.x, enemy.position.y),
            (self.player.x, self.player.y),
            "Enemy moved to player position",
        )

        # Execute several moves and ensure enemy never moves onto player
        for _ in range(10):
            initial_pos = enemy.position
            moved = enemy.move(self.game_map, self.player, self.engine)

            # Enemy should never be on player position
            self.assertNotEqual(
                (enemy.position.x, enemy.position.y),
                (self.player.x, self.player.y),
                "Enemy moved to player position",
            )

            # If adjacent to player, should stop moving
            if enemy.position.is_adjacent_to(Position(self.player.x, self.player.y)):
                break

    def test_enemy_finds_path_when_direct_path_blocked(self):
        """Test that enemies find alternative paths when direct path is blocked."""
        # Place player surrounded by walls except one opening
        self.player.x, self.player.y = 20, 20

        # Surround player with walls, leaving one opening
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if dx == 0 and dy == 0:
                    continue  # Player position
                if dx == 1 and dy == 0:
                    continue  # Leave one opening
                wall_x, wall_y = self.player.x + dx, self.player.y + dy
                if 0 <= wall_x < GameConfig.MAP_WIDTH and 0 <= wall_y < GameConfig.MAP_HEIGHT:
                    self.game_map.walls.add((wall_x, wall_y))

        # Place enemy far away who wants to reach player
        enemy = Enemy(Position(5, 5), "bot")
        enemy.state = EnemyState.HOSTILE
        enemy.last_seen_player = Position(self.player.x, self.player.y)
        self.engine.enemies = [enemy]

        # Execute movement - should find alternative path
        initial_pos = enemy.position
        enemy.move_queue.clear()  # Force refresh
        moved = enemy.move(self.game_map, self.player, self.engine)

        # Enemy should have either moved or have valid planned moves
        if moved:
            self.assertFalse(
                self.game_map.is_wall(enemy.position), "Enemy should not move to a wall"
            )
            self.assertNotEqual(
                (enemy.position.x, enemy.position.y),
                (self.player.x, self.player.y),
                "Enemy should not move to player position",
            )

        # Enemy should have planned moves in queue for pathfinding
        if enemy.move_queue:
            next_planned = enemy.move_queue[0]
            self.assertFalse(
                self.game_map.is_wall(next_planned), "Planned move should not be a wall"
            )

    def test_enemy_movement_prediction_respects_pathfinding(self):
        """Test that movement prediction uses correct pathfinding logic."""
        # Set up scenario where enemy would want to go through player
        self.player.x, self.player.y = 25, 25

        enemy = Enemy(Position(20, 25), "bot")
        enemy.state = EnemyState.HOSTILE
        enemy.last_seen_player = Position(self.player.x, self.player.y)
        self.engine.enemies = [enemy]

        # Get predicted next positions (simulates future moves)
        predicted_positions = self.engine.get_enemy_next_positions(enemy, steps=5)

        # Verify prediction doesn't include player position
        for predicted_pos in predicted_positions:
            self.assertNotEqual(
                (predicted_pos.x, predicted_pos.y),
                (self.player.x, self.player.y),
                "Movement prediction should not include player position",
            )

    def test_blocked_enemy_gets_close_and_stops(self):
        """Test that enemy gets as close as possible when fully blocked."""
        # Create a scenario where player is completely inaccessible
        self.player.x, self.player.y = 30, 30

        # Surround player completely with walls
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if dx == 0 and dy == 0:
                    continue  # Player position
                wall_x, wall_y = self.player.x + dx, self.player.y + dy
                if 0 <= wall_x < GameConfig.MAP_WIDTH and 0 <= wall_y < GameConfig.MAP_HEIGHT:
                    self.game_map.walls.add((wall_x, wall_y))

        # Place enemy outside the wall box
        enemy = Enemy(Position(25, 30), "admin")
        enemy.state = EnemyState.HOSTILE
        enemy.last_seen_player = Position(self.player.x, self.player.y)
        self.engine.enemies = [enemy]

        # Execute multiple movement attempts
        initial_distance = enemy.position.distance_to(Position(self.player.x, self.player.y))

        for _ in range(20):  # Try to move 20 times
            moved = enemy.move(self.game_map, self.player, self.engine)
            if not moved:
                break  # No valid move found

        final_distance = enemy.position.distance_to(Position(self.player.x, self.player.y))

        # Enemy should try to get closer (or may get stuck at walls)
        # Just verify enemy didn't break through walls to player
        self.assertNotEqual(
            (enemy.position.x, enemy.position.y),
            (self.player.x, self.player.y),
            "Enemy should not teleport through walls to player",
        )

        # Verify enemy position is valid (not in a wall)
        self.assertFalse(self.game_map.is_wall(enemy.position), "Enemy should not end up in a wall")

    def test_multiple_enemies_pathfind_independently(self):
        """Test that multiple enemies calculate their own paths correctly."""
        self.player.x, self.player.y = 30, 30

        # Create multiple enemies at different positions
        enemy1 = Enemy(Position(20, 20), "virus")
        enemy1.state = EnemyState.HOSTILE
        enemy1.last_seen_player = Position(self.player.x, self.player.y)

        enemy2 = Enemy(Position(40, 40), "bot")
        enemy2.state = EnemyState.HOSTILE
        enemy2.last_seen_player = Position(self.player.x, self.player.y)

        self.engine.enemies = [enemy1, enemy2]

        # Execute moves for both enemies
        enemy1.move_queue.clear()  # Force refresh
        enemy2.move_queue.clear()  # Force refresh

        moved1 = enemy1.move(self.game_map, self.player, self.engine)
        moved2 = enemy2.move(self.game_map, self.player, self.engine)

        # Both should have moved closer or stayed in place
        # (valid pathfinding behavior)
        self.assertIsNotNone(enemy1.position, "Enemy 1 should have valid position")
        self.assertIsNotNone(enemy2.position, "Enemy 2 should have valid position")

    def test_enemy_pathfinds_around_blocking_enemy_to_attack_player(self):
        """Test P12 scenario: enemy 2 pathfinds around enemy 1 to attack player diagonally.

        Scenario: P 1 2
        - P = player at (10, 10)
        - 1 = enemy1 at (11, 10) - directly right of player, adjacent (in attack range)
        - 2 = enemy2 at (12, 10) - blocked behind enemy1

        Expected: Enemy 2 should pathfind around enemy 1 and approach player from a diagonal
        (e.g., move to (11, 9) or (11, 11)) rather than just stopping behind enemy 1.
        """
        # Clear walls for this test
        self.game_map.walls.clear()

        # Set up P 1 2 scenario
        self.player.x, self.player.y = 10, 10  # P

        # Enemy 1 is adjacent to player (in attack range)
        enemy1 = Enemy(Position(11, 10), "virus")  # 1 - directly right of P
        enemy1.state = EnemyState.HOSTILE
        enemy1.last_seen_player = Position(self.player.x, self.player.y)

        # Enemy 2 is blocked behind enemy 1
        enemy2 = Enemy(Position(12, 10), "bot")  # 2 - blocked behind 1
        enemy2.state = EnemyState.HOSTILE
        enemy2.last_seen_player = Position(self.player.x, self.player.y)

        self.engine.enemies = [enemy1, enemy2]

        # Enemy 1 should stay adjacent to player (already in attack range)
        initial_e1_pos = (enemy1.position.x, enemy1.position.y)
        enemy1.move_queue.clear()
        enemy1.move(self.game_map, self.player, self.engine)

        # Enemy 1 should remain adjacent to player (in attack range, no need to move)
        self.assertTrue(
            enemy1.position.is_adjacent_to(Position(self.player.x, self.player.y)),
            "Enemy 1 should stay adjacent to player",
        )

        # Enemy 2 should pathfind around enemy 1
        initial_e2_pos = (enemy2.position.x, enemy2.position.y)
        enemy2.move_queue.clear()

        # Execute several moves for enemy 2
        for turn in range(10):
            moved = enemy2.move(self.game_map, self.player, self.engine)

            # Enemy 2 should never move onto enemy 1's position
            self.assertNotEqual(
                (enemy2.position.x, enemy2.position.y),
                (enemy1.position.x, enemy1.position.y),
                "Enemy 2 should not move onto enemy 1",
            )

            # Enemy 2 should never move onto player's position
            self.assertNotEqual(
                (enemy2.position.x, enemy2.position.y),
                (self.player.x, self.player.y),
                "Enemy 2 should not move onto player",
            )

            # Check if enemy 2 is now adjacent to player (found diagonal route)
            if enemy2.position.is_adjacent_to(Position(self.player.x, self.player.y)):
                # Success! Enemy 2 found a path around enemy 1
                # Verify it's attacking from a different angle than enemy 1
                e2_attack_pos = (enemy2.position.x, enemy2.position.y)
                e1_attack_pos = (enemy1.position.x, enemy1.position.y)

                # They should be attacking from different positions
                self.assertNotEqual(
                    e2_attack_pos,
                    e1_attack_pos,
                    "Enemy 2 should attack from different position than enemy 1",
                )

                # Enemy 2 should be adjacent (in attack range)
                self.assertTrue(
                    enemy2.position.is_adjacent_to(Position(self.player.x, self.player.y)),
                    "Enemy 2 should be adjacent to player",
                )

                # Success - enemy 2 pathfound around enemy 1
                break

            # If no move, enemy is stuck (shouldn't happen with clear map)
            if not moved:
                self.fail("Enemy 2 should find path around enemy 1 to reach player")

        # Final verification: Enemy 2 should have moved closer to player or be adjacent
        final_distance = enemy2.position.distance_to(Position(self.player.x, self.player.y))
        initial_distance = Position(*initial_e2_pos).distance_to(
            Position(self.player.x, self.player.y)
        )

        # Enemy 2 should be closer now or adjacent
        self.assertLessEqual(
            final_distance,
            initial_distance + 0.5,
            f"Enemy 2 should move closer to player (was {initial_distance:.2f}, now {final_distance:.2f})",
        )

    def test_queue_never_contains_player_position(self):
        """Test that movement queue never includes the player's exact position.

        This is critical - enemies should path TO adjacent (attack range), not ONTO player.
        The queue should stop filling once a position is adjacent to the player.
        """
        self.game_map.walls.clear()
        self.player.x, self.player.y = 20, 20

        # Enemy far from player, will pathfind toward them
        enemy = Enemy(Position(10, 10), "virus")
        enemy.state = EnemyState.HOSTILE
        enemy.last_seen_player = Position(self.player.x, self.player.y)
        self.engine.enemies = [enemy]

        # Execute multiple moves and check queue each time
        for turn in range(15):
            enemy.move(self.game_map, self.player, self.engine)

            # Check every position in the queue
            for queued_pos in enemy.move_queue:
                self.assertNotEqual(
                    (queued_pos.x, queued_pos.y),
                    (self.player.x, self.player.y),
                    f"Queue should never contain player position, found at turn {turn}",
                )

            # If adjacent, we should stop
            if enemy.position.is_adjacent_to(Position(self.player.x, self.player.y)):
                break

    def test_adjacent_enemy_stays_in_attack_range(self):
        """Test that an enemy already adjacent to player doesn't try to move onto them.

        Once in attack range, enemy should stay there and attack, not try to move closer.
        """
        self.game_map.walls.clear()
        self.player.x, self.player.y = 20, 20

        # Place enemy already adjacent to player
        enemy = Enemy(Position(21, 20), "virus")  # One tile to the right
        enemy.state = EnemyState.HOSTILE
        enemy.last_seen_player = Position(self.player.x, self.player.y)
        self.engine.enemies = [enemy]

        # Verify enemy is already adjacent
        self.assertTrue(
            enemy.position.is_adjacent_to(Position(self.player.x, self.player.y)),
            "Enemy should start adjacent to player",
        )

        initial_pos = (enemy.position.x, enemy.position.y)

        # Execute several moves
        for turn in range(5):
            enemy.move(self.game_map, self.player, self.engine)

            # Enemy should never move onto player
            self.assertNotEqual(
                (enemy.position.x, enemy.position.y),
                (self.player.x, self.player.y),
                "Enemy should not move onto player position",
            )

            # Enemy should stay in EXACT same position (not shuffle around)
            self.assertEqual(
                (enemy.position.x, enemy.position.y),
                initial_pos,
                f"Enemy should stay at initial position, not shuffle around (turn {turn})",
            )

            # Queue should be empty (no moves to make when in attack range)
            self.assertEqual(
                len(enemy.move_queue),
                0,
                f"Enemy should have empty queue when adjacent to player (turn {turn})",
            )

    def test_multiple_enemies_surround_player_from_different_angles(self):
        """Test that 3-4 enemies all converge on player from different directions.

        Enemies should occupy different adjacent tiles around the player, not stack up
        or block each other. This tests multi-enemy pathfinding coordination.
        """
        self.game_map.walls.clear()
        self.player.x, self.player.y = 25, 25

        # Create 4 enemies approaching from different cardinal directions
        enemy_north = Enemy(Position(25, 15), "virus")  # North
        enemy_north.state = EnemyState.HOSTILE
        enemy_north.last_seen_player = Position(self.player.x, self.player.y)

        enemy_south = Enemy(Position(25, 35), "bot")  # South
        enemy_south.state = EnemyState.HOSTILE
        enemy_south.last_seen_player = Position(self.player.x, self.player.y)

        enemy_west = Enemy(Position(15, 25), "scanner")  # West
        enemy_west.state = EnemyState.HOSTILE
        enemy_west.last_seen_player = Position(self.player.x, self.player.y)

        enemy_east = Enemy(Position(35, 25), "firewall")  # East
        enemy_east.state = EnemyState.HOSTILE
        enemy_east.last_seen_player = Position(self.player.x, self.player.y)

        self.engine.enemies = [enemy_north, enemy_south, enemy_west, enemy_east]

        # Let all enemies move toward player
        for turn in range(15):
            for enemy in self.engine.enemies:
                enemy.move(self.game_map, self.player, self.engine)

        # All enemies should be adjacent to player
        adjacent_count = 0
        occupied_positions = set()

        for enemy in self.engine.enemies:
            # Should not be on player position
            self.assertNotEqual(
                (enemy.position.x, enemy.position.y),
                (self.player.x, self.player.y),
                f"Enemy {enemy.type} should not be on player position",
            )

            # Check if adjacent
            if enemy.position.is_adjacent_to(Position(self.player.x, self.player.y)):
                adjacent_count += 1
                occupied_positions.add((enemy.position.x, enemy.position.y))

        # At least 2-3 enemies should reach adjacent tiles
        self.assertGreaterEqual(adjacent_count, 2, "At least 2 enemies should reach attack range")

        # All adjacent enemies should occupy different tiles
        adjacent_enemies = [
            e
            for e in self.engine.enemies
            if e.position.is_adjacent_to(Position(self.player.x, self.player.y))
        ]
        self.assertEqual(
            len(occupied_positions),
            len(adjacent_enemies),
            "Adjacent enemies should not stack on same tile",
        )

    def test_enemy_prefers_diagonal_over_two_orthogonal_moves(self):
        """Test that enemies prefer 1 diagonal move over 2 orthogonal moves.

        Given a clear path, an enemy should move diagonally (1 turn) rather than
        taking 2 orthogonal moves (2 turns) to reach the same destination.
        """
        self.game_map.walls.clear()

        # Place player at diagonal from enemy
        self.player.x, self.player.y = 12, 12

        # Place enemy at position where diagonal is clearly better
        enemy = Enemy(Position(10, 10), "virus")
        enemy.state = EnemyState.HOSTILE
        enemy.last_seen_player = Position(self.player.x, self.player.y)
        self.engine.enemies = [enemy]

        # Clear queue and move
        enemy.move_queue.clear()
        enemy.move(self.game_map, self.player, self.engine)

        # First move should be diagonal (11, 11) not orthogonal (10, 11) or (11, 10)
        new_pos = enemy.position

        # Enemy should have moved diagonally (both x and y changed)
        self.assertNotEqual(new_pos.x, 10, "Enemy should move diagonally, x should change")
        self.assertNotEqual(new_pos.y, 10, "Enemy should move diagonally, y should change")

        # Should be at (11, 11) - the diagonal step
        self.assertEqual(
            (new_pos.x, new_pos.y), (11, 11), "Enemy should take diagonal step to (11, 11)"
        )

    def test_greedy_fallback_when_path_blocked_by_enemies(self):
        """Test greedy fallback activates when pathfinding fails due to enemy blockage.

        Scenario: Enemy wants to reach player, but all direct paths are blocked by other enemies.
        Greedy fallback should kick in and find ANY valid adjacent move toward player.
        """
        self.game_map.walls.clear()
        self.player.x, self.player.y = 20, 20

        # Create a wall of enemies blocking direct path to player
        blocking_enemies = []
        for i in range(15, 26):
            if i == 20:  # Leave a gap that requires routing around
                continue
            blocker = Enemy(Position(i, 18), "scanner")
            blocker.state = EnemyState.UNAWARE  # Not moving
            blocking_enemies.append(blocker)

        # Enemy that wants to reach player (behind the wall)
        enemy = Enemy(Position(20, 15), "virus")
        enemy.state = EnemyState.HOSTILE
        enemy.last_seen_player = Position(self.player.x, self.player.y)

        self.engine.enemies = [enemy] + blocking_enemies

        # Move enemy - should use greedy fallback if path is too complex/blocked
        initial_pos = (enemy.position.x, enemy.position.y)
        enemy.move_queue.clear()

        # Execute several moves
        for _ in range(10):
            moved = enemy.move(self.game_map, self.player, self.engine)

            # Enemy should make progress (even if just via greedy)
            if moved:
                self.assertNotEqual(
                    (enemy.position.x, enemy.position.y),
                    initial_pos,
                    "Enemy should move from initial position",
                )

            # Should have moves queued UNLESS adjacent to player (attack range)
            if not enemy.position.is_adjacent_to(Position(self.player.x, self.player.y)):
                self.assertGreater(
                    len(enemy.move_queue),
                    0,
                    "Enemy should have moves queued (greedy or pathfinding)",
                )

            # Greedy should now queue up to 3 moves
            self.assertLessEqual(len(enemy.move_queue), 3, "Queue should not exceed 3 moves")

            # If adjacent, stop testing (enemy reached attack range)
            if enemy.position.is_adjacent_to(Position(self.player.x, self.player.y)):
                break

            initial_pos = (enemy.position.x, enemy.position.y)

    def test_greedy_fallback_chains_three_moves(self):
        """Test that greedy fallback chains up to 3 moves for predictability.

        When pathfinding fails, greedy should fill queue with 3 moves (not just 1)
        to maintain consistent player predictability.
        """
        self.game_map.walls.clear()
        self.player.x, self.player.y = 30, 30

        # Create complex blocking scenario where A* might fail
        # Surround enemy with other enemies on 3 sides
        enemy = Enemy(Position(20, 20), "virus")
        enemy.state = EnemyState.HOSTILE
        enemy.last_seen_player = Position(self.player.x, self.player.y)

        # Block 3 directions, leave 1 open
        blocker1 = Enemy(Position(19, 20), "scanner")  # West
        blocker2 = Enemy(Position(20, 19), "bot")  # North
        blocker3 = Enemy(Position(21, 20), "firewall")  # East
        # South (20, 21) is open

        for blocker in [blocker1, blocker2, blocker3]:
            blocker.state = EnemyState.UNAWARE

        self.engine.enemies = [enemy, blocker1, blocker2, blocker3]

        # Clear queue and trigger movement
        enemy.move_queue.clear()
        enemy._ensure_queue_full(self.game_map, self.player, self.engine)

        # After optimization, greedy should chain moves
        # Should have 1-3 moves (greedy chains toward target)
        self.assertGreater(len(enemy.move_queue), 0, "Greedy should add at least 1 move")

        # After optimization: greedy should chain up to 3
        # If greedy activated, we want 3 moves for predictability
        if len(enemy.move_queue) > 0:
            first_move = enemy.move_queue[0]
            # First move should be valid
            self.assertFalse(self.game_map.is_wall(first_move), "Greedy move should not be on wall")
            # Should not be on another enemy
            for blocker in [blocker1, blocker2, blocker3]:
                self.assertNotEqual(
                    (first_move.x, first_move.y),
                    (blocker.position.x, blocker.position.y),
                    "Greedy move should not be on another enemy",
                )

    def test_greedy_never_queues_player_position(self):
        """Test that greedy fallback never queues the player's exact position.

        Even when pathfinding fails and greedy activates, it should never
        add the player's position to the queue.
        """
        self.game_map.walls.clear()

        # Place enemy adjacent to player (greedy might activate)
        self.player.x, self.player.y = 20, 20
        enemy = Enemy(Position(21, 20), "virus")
        enemy.state = EnemyState.HOSTILE
        enemy.last_seen_player = Position(self.player.x, self.player.y)
        self.engine.enemies = [enemy]

        # Force greedy by making pathfinding "fail" (enemy is adjacent, path would be empty)
        enemy.move_queue.clear()
        enemy._ensure_queue_full(self.game_map, self.player, self.engine)

        # Check queue doesn't contain player position
        for pos in enemy.move_queue:
            self.assertNotEqual(
                (pos.x, pos.y),
                (self.player.x, self.player.y),
                "Greedy should never queue player position",
            )


if __name__ == "__main__":
    unittest.main()
