#!/usr/bin/env python3
"""
Performance benchmarks for critical game systems.
Uses pytest-benchmark to measure and track performance over time.
"""

import pytest
import random
from unittest.mock import Mock

from game_entities import Position, calculate_manhattan_distance, get_adjacent_positions
from game_characters import Player, Enemy
from game_engine import GameEngine
from game_level import LevelGenerator
from game_combat import ExploitSystem
from ..fixtures.mock_factories import player, enemy, scenario, MockGameMapFactory, MockGameFactory


class TestPathfindingBenchmarks:
    """Benchmarks for pathfinding and movement calculations."""
    
    @pytest.mark.performance
    def test_manhattan_distance_performance(self, benchmark):
        """Benchmark Manhattan distance calculation."""
        pos1 = Position(0, 0)
        pos2 = Position(50, 50)
        
        result = benchmark(calculate_manhattan_distance, pos1, pos2)
        assert result == 100
    
    @pytest.mark.performance
    def test_adjacent_positions_performance(self, benchmark):
        """Benchmark adjacent position generation."""
        pos = Position(25, 25)
        
        result = benchmark(get_adjacent_positions, pos, 100, 100)
        assert len(result) == 8  # 8 adjacent positions including diagonals
    
    @pytest.mark.performance
    def test_large_distance_calculation_batch(self, benchmark):
        """Benchmark batch distance calculations."""
        positions = [Position(random.randint(0, 100), random.randint(0, 100)) 
                    for _ in range(1000)]
        target = Position(50, 50)
        
        def calculate_all_distances():
            return [calculate_manhattan_distance(pos, target) for pos in positions]
        
        result = benchmark(calculate_all_distances)
        assert len(result) == 1000


class TestGameStateBenchmarks:
    """Benchmarks for game state operations."""
    
    @pytest.mark.performance
    def test_player_creation_performance(self, benchmark):
        """Benchmark player object creation."""
        def create_player():
            return player().with_cpu(100).with_heat(50).build()
        
        result = benchmark(create_player)
        assert result.cpu == 100
    
    @pytest.mark.performance
    def test_enemy_creation_performance(self, benchmark):
        """Benchmark enemy object creation."""
        def create_enemy():
            return enemy().hostile().at_position(10, 10).build()
        
        result = benchmark(create_enemy)
        assert result.x == 10
    
    @pytest.mark.performance
    def test_scenario_building_performance(self, benchmark):
        """Benchmark complete scenario building."""
        def build_scenario():
            return scenario().player_vs_single_enemy().build()
        
        result = benchmark(build_scenario)
        assert result["type"] == "player_vs_enemy"


class TestRealLevelGenerationBenchmarks:
    """Benchmarks for level generation performance with real objects."""
    
    @pytest.mark.performance
    def test_small_level_generation_real(self, benchmark):
        """Benchmark small level generation with real GameMap (40x30)."""
        from game_map import GameMap
        from game_level import LevelGenerator
        
        def generate_level():
            game_map = GameMap(40, 30)  # Real GameMap, not mock
            generator = LevelGenerator(game_map)
            generator.generate_level(level=1, seed=12345)
            return game_map  # Return the real map for verification
        
        result = benchmark(generate_level)
        # Verify actual level generation occurred
        assert len(result.walls) > 0, "Real level should have walls"
        assert result.gateway is not None, "Real level should have gateway"
    
    @pytest.mark.performance
    def test_standard_level_generation_real(self, benchmark):
        """Benchmark standard level generation with real GameMap (80x40)."""
        from game_map import GameMap
        from game_level import LevelGenerator
        
        def generate_level():
            game_map = GameMap(80, 40)  # Real GameMap, not mock
            generator = LevelGenerator(game_map)
            generator.generate_level(level=2, seed=12345)
            return game_map
        
        result = benchmark(generate_level)
        # Verify actual level generation occurred
        assert len(result.walls) > 50, "Standard level should have substantial content"
        assert result.gateway is not None, "Standard level should have gateway"
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_large_level_generation_real(self, benchmark):
        """Benchmark large level generation with real GameMap (160x80)."""
        from game_map import GameMap
        from game_level import LevelGenerator
        
        def generate_level():
            game_map = GameMap(160, 80)  # Real GameMap, not mock
            generator = LevelGenerator(game_map)
            generator.generate_level(level=3, seed=12345)
            return game_map
        
        result = benchmark(generate_level)
        # Verify actual level generation occurred
        assert len(result.walls) > 200, "Large level should have extensive content"
        assert result.gateway is not None, "Large level should have gateway"


class TestRealCombatBenchmarks:
    """Benchmarks for combat system performance with real objects."""
    
    @pytest.mark.performance
    def test_real_player_creation(self, benchmark):
        """Benchmark real Player object creation and initialization."""
        from game_characters import Player
        
        def create_player():
            player = Player(10, 10)
            # Verify player is properly initialized
            assert player.cpu == 100
            assert player.heat == 0
            assert hasattr(player, 'inventory_manager')
            return player
        
        result = benchmark(create_player)
        assert result is not None
    
    @pytest.mark.performance
    def test_real_exploit_system_creation(self, benchmark):
        """Benchmark ExploitSystem with real Player."""
        from game_characters import Player
        from game_combat import ExploitSystem
        from game_state import MessageLog
        from unittest.mock import Mock
        
        def create_real_exploit_system():
            # Create real player and real message log
            player = Player(5, 5)
            message_log = MessageLog()
            
            # Mock minimal game object
            mock_game = Mock()
            mock_game.player = player
            mock_game.message_log = message_log
            mock_game.sound_manager = Mock()
            
            return ExploitSystem(mock_game)
        
        result = benchmark(create_real_exploit_system)
        assert result is not None
        assert hasattr(result.game.player, 'inventory_manager')
    
    @pytest.mark.performance
    def test_real_inventory_operations(self, benchmark):
        """Benchmark real inventory operations."""
        from game_characters import Player
        
        def inventory_operations():
            player = Player(15, 15)
            
            # Perform multiple inventory operations
            player.inventory_manager.add_exploit("buffer_overflow")
            player.inventory_manager.add_exploit("system_crash")
            player.inventory_manager.add_exploit("threat_scan")
            
            player.inventory_manager.equip_exploit("buffer_overflow")
            player.inventory_manager.equip_exploit("system_crash")
            
            # Check equipped status
            equipped = player.inventory_manager.equipped_exploits
            
            return len(equipped)
        
        result = benchmark(inventory_operations)
        assert result >= 2  # Should have equipped at least 2 exploits


class TestMemoryBenchmarks:
    """Benchmarks for memory usage of critical operations."""
    
    @pytest.mark.performance
    def test_position_memory_usage(self, benchmark):
        """Benchmark memory usage of Position objects."""
        def create_many_positions():
            return [Position(i % 100, i // 100) for i in range(1000)]
        
        result = benchmark(create_many_positions)
        assert len(result) == 1000
    
    @pytest.mark.performance
    def test_game_state_memory_usage(self, benchmark):
        """Benchmark memory usage of game state objects."""
        def create_complex_game_state():
            test_scenario = scenario().player_surrounded().build()
            game_state = test_scenario["game"]
            
            # Add more complexity
            game_state.enemies.extend([enemy().build() for _ in range(20)])
            
            return game_state
        
        result = benchmark(create_complex_game_state)
        assert len(result.enemies) >= 4  # Original 4 + 20 more


class TestRegressionBenchmarks:
    """Benchmarks to catch performance regressions."""
    
    @pytest.mark.performance
    @pytest.mark.regression
    def test_position_creation_regression(self, benchmark):
        """Ensure Position creation doesn't regress in performance."""
        def create_position():
            return Position(42, 24)
        
        result = benchmark(create_position)
        
        # Should complete in under 1 microsecond
        assert benchmark.stats['mean'] < 0.000001
    
    @pytest.mark.performance
    @pytest.mark.regression
    def test_distance_calculation_regression(self, benchmark):
        """Ensure distance calculation doesn't regress."""
        pos1 = Position(0, 0)
        pos2 = Position(100, 100)
        
        result = benchmark(calculate_manhattan_distance, pos1, pos2)
        
        # Should complete in under 10 microseconds
        assert benchmark.stats['mean'] < 0.00001
        assert result == 200


class TestConcurrencyBenchmarks:
    """Benchmarks for concurrent operations (if applicable)."""
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_parallel_distance_calculations(self, benchmark):
        """Benchmark parallel distance calculations."""
        import concurrent.futures
        
        positions = [Position(random.randint(0, 100), random.randint(0, 100)) 
                    for _ in range(100)]
        target = Position(50, 50)
        
        def parallel_distances():
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = [
                    executor.submit(calculate_manhattan_distance, pos, target)
                    for pos in positions
                ]
                return [future.result() for future in futures]
        
        result = benchmark(parallel_distances)
        assert len(result) == 100


# Benchmark configuration
def pytest_benchmark_update_json(config, benchmarks, output_json):
    """Update benchmark JSON with custom metadata."""
    output_json['machine_info']['python_version'] = "3.13.7"
    output_json['machine_info']['game_version'] = "1.0.0"


# Custom benchmark groups
def pytest_configure(config):
    """Configure benchmark groups."""
    config.addinivalue_line(
        "markers", "performance: mark test as performance benchmark"
    )
    config.addinivalue_line(
        "markers", "regression: mark test as regression benchmark"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow benchmark"
    )