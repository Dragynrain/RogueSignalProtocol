#!/usr/bin/env python3
"""
Integration tests for gateway reachability validation.

Ensures that generated levels always have a path from spawn to gateway.
"""

import pytest
from game_engine import GameEngine
from game_entities import Position


class TestGatewayReachability:
    """Test that gateway is always reachable from spawn."""

    def test_new_game_gateway_is_reachable(self):
        """New game should have reachable gateway."""
        engine = GameEngine()

        spawn_pos = Position(engine.player.x, engine.player.y)
        gateway_pos = engine.game_map.gateway

        # Validate using the same method as level generation
        assert engine.level_generator._validate_gateway_reachability(spawn_pos, gateway_pos), \
            f"Gateway at {gateway_pos} is NOT reachable from spawn {spawn_pos}!"

    def test_multiple_level_generations_all_reachable(self):
        """Test that multiple level generations all produce reachable gateways."""
        failures = []

        for seed in range(10):  # Test 10 different seeds
            engine = GameEngine()
            engine.game_state.dungeon_seed = seed
            engine.level_generator.generate_level(level=1, seed=seed)

            # Update player position to spawn location
            engine.player.x = 6
            engine.player.y = 6
            spawn_pos = Position(engine.player.x, engine.player.y)
            gateway_pos = engine.game_map.gateway

            is_reachable = engine.level_generator._validate_gateway_reachability(spawn_pos, gateway_pos)
            if not is_reachable:
                failures.append(f"Seed {seed}: Gateway at {gateway_pos} unreachable from {spawn_pos}")

        assert len(failures) == 0, f"Found {len(failures)} unreachable gateways:\n" + "\n".join(failures)

    def test_level_transitions_maintain_reachability(self):
        """Test that advancing to next level maintains gateway reachability."""
        engine = GameEngine()

        for level_num in range(1, 4):  # Test levels 1-3
            spawn_pos = Position(engine.player.x, engine.player.y)
            gateway_pos = engine.game_map.gateway

            assert engine.level_generator._validate_gateway_reachability(spawn_pos, gateway_pos), \
                f"Level {level_num}: Gateway at {gateway_pos} is NOT reachable from spawn {spawn_pos}!"

            # Advance to next level if not at max
            if level_num < 3:
                engine.game_state.level = level_num + 1
                engine.level_generator.generate_level(level_num + 1, engine.game_state.dungeon_seed)
                engine.player.x = 6  # Reset to spawn
                engine.player.y = 6

    def test_spawn_room_not_sealed(self):
        """Test that spawn room (2,2,8,8) is not completely sealed."""
        engine = GameEngine()

        # Check that there's at least one exit from spawn room
        spawn_room_exits = 0
        for x in range(2, 10):
            for y in range(2, 10):
                pos = Position(x, y)
                if not engine.game_map.is_wall(pos):
                    # Check if this floor tile has a neighbor outside spawn room
                    for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                        neighbor = Position(x + dx, y + dy)
                        if (neighbor.x < 2 or neighbor.x >= 10 or
                            neighbor.y < 2 or neighbor.y >= 10):
                            # This is an edge of spawn room
                            if not engine.game_map.is_wall(neighbor):
                                spawn_room_exits += 1
                                break

        assert spawn_room_exits > 0, "Spawn room (2,2,8,8) is completely sealed with no exits!"

    def test_gateway_not_in_spawn_room(self):
        """Test that gateway is not placed inside spawn room."""
        engine = GameEngine()

        gateway = engine.game_map.gateway

        # Gateway should not be in spawn room bounds (2,2,8,8)
        in_spawn_room = (2 <= gateway.x < 10 and 2 <= gateway.y < 10)

        assert not in_spawn_room, \
            f"Gateway at {gateway} is inside spawn room (2,2,8,8) - too close to start!"
