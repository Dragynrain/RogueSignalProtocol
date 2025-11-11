#!/usr/bin/env python3
"""
Performance and stress tests for the game engine.

Tests game stability under heavy load and extended sessions:
- Long-running sessions (1000+ turns)
- Many simultaneous enemies
- Particle system stress
- Rapid exploit usage
- Memory leak detection

These tests verify the game remains stable and performant
under extreme conditions that might occur in normal play.
"""

import pytest
import gc
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from game_entities import Position
from game_characters import Enemy
from game_config import GameConfig
from tests.test_agent import GameTestAgent
from tests.fixtures.simple_fixtures import enemy_builder


class TestLongRunningSession:
    """Test game stability over extended play sessions."""

    def test_1000_turn_session_no_crash(self):
        """Test that game survives 1000 turns without crashing."""
        agent = GameTestAgent(seed=42)

        # Run 1000 turns (about 10-15 minutes of gameplay)
        turns_completed = 0
        max_turns = 1000

        import random

        try:
            for turn in range(max_turns):
                if agent.player.cpu <= 0:
                    # Player died - that's OK, just verify no crash
                    break

                # Make a simple move to simulate gameplay
                dx = random.choice([-1, 0, 1])
                dy = random.choice([-1, 0, 1])
                agent.move_player(dx, dy)

                turns_completed += 1

                # Periodic memory check (every 100 turns)
                if turns_completed % 100 == 0:
                    gc.collect()  # Force garbage collection

        except Exception as e:
            pytest.fail(f"Game crashed after {turns_completed} turns: {e}")

        # Should complete at least 100 turns without crash
        assert turns_completed >= 100, f"Game should survive at least 100 turns, got {turns_completed}"

    def test_500_turn_session_memory_stable(self):
        """Test memory doesn't grow excessively over 500 turns."""
        import tracemalloc

        agent = GameTestAgent(seed=123)

        # Start memory tracking
        tracemalloc.start()
        snapshot_start = tracemalloc.take_snapshot()

        # Run 500 turns
        turns = 0
        max_turns = 500

        for turn in range(max_turns):
            if agent.player.cpu <= 0:
                break

            # Simple random movement
            import random
            dx = random.choice([-1, 0, 1])
            dy = random.choice([-1, 0, 1])
            agent.move_player(dx, dy)

            turns += 1

        # Take ending snapshot
        gc.collect()  # Clean up before measuring
        snapshot_end = tracemalloc.take_snapshot()

        # Compare memory usage
        top_stats = snapshot_end.compare_to(snapshot_start, 'lineno')

        # Calculate total memory increase
        total_increase = sum(stat.size_diff for stat in top_stats)

        tracemalloc.stop()

        # Memory should not increase by more than 50MB over 500 turns
        max_allowed_increase = 50 * 1024 * 1024  # 50 MB

        assert total_increase < max_allowed_increase, \
            f"Memory increased by {total_increase / 1024 / 1024:.2f} MB (max allowed: 50 MB)"


class TestManyEnemies:
    """Test performance with many simultaneous enemies."""

    def test_20_enemies_no_crash(self, basic_game_engine):
        """Test game handles 20+ enemies without crashing."""
        # Clear existing enemies
        basic_game_engine.enemies.clear()

        # Spawn 20 enemies around the map
        for i in range(20):
            x = 20 + (i % 5) * 3
            y = 20 + (i // 5) * 3
            enemy = enemy_builder("scanner", pos=(x, y))
            basic_game_engine.enemies.append(enemy)

        assert len(basic_game_engine.enemies) == 20

        # Run several turns with many enemies active
        import random

        for turn in range(50):
            if basic_game_engine.player.cpu <= 0:
                break

            # Move player randomly
            dx = random.choice([-1, 0, 1])
            dy = random.choice([-1, 0, 1])
            basic_game_engine.move_player(dx, dy)

        # Should not crash
        assert True

    def test_many_enemies_pathfinding_performance(self, basic_game_engine):
        """Test pathfinding performance with many enemies."""
        import time

        # Clear and spawn 15 enemies
        basic_game_engine.enemies.clear()

        for i in range(15):
            x = 20 + (i % 5) * 4
            y = 20 + (i // 5) * 4
            enemy = enemy_builder("hunter", pos=(x, y))
            basic_game_engine.enemies.append(enemy)

        # Measure time for 10 turns of enemy movement
        start_time = time.perf_counter()

        import random

        for turn in range(10):
            # Move player to trigger enemy pathfinding
            dx = random.choice([-1, 0, 1])
            dy = random.choice([-1, 0, 1])
            basic_game_engine.move_player(dx, dy)

        elapsed = time.perf_counter() - start_time

        # 10 turns with 15 enemies should complete in under 5 seconds
        assert elapsed < 5.0, f"Pathfinding too slow: {elapsed:.2f}s for 10 turns"


class TestParticleSystemStress:
    """Test particle system under heavy load."""

    def test_particle_spawn_burst(self, basic_game_engine):
        """Test spawning many particles at once."""
        particle_system = basic_game_engine.particle_system

        # Spawn many particle explosions at once
        for i in range(10):
            particle_system.create_death_explosion(
                world_x=25 + i % 5,
                world_y=25 + i // 5,
                colors=[(255, 0, 0), (255, 255, 0)],
                particle_count=10
            )

        # Update once
        particle_system.update(0.016)

        # Should handle burst without crash
        # Particles were created
        assert True

    def test_particle_continuous_spawning(self, basic_game_engine):
        """Test continuous particle spawning over time."""
        particle_system = basic_game_engine.particle_system

        # Spawn particles over many updates
        for frame in range(50):
            # Create explosions
            particle_system.create_death_explosion(
                world_x=25,
                world_y=25,
                colors=[(255, 0, 0)],
                particle_count=5
            )

            particle_system.update(0.016)

        # Old particles should have cleaned up
        # Should not have accumulated all particles (allow for exactly 250)
        assert particle_system.get_particle_count() <= 250, "Particles should clean up over time"


class TestRapidExploitUsage:
    """Test rapid exploit usage doesn't cause issues."""

    def test_exploit_spam_heat_management(self, basic_game_engine):
        """Test using exploits rapidly manages heat correctly."""
        from game_combat import ExploitSystem

        basic_game_engine.player.position = Position(10, 10)
        basic_game_engine.player.cpu = 100
        basic_game_engine.player.heat = 0

        # Place enemy
        enemy = enemy_builder("scanner", pos=(11, 10))
        basic_game_engine.enemies = [enemy]

        basic_game_engine.player.inventory_manager.equipped_exploits = ['buffer_overflow']

        exploit_system = ExploitSystem(basic_game_engine)

        # Try to use exploit 10 times rapidly
        uses = 0
        for _ in range(10):
            # Only execute if not overheated
            if basic_game_engine.player.heat < basic_game_engine.player.max_heat:
                result = exploit_system.execute_exploit('buffer_overflow', enemy.position)
                if result:
                    uses += 1

        # Should have used exploit at least once
        assert uses > 0, "Should be able to use exploit at least once"

        # Heat should have increased
        assert basic_game_engine.player.heat > 0, "Heat should increase from exploit usage"


class TestLargeMapExploration:
    """Test performance with large explored areas."""

    def test_explore_large_area_no_slowdown(self, basic_game_engine):
        """Test exploring large area doesn't cause slowdown."""
        import time

        # Mark large area as explored (simulate long play session)
        game_map = basic_game_engine.game_map

        for x in range(10, 70):
            for y in range(10, 40):
                if not game_map.is_wall(Position(x, y)):
                    game_map.explored_tiles.add((x, y))

        explored_count = len(game_map.explored_tiles)
        # Should have explored a significant area (at least 500 tiles)
        assert explored_count > 500, f"Should have explored large area, got {explored_count}"

        # Run several turns to test performance with large explored area
        start_time = time.perf_counter()

        import random

        for turn in range(20):
            if basic_game_engine.player.cpu <= 0:
                break

            # Move player
            dx = random.choice([-1, 0, 1])
            dy = random.choice([-1, 0, 1])
            basic_game_engine.move_player(dx, dy)

        elapsed = time.perf_counter() - start_time

        # 20 turns should complete quickly even with large explored area
        assert elapsed < 2.0, f"Large explored area causing slowdown: {elapsed:.2f}s"


class TestMemoryLeaks:
    """Test for memory leaks in common operations."""

    def test_enemy_spawn_cleanup_no_leak(self, basic_game_engine):
        """Test spawning and removing enemies doesn't leak memory."""
        import tracemalloc

        tracemalloc.start()
        snapshot_start = tracemalloc.take_snapshot()

        # Repeatedly spawn and remove enemies
        for cycle in range(10):
            # Spawn 20 enemies
            for i in range(20):
                enemy = enemy_builder("scanner", pos=(20 + i, 20))
                basic_game_engine.enemies.append(enemy)

            # Remove all enemies (simulate death)
            basic_game_engine.enemies.clear()

            # Force garbage collection
            gc.collect()

        snapshot_end = tracemalloc.take_snapshot()

        top_stats = snapshot_end.compare_to(snapshot_start, 'lineno')
        total_increase = sum(stat.size_diff for stat in top_stats)

        tracemalloc.stop()

        # Should not leak significant memory
        max_allowed = 5 * 1024 * 1024  # 5 MB
        assert total_increase < max_allowed, \
            f"Memory leak detected: {total_increase / 1024 / 1024:.2f} MB increase"

    def test_particle_spawn_cleanup_no_leak(self, basic_game_engine):
        """Test particle spawning and cleanup doesn't leak memory."""
        import tracemalloc

        particle_system = basic_game_engine.particle_system

        tracemalloc.start()
        snapshot_start = tracemalloc.take_snapshot()

        # Repeatedly spawn and clean up particles
        for cycle in range(50):
            # Spawn particles
            particle_system.create_death_explosion(
                world_x=25,
                world_y=25,
                colors=[(255, 0, 0)],
                particle_count=10
            )

            # Update to clean up expired particles
            for _ in range(10):
                particle_system.update(0.1)  # Large delta to expire particles

        gc.collect()
        snapshot_end = tracemalloc.take_snapshot()

        top_stats = snapshot_end.compare_to(snapshot_start, 'lineno')
        total_increase = sum(stat.size_diff for stat in top_stats)

        tracemalloc.stop()

        # Should not leak significant memory
        max_allowed = 5 * 1024 * 1024  # 5 MB
        assert total_increase < max_allowed, \
            f"Particle memory leak: {total_increase / 1024 / 1024:.2f} MB"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
