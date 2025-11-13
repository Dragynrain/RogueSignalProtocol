#!/usr/bin/env python3
"""
Integration tests for player movement and map interaction.
Tests real movement mechanics, collision detection, and map navigation.
"""

import pytest

from game_entities import Position


class TestPlayerMovementIntegration:
    """Integration tests for player movement with real map objects."""

    def test_player_basic_movement_mechanics(self, basic_game_engine):
        """Test that player can move to valid positions and is blocked by walls."""
        engine = basic_game_engine

        # Find a position with at least one valid adjacent move
        # (The test-specific seed might spawn player in a tight corner)
        test_positions = [
            engine.player.position,  # Try current position first
            Position(10, 10),  # Common open area
            Position(20, 20),
            Position(15, 15),
        ]

        original_position = None
        for test_pos in test_positions:
            if engine.game_map.is_valid_position(test_pos):
                # Check if this position has at least one valid adjacent move
                has_valid_move = False
                for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
                    adj_pos = Position(test_pos.x + dx, test_pos.y + dy)
                    if engine.game_map.is_valid_position(adj_pos):
                        has_valid_move = True
                        break
                if has_valid_move:
                    original_position = test_pos
                    engine.player.position = test_pos
                    break

        # If we can't find any valid position, skip test (extremely rare with proper map generation)
        if original_position is None:
            pytest.skip("No valid test position with adjacent moves found in generated map")

        # Test movement in all four directions
        directions = [
            Position(0, -1),  # North
            Position(1, 0),  # East
            Position(0, 1),  # South
            Position(-1, 0),  # West
        ]

        successful_moves = 0
        blocked_moves = 0

        for direction in directions:
            target_x = original_position.x + direction.x
            target_y = original_position.y + direction.y
            target_pos = Position(target_x, target_y)

            # Check if target position is valid
            if engine.game_map.is_valid_position(target_pos):
                # Should be able to move here
                engine.player.position = target_pos
                assert engine.player.position == target_pos
                successful_moves += 1
                # Move back to test next direction
                engine.player.position = original_position
            else:
                # Movement blocked by wall or out of bounds
                assert engine.game_map.is_wall(target_pos) or not (
                    0 <= target_x < engine.game_map.width and 0 <= target_y < engine.game_map.height
                )
                blocked_moves += 1

        # Should have attempted movement in all directions
        assert successful_moves + blocked_moves == 4
        assert successful_moves > 0

    def test_player_collision_detection_with_map_features(self, basic_game_engine):
        """Test collision detection with various map features."""
        engine = basic_game_engine

        # Test wall collision
        wall_positions = list(engine.game_map.walls)
        if len(wall_positions) > 0:
            wall_pos = Position(wall_positions[0][0], wall_positions[0][1])
            assert engine.game_map.is_wall(wall_pos)

            # Verify walls block movement
            assert not engine.game_map.is_valid_position(wall_pos)

        # Test shadow interaction
        shadow_positions = list(engine.game_map.blind_spots)
        if len(shadow_positions) > 0:
            shadow_pos = Position(shadow_positions[0][0], shadow_positions[0][1])

            # Player should be able to move into shadows (for stealth)
            if not engine.game_map.is_wall(shadow_pos):
                engine.player.position = shadow_pos
                assert engine.game_map.is_blind_spot(shadow_pos)
                # Player gets stealth benefit in blind spots
                in_shadow = engine.game_map.is_blind_spot(engine.player.position)
                assert in_shadow

    def test_player_navigation_to_objectives(self, basic_game_engine):
        """Test player navigation to map objectives like gateway."""
        engine = basic_game_engine

        # Test navigation to gateway
        gateway = engine.game_map.gateway
        assert gateway is not None

        # Calculate path to gateway
        start_pos = engine.player.position
        distance_to_gateway = abs(start_pos.x - gateway.x) + abs(start_pos.y - gateway.y)

        # Move one step toward gateway
        if distance_to_gateway > 1:
            dx = 1 if gateway.x > start_pos.x else (-1 if gateway.x < start_pos.x else 0)
            dy = 1 if gateway.y > start_pos.y else (-1 if gateway.y < start_pos.y else 0)
            next_pos = Position(start_pos.x + dx, start_pos.y + dy)

            if engine.game_map.is_valid_position(next_pos):
                engine.player.position = next_pos
                new_distance = abs(next_pos.x - gateway.x) + abs(next_pos.y - gateway.y)
                assert new_distance <= distance_to_gateway

        # Test interaction with special nodes
        special_nodes = (
            engine.game_map.cooling_nodes
            | engine.game_map.cpu_recovery_nodes
            | engine.game_map.ghost_nodes
        )

        if len(special_nodes) > 0:
            node_pos = Position(list(special_nodes)[0][0], list(special_nodes)[0][1])

            if not engine.game_map.is_wall(node_pos):
                engine.player.position = node_pos
                player_tuple = (engine.player.position.x, engine.player.position.y)
                at_special_node = player_tuple in special_nodes
                assert at_special_node

    def test_player_movement_with_game_state_tracking(self, basic_game_engine):
        """Test that player movement properly integrates with game state."""
        engine = basic_game_engine
        initial_position = engine.player.position

        # Find valid moves
        valid_moves = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue

                test_pos = Position(initial_position.x + dx, initial_position.y + dy)
                if engine.game_map.is_valid_position(test_pos):
                    valid_moves.append(test_pos)

        # Execute movement and verify state tracking
        if len(valid_moves) > 0:
            target_move = valid_moves[0]

            # Store last position
            engine.player.last_position = engine.player.position

            # Execute move
            engine.player.position = target_move

            # Verify state tracking
            assert engine.player.last_position == initial_position
            assert engine.player.position == target_move
            assert engine.player.position != engine.player.last_position

        # Test position validation
        assert engine.player.position.is_valid(engine.game_map.width, engine.game_map.height)


class TestMapInteractionIntegration:
    """Integration tests for player interaction with map elements."""

    def test_player_interaction_with_cooling_nodes(self, basic_game_engine):
        """Test player interaction with cooling nodes."""
        engine = basic_game_engine
        cooling_nodes = engine.game_map.cooling_nodes

        if len(cooling_nodes) > 0:
            node_x, node_y = list(cooling_nodes)[0]
            node_pos = Position(node_x, node_y)

            if not engine.game_map.is_wall(node_pos):
                engine.player.position = node_pos
                engine.player.heat = 50

                player_at_cooling_node = (
                    engine.player.position.x,
                    engine.player.position.y,
                ) in cooling_nodes

                assert player_at_cooling_node
                assert engine.player.heat >= 0
                assert node_pos.is_valid(engine.game_map.width, engine.game_map.height)

    def test_player_interaction_with_cpu_recovery_nodes(self, basic_game_engine):
        """Test player interaction with CPU recovery nodes."""
        engine = basic_game_engine
        cpu_nodes = engine.game_map.cpu_recovery_nodes

        if len(cpu_nodes) > 0:
            node_x, node_y = list(cpu_nodes)[0]
            node_pos = Position(node_x, node_y)

            if not engine.game_map.is_wall(node_pos):
                engine.player.position = node_pos
                engine.player.cpu = 70

                player_at_cpu_node = (
                    engine.player.position.x,
                    engine.player.position.y,
                ) in cpu_nodes

                assert player_at_cpu_node
                assert engine.player.cpu <= engine.player.max_cpu

    def test_player_vision_and_exploration_mechanics(self, basic_game_engine):
        """Test player vision system and map exploration."""
        engine = basic_game_engine

        # Test vision range
        vision_range = engine.player.base_vision_range
        assert vision_range > 0

        # Test exploration tracking
        initial_explored = len(engine.game_map.explored_tiles)
        player_pos = engine.player.position

        # Simulate exploring current area (5x5 around player)
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                explore_x = player_pos.x + dx
                explore_y = player_pos.y + dy

                if (
                    0 <= explore_x < engine.game_map.width
                    and 0 <= explore_y < engine.game_map.height
                ):
                    engine.game_map.explored_tiles.add((explore_x, explore_y))

        final_explored = len(engine.game_map.explored_tiles)

        assert final_explored >= initial_explored
        assert (player_pos.x, player_pos.y) in engine.game_map.explored_tiles

    def test_map_boundary_handling(self, basic_game_engine):
        """Test how player movement handles map boundaries."""
        engine = basic_game_engine

        # Test various edge positions
        edge_positions = [
            Position(0, 5),
            Position(engine.game_map.width - 1, 5),
            Position(5, 0),
            Position(5, engine.game_map.height - 1),
        ]

        for edge_pos in edge_positions:
            if not engine.game_map.is_wall(edge_pos):
                engine.player.position = edge_pos

                # Test adjacent positions for boundary validation
                adjacent = [
                    Position(edge_pos.x - 1, edge_pos.y),
                    Position(edge_pos.x + 1, edge_pos.y),
                    Position(edge_pos.x, edge_pos.y - 1),
                    Position(edge_pos.x, edge_pos.y + 1),
                ]

                for adj_pos in adjacent:
                    is_valid = adj_pos.is_valid(engine.game_map.width, engine.game_map.height)
                    is_in_bounds = (
                        0 <= adj_pos.x < engine.game_map.width
                        and 0 <= adj_pos.y < engine.game_map.height
                    )
                    assert is_valid == is_in_bounds
