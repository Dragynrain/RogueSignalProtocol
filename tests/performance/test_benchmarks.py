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


class TestLevelGenerationBenchmarks:
    """Benchmarks for level generation performance."""
    
    @pytest.mark.performance
    def test_small_level_generation(self, benchmark):
        """Benchmark small level generation (40x30)."""
        def generate_level():
            game_map = MockGameMapFactory.create_basic_map(40, 30)
            generator = LevelGenerator(game_map)
            return generator.generate_level(40, 30, seed=12345)
        
        result = benchmark(generate_level)
        assert result is not None
    
    @pytest.mark.performance
    def test_standard_level_generation(self, benchmark):
        """Benchmark standard level generation (80x40)."""
        def generate_level():
            game_map = MockGameMapFactory.create_basic_map(80, 40)
            generator = LevelGenerator(game_map)
            return generator.generate_level(80, 40, seed=12345)
        
        result = benchmark(generate_level)
        assert result is not None
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_large_level_generation(self, benchmark):
        """Benchmark large level generation (160x80)."""
        def generate_level():
            game_map = MockGameMapFactory.create_basic_map(160, 80)
            generator = LevelGenerator(game_map)
            return generator.generate_level(160, 80, seed=12345)
        
        result = benchmark(generate_level)
        assert result is not None


class TestCombatBenchmarks:
    """Benchmarks for combat system performance."""
    
    @pytest.mark.performance
    def test_exploit_system_creation(self, benchmark):
        """Benchmark exploit system initialization."""
        def create_exploit_system():
            mock_game = MockGameFactory.create_basic_game()
            return ExploitSystem(mock_game)
        
        result = benchmark(create_exploit_system)
        assert result is not None
    
    @pytest.mark.performance
    def test_single_exploit_calculation(self, benchmark):
        """Benchmark single exploit damage calculation."""
        mock_game = MockGameFactory.create_basic_game()
        exploit_system = ExploitSystem(mock_game)
        mock_player = player().build()
        mock_enemy = enemy().build()
        
        def calculate_exploit():
            return exploit_system.calculate_exploit_damage(
                "buffer_overflow", mock_player, mock_enemy
            )
        
        result = benchmark(calculate_exploit)
        assert isinstance(result, (int, type(None)))
    
    @pytest.mark.performance
    def test_multiple_exploit_calculations(self, benchmark):
        """Benchmark multiple exploit calculations."""
        mock_game = MockGameFactory.create_basic_game()
        exploit_system = ExploitSystem(mock_game)
        mock_player = player().build()
        enemies = [enemy().build() for _ in range(10)]
        
        def calculate_multiple_exploits():
            results = []
            for enemy_obj in enemies:
                damage = exploit_system.calculate_exploit_damage(
                    "buffer_overflow", mock_player, enemy_obj
                )
                results.append(damage)
            return results
        
        result = benchmark(calculate_multiple_exploits)
        assert len(result) == 10


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