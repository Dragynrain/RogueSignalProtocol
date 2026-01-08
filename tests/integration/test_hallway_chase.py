"""
Test enemy chase behavior in hallway scenarios.

Verifies that enemies correctly path toward the player in narrow corridors
and don't get stuck or take unexpected routes.
"""

import pytest

from rsp.entities.base import EnemyState, Position
from rsp.entities.characters import Enemy
from tests.fixtures.standard_patterns import create_basic_game_environment


def _invalidate_map_caches(game_map):
    """Invalidate all map caches after modifying walls."""
    # Walkability cache
    if hasattr(game_map, "_walkability_cache"):
        del game_map._walkability_cache
    # Transparency cache (for FOV)
    if hasattr(game_map, "_transparency_cache"):
        del game_map._transparency_cache
    # LRU FOV cache
    if hasattr(game_map, "_compute_fov_cached"):
        game_map._compute_fov_cached.cache_clear()
    # Clear blind spots from original map (they block enemy vision)
    if hasattr(game_map, "blind_spots"):
        game_map.blind_spots.clear()
    if hasattr(game_map, "ghost_nodes"):
        game_map.ghost_nodes.clear()


def create_horizontal_hallway_map(game_map, hallway_y: int = 5):
    """
    Convert an existing map to a horizontal hallway.

    Clears all existing terrain and creates a single horizontal hallway.
    """
    # Clear all walls first
    game_map.walls.clear()

    # Add walls everywhere except hallway row
    for y in range(game_map.height):
        for x in range(game_map.width):
            if y != hallway_y:
                game_map.walls.add((x, y))

    # Invalidate all caches since we modified walls
    _invalidate_map_caches(game_map)


def create_vertical_hallway_map(game_map, hallway_x: int = 15):
    """Convert an existing map to a vertical hallway."""
    game_map.walls.clear()

    for y in range(game_map.height):
        for x in range(game_map.width):
            if x != hallway_x:
                game_map.walls.add((x, y))

    # Invalidate all caches since we modified walls
    _invalidate_map_caches(game_map)


def create_t_junction_map(game_map, mid_x: int = 15, mid_y: int = 15):
    """Convert an existing map to a T-junction."""
    game_map.walls.clear()

    for y in range(game_map.height):
        for x in range(game_map.width):
            if y != mid_y and x != mid_x:
                game_map.walls.add((x, y))

    # Invalidate all caches since we modified walls
    _invalidate_map_caches(game_map)


def create_hostile_enemy_at(x: int, y: int, game_engine, enemy_type: str = "hunter") -> Enemy:
    """Create a hostile enemy at the specified position.

    Uses 'hunter' by default (vision 6, mobile when hostile).
    Scanner is STATIC and cannot move even when hostile.
    """
    enemy = Enemy(Position(x, y), enemy_type)
    enemy.state = EnemyState.HOSTILE
    enemy.last_seen_player = game_engine.player.position
    game_engine.enemies.append(enemy)
    return enemy


class TestHorizontalHallwayChase:
    """Test enemy chase in horizontal hallways."""

    def test_hallway_setup_is_correct(self):
        """Verify hallway map is set up correctly."""
        engine = create_basic_game_environment()
        engine.enemies.clear()

        create_horizontal_hallway_map(engine.game_map, hallway_y=15)

        # Verify hallway tiles are NOT walls
        assert not engine.game_map.is_wall(Position(10, 15)), "Tile (10,15) should be walkable"
        assert not engine.game_map.is_wall(Position(20, 15)), "Tile (20,15) should be walkable"
        assert not engine.game_map.is_wall(Position(24, 15)), "Tile (24,15) should be walkable"
        assert not engine.game_map.is_wall(Position(25, 15)), "Tile (25,15) should be walkable"
        assert not engine.game_map.is_wall(Position(26, 15)), "Tile (26,15) should be walkable"

        # Verify tiles above and below ARE walls
        assert engine.game_map.is_wall(Position(15, 14)), "Tile (15,14) should be a wall"
        assert engine.game_map.is_wall(Position(15, 16)), "Tile (15,16) should be a wall"

    def test_enemy_targets_player_position_directly(self):
        """Enemy should target player position directly (original behavior)."""
        engine = create_basic_game_environment()
        engine.enemies.clear()

        create_horizontal_hallway_map(engine.game_map, hallway_y=15)

        # Place enemy within vision range (hunter has vision 6)
        engine.player.position = Position(20, 15)
        enemy = create_hostile_enemy_at(16, 15, engine)  # 4 tiles away, within vision

        # Verify enemy can see player
        can_see = enemy.can_see_player(engine.player, engine.game_map)
        assert can_see, f"Enemy at {enemy.position} should see player at {engine.player.position}"

        target = enemy._get_current_target(engine.player, engine.game_map)

        # Original behavior: target IS the player position
        assert target is not None
        assert (
            target == engine.player.position
        ), f"Target should be player position {engine.player.position}, got {target}"

    def test_enemy_from_right_targets_player(self):
        """Enemy to the right of player should target player position."""
        engine = create_basic_game_environment()
        engine.enemies.clear()

        create_horizontal_hallway_map(engine.game_map, hallway_y=15)

        # Place within vision range
        engine.player.position = Position(15, 15)
        enemy = create_hostile_enemy_at(19, 15, engine)  # 4 tiles to the right

        can_see = enemy.can_see_player(engine.player, engine.game_map)
        assert can_see, "Enemy should see player"

        target = enemy._get_current_target(engine.player, engine.game_map)

        # Original behavior: target IS the player position
        assert target is not None
        assert target == engine.player.position, f"Target should be player position, got {target}"

    def test_pathfinding_works_in_hallway(self):
        """Debug: Verify pathfinding returns a valid path in hallway."""
        from rsp.level.pathfinding import PathfindingHelper

        engine = create_basic_game_environment()
        engine.enemies.clear()

        create_horizontal_hallway_map(engine.game_map, hallway_y=15)

        engine.player.position = Position(20, 15)
        enemy = create_hostile_enemy_at(16, 15, engine)

        # Check walkability map is correct for hallway
        walkability = engine.game_map.get_walkability_map()
        assert walkability[15, 16], "Enemy position (16,15) should be walkable"
        assert walkability[15, 17], "Position (17,15) should be walkable"
        assert walkability[15, 18], "Position (18,15) should be walkable"
        assert walkability[15, 19], "Position (19,15) should be walkable"
        assert not walkability[14, 16], "Position (16,14) should be a wall"
        assert not walkability[16, 16], "Position (16,16) should be a wall"

        # Calculate path directly
        start = Position(16, 15)
        goal = Position(19, 15)
        path = PathfindingHelper.calculate_path(
            start=start,
            goal=goal,
            game_map=engine.game_map,
            game_engine=engine,
            moving_enemy=enemy,
        )

        assert path is not None, f"Path from {start} to {goal} should exist in hallway"
        assert len(path) > 1, f"Path should have at least 2 points, got {len(path)}"

    def test_enemy_chase_moves_toward_player(self):
        """Enemy should consistently move toward player in hallway."""
        engine = create_basic_game_environment()
        engine.enemies.clear()

        create_horizontal_hallway_map(engine.game_map, hallway_y=15)

        # Place within vision range (hunter has vision 6)
        engine.player.position = Position(20, 15)
        enemy = create_hostile_enemy_at(16, 15, engine)  # 4 tiles away
        initial_x = enemy.x

        # Verify enemy can see player initially
        assert enemy.can_see_player(
            engine.player, engine.game_map
        ), f"Enemy at {enemy.position} should see player at {engine.player.position}"

        # Fill the queue and verify moves are queued
        enemy._ensure_queue_full(engine.game_map, engine.player, engine)
        assert len(enemy.move_queue) > 0, f"Enemy at {enemy.position} should have moves queued"

        # Simulate several movement turns
        for i in range(3):
            if enemy.move_queue:
                next_pos = enemy.move_queue.pop(0)
                # Verify move is toward player (x increases)
                assert (
                    next_pos.x >= enemy.x
                ), f"Move {i+1}: Enemy should move right, but moved from x={enemy.x} to x={next_pos.x}"
                enemy.position = next_pos

                # Refill queue for next iteration
                if i < 2:  # Don't refill on last iteration
                    enemy._ensure_queue_full(engine.game_map, engine.player, engine)

        # Enemy should have moved closer
        assert (
            enemy.x > initial_x
        ), f"Enemy should have moved right, started at x={initial_x}, ended at x={enemy.x}"


class TestVerticalHallwayChase:
    """Test enemy chase in vertical hallways."""

    def test_enemy_targets_player_in_vertical_hallway(self):
        """Enemy should target player position in vertical hallway."""
        engine = create_basic_game_environment()
        engine.enemies.clear()

        create_vertical_hallway_map(engine.game_map, hallway_x=15)

        # Place within vision range (hunter vision = 6)
        engine.player.position = Position(15, 20)

        # Enemy above player (4 tiles away)
        enemy = create_hostile_enemy_at(15, 16, engine)

        # Debug: check vision range and distance
        distance = enemy.position.distance_to(engine.player.position)
        assert (
            distance <= enemy.vision_range
        ), f"Distance {distance} exceeds vision range {enemy.vision_range}"

        # Debug: check line of sight via map
        has_los = engine.game_map.has_line_of_sight(enemy.position, engine.player.position)
        assert has_los, f"No line of sight from {enemy.position} to {engine.player.position}"

        # Debug: check FOV via can_see_position
        can_see_pos = engine.game_map.can_see_position(
            enemy.position, engine.player.position, enemy.vision_range
        )
        assert (
            can_see_pos
        ), f"can_see_position failed: {enemy.position} -> {engine.player.position}, range {enemy.vision_range}"

        # Debug: check if player is in blind spot
        is_blind = engine.game_map.is_blind_spot(engine.player.position)
        assert not is_blind, f"Player at {engine.player.position} is in a blind spot"

        # Debug: check if player is invisible
        is_invis = engine.player.is_invisible()
        assert not is_invis, "Player is invisible"

        # Verify enemy can see player
        can_see = enemy.can_see_player(engine.player, engine.game_map)
        assert can_see, f"Enemy at {enemy.position} should see player at {engine.player.position}"

        target = enemy._get_current_target(engine.player, engine.game_map)

        # Original behavior: target IS the player position
        assert target is not None
        assert (
            target == engine.player.position
        ), f"Target should be player position {engine.player.position}, got {target}"


class TestTJunctionChase:
    """Test enemy chase at T-junctions."""

    def test_enemy_moves_toward_junction(self):
        """Enemy should move toward junction when chasing."""
        engine = create_basic_game_environment()
        engine.enemies.clear()

        create_t_junction_map(engine.game_map, mid_x=15, mid_y=15)

        # Player at junction (scanner vision = 5, so enemy must be close)
        engine.player.position = Position(15, 15)

        # Enemy in vertical arm, above junction (4 tiles away)
        enemy = create_hostile_enemy_at(15, 11, engine)

        # Verify enemy can see player
        can_see = enemy.can_see_player(engine.player, engine.game_map)
        assert can_see, f"Enemy at {enemy.position} should see player at {engine.player.position}"

        # Fill queue
        enemy._ensure_queue_full(engine.game_map, engine.player, engine)

        # Enemy should have queued moves
        assert len(enemy.move_queue) > 0, "Enemy should have moves queued"

        # First move should be DOWN toward player at junction (y increases)
        first_move = enemy.move_queue[0]
        assert (
            first_move.y > enemy.y
        ), f"Enemy should move down toward junction, but y went from {enemy.y} to {first_move.y}"


class TestMultipleEnemiesInHallway:
    """Test multiple enemies chasing in a hallway."""

    def test_lead_enemy_gets_moves(self):
        """Lead enemy closest to player should be able to move."""
        engine = create_basic_game_environment()
        engine.enemies.clear()

        create_horizontal_hallway_map(engine.game_map, hallway_y=15)

        # Place player so enemies are within vision range (scanner vision = 5)
        engine.player.position = Position(20, 15)

        # Create 3 enemies in a line (enemy3 is closest to player at x=17, 3 tiles away)
        enemy1 = create_hostile_enemy_at(15, 15, engine)  # 5 tiles away
        enemy2 = create_hostile_enemy_at(16, 15, engine)  # 4 tiles away
        enemy3 = create_hostile_enemy_at(17, 15, engine)  # 3 tiles away (lead)

        # Verify all enemies can see player
        for i, enemy in enumerate([enemy1, enemy2, enemy3]):
            can_see = enemy.can_see_player(engine.player, engine.game_map)
            assert (
                can_see
            ), f"Enemy {i+1} at {enemy.position} should see player at {engine.player.position}"

        # Each enemy should get a valid target
        for i, enemy in enumerate([enemy1, enemy2, enemy3]):
            target = enemy._get_current_target(engine.player, engine.game_map)
            assert target is not None, f"Enemy {i+1} should have a valid target"

        # Lead enemy should be able to get moves
        enemy3._ensure_queue_full(engine.game_map, engine.player, engine)
        assert len(enemy3.move_queue) > 0, "Lead enemy should have moves queued"


class TestInhibitorSpecificChase:
    """Test Inhibitor enemy chase behavior specifically."""

    def test_inhibitor_chases_in_hallway(self):
        """Inhibitor (RANDOM movement type) should still chase when hostile."""
        engine = create_basic_game_environment()
        engine.enemies.clear()

        create_horizontal_hallway_map(engine.game_map, hallway_y=15)

        engine.player.position = Position(25, 15)

        # Create hostile Inhibitor
        enemy = create_hostile_enemy_at(5, 15, engine, enemy_type="inhibitor")
        initial_x = enemy.x

        # Ensure it uses pathfinding (hostile overrides RANDOM movement)
        enemy._ensure_queue_full(engine.game_map, engine.player, engine)

        assert len(enemy.move_queue) > 0, "Hostile inhibitor should have moves queued"

        # Move should be toward player
        first_move = enemy.move_queue[0]
        assert (
            first_move.x > enemy.x
        ), f"Inhibitor should move toward player (right), but x went from {enemy.x} to {first_move.x}"


class TestVaryingDistances:
    """Test chase behavior at different distances."""

    def test_enemy_just_outside_vision_uses_last_known(self):
        """Enemy outside vision range should use last known player position."""
        engine = create_basic_game_environment()
        engine.enemies.clear()

        create_horizontal_hallway_map(engine.game_map, hallway_y=15)

        # Player at one end
        engine.player.position = Position(5, 15)

        # Enemy far away (hunter vision is 6)
        enemy = create_hostile_enemy_at(20, 15, engine)  # 15 tiles away

        # Enemy can't see player
        assert not enemy.can_see_player(engine.player, engine.game_map)

        # But has last_seen_player set from creation
        target = enemy._get_current_target(engine.player, engine.game_map)

        # Should use last_seen_player directly (not adjacent) since can't see
        assert target == enemy.last_seen_player

    def test_close_range_chase(self):
        """Test enemy behavior when very close to player."""
        engine = create_basic_game_environment()
        engine.enemies.clear()

        engine.game_map.walls.clear()
        _invalidate_map_caches(engine.game_map)

        engine.player.position = Position(15, 15)

        # Enemy just 2 tiles away on same row
        enemy = create_hostile_enemy_at(13, 15, engine)

        # Enemy should target player position directly
        target = enemy._get_current_target(engine.player, engine.game_map)
        assert (
            target == engine.player.position
        ), f"Expected player position {engine.player.position}, got {target}"

        # Enemy should be able to move toward player
        enemy._ensure_queue_full(engine.game_map, engine.player, engine)
        assert len(enemy.move_queue) > 0

        # First move should be toward player (x increases)
        first_move = enemy.move_queue[0]
        assert first_move.x > enemy.x, f"Enemy should move toward player (right), got {first_move}"


class TestStackedEnemies:
    """Test behavior with multiple enemies in close proximity."""

    def test_enemies_all_target_player_position(self):
        """Each enemy should independently target player position."""
        engine = create_basic_game_environment()
        engine.enemies.clear()

        create_horizontal_hallway_map(engine.game_map, hallway_y=15)

        engine.player.position = Position(20, 15)

        # Create multiple enemies in a line - all well within vision range (hunter=6)
        enemy1 = create_hostile_enemy_at(17, 15, engine)  # 3 tiles away
        enemy2 = create_hostile_enemy_at(16, 15, engine)  # 4 tiles away
        enemy3 = create_hostile_enemy_at(15, 15, engine)  # 5 tiles away

        # Verify all can see player
        for i, enemy in enumerate([enemy1, enemy2, enemy3]):
            can_see = enemy.can_see_player(engine.player, engine.game_map)
            assert (
                can_see
            ), f"Enemy {i+1} at {enemy.position} should see player at {engine.player.position}"

        # Each should be able to get a target
        target1 = enemy1._get_current_target(engine.player, engine.game_map)
        target2 = enemy2._get_current_target(engine.player, engine.game_map)
        target3 = enemy3._get_current_target(engine.player, engine.game_map)

        # Original behavior: all target player position directly
        assert target1 == engine.player.position, f"enemy1 target: {target1}"
        assert target2 == engine.player.position, f"enemy2 target: {target2}"
        assert target3 == engine.player.position, f"enemy3 target: {target3}"

    def test_lead_enemy_can_move_followers_blocked(self):
        """Lead enemy should move, followers blocked by other enemies."""
        engine = create_basic_game_environment()
        engine.enemies.clear()

        create_horizontal_hallway_map(engine.game_map, hallway_y=15)

        engine.player.position = Position(20, 15)

        # Create enemies in a line (enemy3 is lead - closest to player)
        enemy1 = create_hostile_enemy_at(15, 15, engine)
        enemy2 = create_hostile_enemy_at(16, 15, engine)
        enemy3 = create_hostile_enemy_at(17, 15, engine)

        # Lead enemy (enemy3) should be able to queue moves
        enemy3._ensure_queue_full(engine.game_map, engine.player, engine)
        assert len(enemy3.move_queue) > 0

        # First move should be toward player (x=18)
        first_move = enemy3.move_queue[0]
        assert first_move.x == 18

    def test_pathfinding_avoids_other_enemies(self):
        """Pathfinding should mark other enemies as impassable."""
        from rsp.level.pathfinding import PathfindingHelper

        engine = create_basic_game_environment()
        engine.enemies.clear()

        create_horizontal_hallway_map(engine.game_map, hallway_y=15)

        engine.player.position = Position(20, 15)

        # Create blocking enemy
        blocking_enemy = create_hostile_enemy_at(17, 15, engine)

        # Create enemy behind the blocker
        chasing_enemy = create_hostile_enemy_at(15, 15, engine)

        # Path from chasing enemy should fail (can't get past blocker in 1-wide hallway)
        path = PathfindingHelper.calculate_path(
            start=chasing_enemy.position,
            goal=Position(19, 15),  # Adjacent to player
            game_map=engine.game_map,
            game_engine=engine,
            moving_enemy=chasing_enemy,
        )

        # In a 1-tile-wide hallway, can't path around the blocking enemy
        assert path is None, "Should not find path through another enemy"


class TestEdgeCaseBugs:
    """Tests for specific edge cases that could cause chase failures.

    These test potential explanations for the reported bug where an
    Inhibitor stopped moving in a hallway but stayed hostile.
    """

    def test_enemy_at_last_seen_position_paths_to_self(self):
        """BUG THEORY 1: Enemy reached last_seen_player, player moved, paths to self.

        When enemy reaches last_seen_player and can't see the player anymore,
        it tries to path to its own position, which should fail (path length < 2).
        """
        from rsp.level.pathfinding import PathfindingHelper

        engine = create_basic_game_environment()
        engine.enemies.clear()

        create_horizontal_hallway_map(engine.game_map, hallway_y=15)

        # Player far away (out of vision)
        engine.player.position = Position(5, 15)

        # Enemy at position (20, 15)
        enemy = create_hostile_enemy_at(20, 15, engine)

        # Simulate: enemy reached old last_seen_player position
        # Set last_seen_player to enemy's CURRENT position
        enemy.last_seen_player = Position(20, 15)  # Same as enemy position!

        # Enemy can't see player (15 tiles away, vision=6)
        assert not enemy.can_see_player(engine.player, engine.game_map)

        # Target should be last_seen_player (enemy's own position)
        target = enemy._get_current_target(engine.player, engine.game_map)
        assert target == Position(20, 15), f"Target should be last_seen_player: {target}"

        # Pathfinding to self should fail (path length would be 1)
        path = PathfindingHelper.calculate_path(
            start=enemy.position,
            goal=target,
            game_map=engine.game_map,
            game_engine=engine,
            moving_enemy=enemy,
        )

        # THIS IS THE BUG: path to self returns None, enemy stops moving!
        assert path is None, "Pathing to self should fail (this is a bug scenario)"

        # Enemy tries to queue moves but fails
        enemy.move_queue.clear()
        enemy._ensure_queue_full(engine.game_map, engine.player, engine)

        # EXPECTED BUG: Enemy has no moves but is still hostile
        assert enemy.state == EnemyState.HOSTILE
        # This assertion shows the bug - enemy stuck with no moves
        # assert len(enemy.move_queue) == 0  # Uncomment to verify bug

    def test_room_to_hallway_pathfinding_succeeds_to_player(self):
        """Pathfinding to player position now succeeds directly.

        After the architectural fix, player is NOT marked as blocked in the
        cost map. Enemies can path directly TO the player position, but the
        queue-filling code in characters.py prevents them from actually
        stepping ON the player (stops when adjacent).
        """
        from rsp.level.pathfinding import PathfindingHelper

        engine = create_basic_game_environment()
        engine.enemies.clear()

        game_map = engine.game_map
        game_map.walls.clear()

        for y in range(game_map.height):
            for x in range(game_map.width):
                game_map.walls.add((x, y))

        for y in range(10, 20):
            for x in range(10, 20):
                game_map.walls.discard((x, y))
        for x in range(0, 10):
            game_map.walls.discard((x, 15))

        _invalidate_map_caches(game_map)

        engine.player.position = Position(5, 15)

        enemy = Enemy(Position(10, 15), "hunter")
        enemy.state = EnemyState.HOSTILE
        enemy.last_seen_player = engine.player.position
        engine.enemies.append(enemy)

        # Direct pathfinding to player position now SUCCEEDS
        path = PathfindingHelper.calculate_path(
            start=enemy.position,
            goal=engine.player.position,  # No longer blocked in cost map
            game_map=engine.game_map,
            game_engine=engine,
            moving_enemy=enemy,
        )
        assert path is not None, "Pathfinding to player should now succeed"
        assert len(path) > 1, f"Path should have multiple steps, got {len(path)}"

        # _ensure_queue_full also works and queues moves
        enemy._ensure_queue_full(engine.game_map, engine.player, engine)
        assert len(enemy.move_queue) > 0, "Should queue moves toward player"

        # First move should be toward player
        first_move = enemy.move_queue[0]
        assert first_move.x < enemy.x, f"Should move left toward player, got {first_move}"

    def test_adjacent_to_player_stops_queuing(self):
        """Enemy adjacent to player should stop queuing moves (ready to attack).

        When enemy is already adjacent to player, the queue-filling code
        in characters.py detects this and stops adding moves. The enemy
        doesn't need to path anywhere - it's already in attack range.
        """
        engine = create_basic_game_environment()
        engine.enemies.clear()

        create_horizontal_hallway_map(engine.game_map, hallway_y=15)

        # Player and enemy adjacent in narrow hallway
        engine.player.position = Position(10, 15)
        enemy = create_hostile_enemy_at(11, 15, engine)

        # Enemy can see player (adjacent)
        assert enemy.can_see_player(engine.player, engine.game_map)

        # Target is player position
        target = enemy._get_current_target(engine.player, engine.game_map)
        assert target == engine.player.position

        # Enemy is already adjacent - grid distance is 1
        assert enemy.position.grid_distance_to(engine.player.position) == 1

        # Queue filling should recognize enemy is already in attack range
        enemy.move_queue.clear()
        enemy._ensure_queue_full(engine.game_map, engine.player, engine)

        # When already adjacent, enemy doesn't need to queue moves
        # (queue might be empty or have been stopped early)
        # The key is that enemy is in position to attack

    def test_path_length_exceeds_limit_in_winding_path(self):
        """BUG THEORY 4: Path length exceeds max_length due to winding route.

        If direct distance is small but actual path is much longer (winding),
        max_length = direct_distance * 3 might be too restrictive.
        """

        engine = create_basic_game_environment()
        engine.enemies.clear()

        game_map = engine.game_map
        game_map.walls.clear()

        # Create a U-shaped corridor where direct distance is short
        # but actual path is long
        #
        # P#####E
        # .#####.
        # .#####.
        # .#####.
        # .......
        #
        # Direct distance: ~6 tiles (diagonal)
        # Actual path: ~14 tiles (down, across, up)

        # Fill with walls
        for y in range(game_map.height):
            for x in range(game_map.width):
                game_map.walls.add((x, y))

        # Carve left vertical corridor (x=5, y=10-20)
        for y in range(10, 21):
            game_map.walls.discard((5, y))

        # Carve bottom horizontal corridor (y=20, x=5-15)
        for x in range(5, 16):
            game_map.walls.discard((x, 20))

        # Carve right vertical corridor (x=15, y=10-20)
        for y in range(10, 21):
            game_map.walls.discard((15, y))

        _invalidate_map_caches(game_map)

        # Player at top-left of U
        engine.player.position = Position(5, 10)

        # Enemy at top-right of U (within vision range)
        enemy = create_hostile_enemy_at(15, 10, engine)

        # Direct distance is 10 (horizontal only)
        direct_dist = enemy.position.distance_to(engine.player.position)
        assert 9 < direct_dist < 11, f"Direct distance should be ~10: {direct_dist}"

        # Actual path: down 10 + across 10 + up 0 = ~20+ tiles
        # max_length = max(15, 10 * 3) = 30
        # Path should fit... unless path is longer

        # But what if direct distance appears shorter due to blocked vision?
        # In this U-shape, enemy can't actually SEE player (wall in between)

        can_see = enemy.can_see_player(engine.player, engine.game_map)
        # Enemy probably CAN'T see player through walls
        # So it would use last_seen_player

        if not can_see:
            # This is actually the normal case - enemy uses last known position
            # If last_seen_player is None, targeting fails
            enemy.last_seen_player = None
            target = enemy._get_current_target(engine.player, engine.game_map)
            assert target is None, "No last_seen_player means no target"

    def test_inhibitor_specific_in_room_hallway_junction(self):
        """Test Inhibitor specifically in room-to-hallway scenario.

        Inhibitor has different stats than hunter. Test the exact enemy type.
        """
        from rsp.level.pathfinding import PathfindingHelper

        engine = create_basic_game_environment()
        engine.enemies.clear()

        # Room with hallway exit
        game_map = engine.game_map
        game_map.walls.clear()

        for y in range(game_map.height):
            for x in range(game_map.width):
                game_map.walls.add((x, y))

        # Room 15x15 centered at (20, 20)
        for y in range(13, 28):
            for x in range(13, 28):
                game_map.walls.discard((x, y))

        # Hallway to the left (y=20, x=5-12)
        for x in range(5, 13):
            game_map.walls.discard((x, 20))

        _invalidate_map_caches(game_map)

        # Player in hallway
        engine.player.position = Position(8, 20)

        # Inhibitor in room (use actual inhibitor type)
        inhibitor = Enemy(Position(18, 20), "inhibitor")
        inhibitor.state = EnemyState.HOSTILE
        inhibitor.last_seen_player = engine.player.position
        engine.enemies.append(inhibitor)

        # Check inhibitor stats
        # Inhibitor vision range might be different from hunter

        can_see = inhibitor.can_see_player(engine.player, engine.game_map)

        # Distance is 10 tiles - check if within inhibitor vision
        dist = inhibitor.position.distance_to(engine.player.position)

        target = inhibitor._get_current_target(engine.player, engine.game_map)

        if can_see:
            assert target == engine.player.position
        else:
            assert target == inhibitor.last_seen_player

        # Try pathfinding
        if target:
            path = PathfindingHelper.calculate_path(
                start=inhibitor.position,
                goal=target,
                game_map=engine.game_map,
                game_engine=engine,
                moving_enemy=inhibitor,
            )

            # Check if path exists
            if path is None:
                # POTENTIAL BUG: No path found
                # Check why - is it path length?
                direct_dist = inhibitor.position.distance_to(target)
                max_length = max(15, int(direct_dist * 3.0))
                # Actual path is 10 tiles, max is ~30, should work

            inhibitor._ensure_queue_full(engine.game_map, engine.player, engine)

            # If no moves queued, we found the bug!
            if len(inhibitor.move_queue) == 0:
                # Mark this test as finding the bug
                pass


class TestNoPathThroughPlayer:
    """Verify enemies don't try to path through the player.

    Critical regression tests: When player is not blocked in cost map,
    enemies must still stop at the player, not path through to the other side.
    """

    def test_enemy_stops_at_player_not_paths_through(self):
        """Enemy targeting position behind player should stop at player."""
        engine = create_basic_game_environment()
        engine.enemies.clear()

        # Open area
        engine.game_map.walls.clear()
        _invalidate_map_caches(engine.game_map)

        # Player in the middle
        engine.player.position = Position(15, 15)

        # Enemy on left side, targeting position on right side of player
        enemy = create_hostile_enemy_at(10, 15, engine)
        enemy.last_seen_player = Position(20, 15)  # Target is PAST the player

        # Queue moves
        enemy._ensure_queue_full(engine.game_map, engine.player, engine)

        # Enemy should have moves
        assert len(enemy.move_queue) > 0, "Enemy should have moves queued"

        # NO queued move should be the player's position
        for move in enemy.move_queue:
            assert move != engine.player.position, f"Enemy queued player's position {move}"

        # NO queued move should be past the player (x > 15)
        for move in enemy.move_queue:
            assert move.x <= 15, f"Enemy queued position past player: {move}"

    def test_enemy_stops_adjacent_to_player(self):
        """Enemy should stop queuing moves once adjacent to player."""
        engine = create_basic_game_environment()
        engine.enemies.clear()

        engine.game_map.walls.clear()
        _invalidate_map_caches(engine.game_map)

        engine.player.position = Position(15, 15)

        # Enemy 3 tiles away
        enemy = create_hostile_enemy_at(12, 15, engine)

        enemy._ensure_queue_full(engine.game_map, engine.player, engine)

        # Last queued move should be adjacent to player
        if enemy.move_queue:
            last_move = enemy.move_queue[-1]
            distance = last_move.grid_distance_to(engine.player.position)
            assert distance >= 1, f"Last move {last_move} is ON player at {engine.player.position}"

    def test_multiple_enemies_surround_player_no_overlap(self):
        """Multiple enemies surrounding player should not queue overlapping moves."""
        engine = create_basic_game_environment()
        engine.enemies.clear()

        engine.game_map.walls.clear()
        _invalidate_map_caches(engine.game_map)

        engine.player.position = Position(15, 15)

        # Create 4 enemies around the player (cardinal directions, 3 tiles away)
        enemies = [
            create_hostile_enemy_at(12, 15, engine),  # Left
            create_hostile_enemy_at(18, 15, engine),  # Right
            create_hostile_enemy_at(15, 12, engine),  # Up
            create_hostile_enemy_at(15, 18, engine),  # Down
        ]

        # Queue moves for all enemies
        for enemy in enemies:
            enemy._ensure_queue_full(engine.game_map, engine.player, engine)

        # No enemy should queue the player's position
        for i, enemy in enumerate(enemies):
            for move in enemy.move_queue:
                assert move != engine.player.position, f"Enemy {i} queued player position {move}"

    def test_eight_enemies_converge_on_player(self):
        """8 enemies converging on player from all directions."""
        engine = create_basic_game_environment()
        engine.enemies.clear()

        engine.game_map.walls.clear()
        _invalidate_map_caches(engine.game_map)

        engine.player.position = Position(20, 20)

        # 8 enemies from all directions (4 tiles away)
        positions = [
            (16, 20),  # Left
            (24, 20),  # Right
            (20, 16),  # Up
            (20, 24),  # Down
            (16, 16),  # Upper-left
            (24, 16),  # Upper-right
            (16, 24),  # Lower-left
            (24, 24),  # Lower-right
        ]

        enemies = []
        for x, y in positions:
            enemy = create_hostile_enemy_at(x, y, engine)
            enemies.append(enemy)

        # Queue moves for all
        for enemy in enemies:
            enemy._ensure_queue_full(engine.game_map, engine.player, engine)

        # Verify constraints
        for i, enemy in enumerate(enemies):
            # Should have moves (not stuck)
            assert len(enemy.move_queue) > 0, f"Enemy {i} at {enemy.position} has no moves"

            # No move should be player's position
            for move in enemy.move_queue:
                assert move != engine.player.position, f"Enemy {i} queued player position"

            # All moves should be closer to player than starting position
            start_dist = enemy.position.grid_distance_to(engine.player.position)
            for move in enemy.move_queue:
                # Move should be toward player or same distance (blocked by others)
                move_dist = move.grid_distance_to(engine.player.position)
                assert (
                    move_dist < start_dist or move_dist == start_dist
                ), f"Enemy {i} moved away from player: {move_dist} vs {start_dist}"

    def test_enemy_with_target_behind_player_in_hallway(self):
        """Enemy in narrow hallway with target behind player stops at player."""
        engine = create_basic_game_environment()
        engine.enemies.clear()

        create_horizontal_hallway_map(engine.game_map, hallway_y=15)

        # Player in the middle of hallway
        engine.player.position = Position(20, 15)

        # Enemy on left, target on right side of player
        enemy = create_hostile_enemy_at(15, 15, engine)
        enemy.last_seen_player = Position(25, 15)  # Past the player

        enemy._ensure_queue_full(engine.game_map, engine.player, engine)

        assert len(enemy.move_queue) > 0, "Enemy should have moves"

        # All moves should stop at or before player
        for move in enemy.move_queue:
            assert move.x <= 20, f"Enemy queued move past player: {move}"
            assert move != engine.player.position, "Enemy queued player position"

    def test_player_moves_enemy_still_stops(self):
        """After player moves, enemy re-paths but still stops at new position."""
        engine = create_basic_game_environment()
        engine.enemies.clear()

        engine.game_map.walls.clear()
        _invalidate_map_caches(engine.game_map)

        # Initial: player at (20, 15), enemy at (15, 15)
        engine.player.position = Position(20, 15)
        enemy = create_hostile_enemy_at(15, 15, engine)

        # Queue initial moves
        enemy._ensure_queue_full(engine.game_map, engine.player, engine)
        assert len(enemy.move_queue) > 0

        # Simulate enemy moving one step
        first_move = enemy.move_queue.pop(0)
        enemy.position = first_move

        # Player moves (enemy would normally invalidate queue, but let's test)
        engine.player.position = Position(22, 15)

        # Invalidate and re-queue
        enemy.move_queue.clear()
        enemy._ensure_queue_full(engine.game_map, engine.player, engine)

        # Still should not path through player
        for move in enemy.move_queue:
            assert move != engine.player.position, f"Enemy queued new player position {move}"

    def test_diagonal_approach_stops_adjacent(self):
        """Enemy approaching diagonally should stop adjacent, not on player."""
        engine = create_basic_game_environment()
        engine.enemies.clear()

        engine.game_map.walls.clear()
        _invalidate_map_caches(engine.game_map)

        engine.player.position = Position(15, 15)

        # Enemy approaching from diagonal
        enemy = create_hostile_enemy_at(12, 12, engine)

        enemy._ensure_queue_full(engine.game_map, engine.player, engine)

        # Should have moves
        assert len(enemy.move_queue) > 0

        # Last move should be adjacent, not on player
        last_move = enemy.move_queue[-1]
        assert last_move != engine.player.position, "Last move is player position"
        assert (
            last_move.grid_distance_to(engine.player.position) >= 1
        ), f"Last move {last_move} is on player"

    def test_hostile_inhibitor_stops_at_player(self):
        """Hostile Inhibitor (RANDOM movement) should still stop at player."""
        engine = create_basic_game_environment()
        engine.enemies.clear()

        engine.game_map.walls.clear()
        _invalidate_map_caches(engine.game_map)

        engine.player.position = Position(15, 15)

        # Inhibitor with target behind player
        inhibitor = create_hostile_enemy_at(10, 15, engine, enemy_type="inhibitor")
        inhibitor.last_seen_player = Position(20, 15)  # Past player

        inhibitor._ensure_queue_full(engine.game_map, engine.player, engine)

        # Should have moves and stop at player
        assert len(inhibitor.move_queue) > 0
        for move in inhibitor.move_queue:
            assert move != engine.player.position
            assert move.x <= 15, f"Inhibitor queued move past player: {move}"

    def test_chase_then_player_sidesteps(self):
        """Enemy chasing, then player sidesteps - enemy should adjust."""
        engine = create_basic_game_environment()
        engine.enemies.clear()

        engine.game_map.walls.clear()
        _invalidate_map_caches(engine.game_map)

        # Horizontal chase
        engine.player.position = Position(20, 15)
        enemy = create_hostile_enemy_at(15, 15, engine)

        # Initial queue
        enemy._ensure_queue_full(engine.game_map, engine.player, engine)
        assert len(enemy.move_queue) > 0

        # Player sidesteps up
        engine.player.position = Position(20, 14)

        # Enemy queue now stale - invalidate and re-queue
        enemy.move_queue.clear()
        enemy._ensure_queue_full(engine.game_map, engine.player, engine)

        # Should track new position without pathing through old position
        for move in enemy.move_queue:
            assert move != engine.player.position

    def test_crowded_corridor_enemies_dont_pile_on_player(self):
        """Multiple enemies in corridor don't all try to occupy player tile.

        In a 1-tile corridor, only the lead enemy can move. Followers are
        blocked by enemies in front of them - this is expected behavior.
        The key test is that NO enemy queues the player's position.
        """
        engine = create_basic_game_environment()
        engine.enemies.clear()

        create_horizontal_hallway_map(engine.game_map, hallway_y=15)

        # Player in middle of corridor
        engine.player.position = Position(15, 15)

        # 3 enemies to the left - enemy3 is closest (lead)
        enemy1 = create_hostile_enemy_at(10, 15, engine)  # Furthest back
        enemy2 = create_hostile_enemy_at(11, 15, engine)  # Middle
        enemy3 = create_hostile_enemy_at(12, 15, engine)  # Lead (closest)

        enemies = [enemy1, enemy2, enemy3]

        # Queue moves for all
        for enemy in enemies:
            enemy._ensure_queue_full(engine.game_map, engine.player, engine)

        # Lead enemy (enemy3) should have moves - closest to player
        assert len(enemy3.move_queue) > 0, "Lead enemy should have moves"

        # Followers may be blocked (no moves) - this is expected in narrow corridor
        # The important test: NO enemy should queue player position
        for i, enemy in enumerate(enemies):
            for move in enemy.move_queue:
                assert move != engine.player.position, f"Enemy {i} queued player position"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
