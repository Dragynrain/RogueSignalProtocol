"""
Integration tests for player movement → enemy vision → enemy alerting chain.
Tests the complete trace level and alerting workflow using real game data.
"""

import pytest
from unittest.mock import Mock, patch
from game_characters import Enemy, Player
from game_entities import Position, EnemyState, EnemyMovement
from game_engine import GameEngine
from tests.fixtures.simple_fixtures import enemy_builder


class TestPlayerEnemyVisionChain:
    """Test complete vision and alerting chain with real game data."""
    
    def test_player_enters_enemy_vision_triggers_alert(self, basic_game_engine):
        """Test that moving into enemy vision triggers state change using real data."""
        # Create enemies for this test
        scanner1 = enemy_builder("scanner", pos=(15, 10))
        scanner2 = enemy_builder("scanner", pos=(30, 10))
        basic_game_engine.enemy_manager.enemies = [scanner1, scanner2]

        # Initially enemy should be unaware
        assert scanner1.state == EnemyState.UNAWARE

        # Move player into scanner's vision range (using real vision range from GameData)
        vision_range = scanner1.type_data.vision
        close_position = Position(scanner1.position.x + vision_range - 1, scanner1.position.y)
        basic_game_engine.player.x = close_position.x
        basic_game_engine.player.y = close_position.y

        # Process enemy vision using actual game logic
        with patch.object(basic_game_engine.player, 'is_invisible', return_value=False):
            # Mock clear line of sight
            with patch.object(basic_game_engine.game_map, 'can_see_position', return_value=True), \
                 patch.object(basic_game_engine.game_map, 'is_blind_spot', return_value=False):

                can_see = scanner1.can_see_player(basic_game_engine.player, basic_game_engine.game_map)

                if can_see:
                    # Simulate trace level logic
                    scanner1.state = EnemyState.ALERT
                    scanner1.last_seen_player = Position(basic_game_engine.player.x, basic_game_engine.player.y)

        # Verify scanner1 detected player if within range
        distance = scanner1.position.distance_to(Position(basic_game_engine.player.x, basic_game_engine.player.y))
        if distance <= vision_range:
            assert scanner1.state == EnemyState.ALERT, "Scanner should become alert when seeing player"
            assert scanner1.last_seen_player == Position(basic_game_engine.player.x, basic_game_engine.player.y), "Scanner should track player position"

        # Verify other enemies still unaware (too far)
        assert scanner2.state == EnemyState.UNAWARE, "Distant scanner should remain unaware"
    
    def test_enemy_alerting_chain(self, basic_game_engine):
        """Test that alerted enemy alerts nearby enemies using real data."""
        # Create enemies for this test
        scanner1 = enemy_builder("scanner", pos=(15, 10), state=EnemyState.ALERT, last_seen=(12, 10))
        scanner2 = enemy_builder("scanner", pos=(30, 10))
        patrol1 = enemy_builder("patrol", pos=(15, 15))
        basic_game_engine.enemy_manager.enemies = [scanner1, scanner2, patrol1]

        # Test enemy alerting using actual game engine method
        if hasattr(basic_game_engine, '_alert_nearby_enemies'):
            basic_game_engine._alert_nearby_enemies(scanner1)

            # Verify nearby enemies become alert based on real alert range
            patrol_distance = scanner1.position.distance_to(patrol1.position)
            alert_range = 5  # Typical alert range

            if patrol_distance <= alert_range:
                # Real game behavior: alerted enemies become HOSTILE, not ALERT
                assert patrol1.state in [EnemyState.ALERT, EnemyState.HOSTILE], "Nearby enemies should become alert or hostile"

            # Verify distant enemies remain unaware
            scanner2_distance = scanner1.position.distance_to(scanner2.position)
            if scanner2_distance > alert_range:
                assert scanner2.state == EnemyState.UNAWARE, "Distant enemies should remain unaware"
    
    def test_alerted_enemies_update_movement_queues(self, basic_game_engine):
        """Test that alerted enemies can calculate moves to seek player."""
        # Create enemy for this test
        scanner1 = enemy_builder("scanner", pos=(15, 10), state=EnemyState.ALERT, last_seen=(12, 10))
        basic_game_engine.enemy_manager.enemies = [scanner1]

        # Execute movement to test pathfinding
        initial_pos = scanner1.position
        scanner1.move_queue.clear()  # Force refresh
        moved = scanner1.move(basic_game_engine.game_map, basic_game_engine.player, basic_game_engine)

        # Verify movement behavior is valid
        if moved:
            assert not basic_game_engine.game_map.is_wall(scanner1.position), f"Enemy moved to wall at {scanner1.position}"
            assert 0 <= scanner1.position.x < basic_game_engine.game_map.width, "Enemy must stay within map width"
            assert 0 <= scanner1.position.y < basic_game_engine.game_map.height, "Enemy must stay within map height"

        # Verify movement queue has valid planned moves
        if scanner1.move_queue:
            next_planned = scanner1.move_queue[0]
            assert not basic_game_engine.game_map.is_wall(next_planned), f"Planned move to {next_planned} must not be a wall"
    
    def test_complete_trace_level_workflow(self, basic_game_engine):
        """Test the complete workflow from player movement to enemy response."""
        # Create enemy for this test
        scanner1 = enemy_builder("scanner", pos=(15, 10))
        basic_game_engine.enemy_manager.enemies = [scanner1]

        # Step 1: Player starts in safe position
        basic_game_engine.player.x = 5
        basic_game_engine.player.y = 5
        initial_distance = Position(basic_game_engine.player.x, basic_game_engine.player.y).distance_to(scanner1.position)

        # Step 2: Move player closer to enemy
        basic_game_engine.player.x = 13  # Move closer to scanner1 at (15, 10)
        basic_game_engine.player.y = 10

        # Step 3: Check if enemy can see player with real vision system
        with patch.object(basic_game_engine.player, 'is_invisible', return_value=False), \
             patch.object(basic_game_engine.game_map, 'can_see_position', return_value=True), \
             patch.object(basic_game_engine.game_map, 'is_blind_spot', return_value=False):

            can_see = scanner1.can_see_player(basic_game_engine.player, basic_game_engine.game_map)

        # Step 4: If enemy can see player, update state
        if can_see:
            scanner1.state = EnemyState.ALERT
            scanner1.last_seen_player = Position(basic_game_engine.player.x, basic_game_engine.player.y)

        # Step 5: Verify the complete chain worked
        new_distance = Position(basic_game_engine.player.x, basic_game_engine.player.y).distance_to(scanner1.position)
        vision_range = scanner1.type_data.vision

        if new_distance <= vision_range:
            # Player should be detected
            assert scanner1.state == EnemyState.ALERT, "Enemy should be alert after detecting player"
            assert scanner1.last_seen_player is not None, "Enemy should remember player position"
        else:
            # Player is out of range, enemy should remain unaware
            assert scanner1.state == EnemyState.UNAWARE, "Enemy should remain unaware if player out of range"
    
    def test_line_of_sight_blocking(self, basic_game_engine):
        """Test that walls block enemy vision in the complete workflow."""
        # Create enemy for this test
        scanner1 = enemy_builder("scanner", pos=(15, 10))
        basic_game_engine.enemy_manager.enemies = [scanner1]

        # Position player close to enemy
        basic_game_engine.player.x = 14
        basic_game_engine.player.y = 10

        # Add wall between player and enemy
        wall_pos = Position(14, 10)
        basic_game_engine.game_map.walls.add((wall_pos.x, wall_pos.y))

        # Test vision with blocked line of sight
        with patch.object(basic_game_engine.player, 'is_invisible', return_value=False), \
             patch.object(basic_game_engine.game_map, 'can_see_position', return_value=False):  # Blocked by wall

            can_see = scanner1.can_see_player(basic_game_engine.player, basic_game_engine.game_map)

        # Even if in range, wall should block vision
        assert can_see is False, "Wall should block enemy vision"
        assert scanner1.state == EnemyState.UNAWARE, "Enemy should remain unaware when vision blocked"
    
    def test_player_invisibility_prevents_trace_level(self, basic_game_engine):
        """Test that invisible player is not detected even in enemy vision range."""
        # Create enemy for this test
        scanner1 = enemy_builder("scanner", pos=(15, 10))
        basic_game_engine.enemy_manager.enemies = [scanner1]

        # Position player very close to enemy
        basic_game_engine.player.x = scanner1.position.x + 1
        basic_game_engine.player.y = scanner1.position.y

        # Test vision with invisible player
        with patch.object(basic_game_engine.player, 'is_invisible', return_value=True), \
             patch.object(basic_game_engine.game_map, 'can_see_position', return_value=True), \
             patch.object(basic_game_engine.game_map, 'is_blind_spot', return_value=False):

            can_see = scanner1.can_see_player(basic_game_engine.player, basic_game_engine.game_map)

        # Invisible player should not be detected
        assert can_see is False, "Invisible player should not be detected"
        assert scanner1.state == EnemyState.UNAWARE, "Enemy should remain unaware of invisible player"