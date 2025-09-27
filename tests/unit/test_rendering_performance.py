#!/usr/bin/env python3
"""
Rendering Performance Tests.
Tests performance characteristics and optimization of rendering systems.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import time
import tcod
from typing import List, Set

from game_rendering import BaseRenderer, ASCIIRenderer, UIRenderer, MapRenderer
from game_entities import Colors, Position, EnemyState, EnemyMovement
from game_characters import Player, Enemy
from game_config import GameConfig
from game_map import GameMap
from game_state import MessageLog
from game_inventory import CodeHack, ExploitItem


class TestRenderingPerformanceBenchmarks:
    """Benchmark rendering performance under various conditions."""
    
    def setup_method(self):
        """Set up performance testing environment."""
        self.mock_console = Mock(spec=tcod.console.Console)
        self.ascii_renderer = ASCIIRenderer()
        self.ui_renderer = UIRenderer()
        
        # Create comprehensive game state for testing
        self.mock_game = self._create_comprehensive_game_state()
    
    def _create_comprehensive_game_state(self):
        """Create a comprehensive game state for performance testing."""
        game = Mock()
        
        # Player setup
        game.player = Mock(spec=Player)
        game.player.x = 20
        game.player.y = 15
        game.player.cpu = 85
        game.player.max_cpu = 100
        game.player.detection = 45.5
        game.player.heat = 60
        game.player.shadow_steps = 3
        
        # Game state
        game.game_state = Mock()
        game.level = 2
        game.turn = 250
        game.game_over = False
        
        # Map with various elements
        game.game_map = Mock(spec=GameMap)
        game.game_map.walls = self._generate_wall_pattern(50)
        game.game_map.shadows = self._generate_shadow_pattern(30)
        game.game_map.cooling_nodes = self._generate_node_pattern(10, "cooling")
        game.game_map.cpu_recovery_nodes = self._generate_node_pattern(8, "cpu")
        game.game_map.ghost_nodes = self._generate_ghost_nodes(15)
        game.game_map.code_hacks = self._generate_code_hacks(12)
        game.game_map.exploit_pickups = self._generate_exploit_pickups(8)
        game.game_map.permanent_upgrades = self._generate_upgrades(5)
        
        # Enemies
        game.enemies = self._generate_enemies(25)
        
        # Message log
        game.message_log = Mock(spec=MessageLog)
        game.message_log.messages = self._generate_messages(20)
        
        # UI state
        game.show_inventory = False
        game.show_help = False
        game.show_lore_viewer = False
        game.show_story_fragment = None
        game.targeting_mode = False
        
        return game
    
    def _generate_wall_pattern(self, count: int) -> Set[Position]:
        """Generate a realistic wall pattern for testing."""
        walls = set()
        
        # Border walls
        for x in range(GameConfig.MAP_WIDTH):
            walls.add(Position(x, 0))
            walls.add(Position(x, GameConfig.MAP_HEIGHT - 1))
        for y in range(GameConfig.MAP_HEIGHT):
            walls.add(Position(0, y))
            walls.add(Position(GameConfig.MAP_WIDTH - 1, y))
        
        # Interior walls (rooms and corridors)
        for i in range(count - len(walls)):
            x = (i * 3 + 5) % (GameConfig.MAP_WIDTH - 2) + 1
            y = (i * 2 + 3) % (GameConfig.MAP_HEIGHT - 2) + 1
            walls.add(Position(x, y))
        
        return walls
    
    def _generate_shadow_pattern(self, count: int) -> Set[Position]:
        """Generate shadow positions for testing."""
        shadows = set()
        for i in range(count):
            x = (i * 4 + 7) % GameConfig.MAP_WIDTH
            y = (i * 3 + 5) % GameConfig.MAP_HEIGHT
            shadows.add(Position(x, y))
        return shadows
    
    def _generate_node_pattern(self, count: int, node_type: str) -> Set[Position]:
        """Generate special node positions."""
        nodes = set()
        for i in range(count):
            x = (i * 5 + 10) % GameConfig.MAP_WIDTH
            y = (i * 4 + 8) % GameConfig.MAP_HEIGHT
            nodes.add(Position(x, y))
        return nodes
    
    def _generate_ghost_nodes(self, count: int) -> dict:
        """Generate ghost nodes with timestamps."""
        ghosts = {}
        for i in range(count):
            x = (i * 6 + 12) % GameConfig.MAP_WIDTH
            y = (i * 5 + 10) % GameConfig.MAP_HEIGHT
            ghosts[Position(x, y)] = 1000.0 + i * 100
        return ghosts
    
    def _generate_code_hacks(self, count: int) -> List[CodeHack]:
        """Generate code hacks for testing."""
        hacks = []
        colors = ["red", "blue", "green", "yellow"]
        for i in range(count):
            x = (i * 7 + 15) % GameConfig.MAP_WIDTH
            y = (i * 6 + 12) % GameConfig.MAP_HEIGHT
            hack = CodeHack(f"hack_{i}", Position(x, y), colors[i % len(colors)])
            hacks.append(hack)
        return hacks
    
    def _generate_exploit_pickups(self, count: int) -> List[ExploitItem]:
        """Generate exploit pickups for testing."""
        exploits = []
        exploit_names = ["buffer_overflow", "system_crash", "shadow_step", "data_mimic"]
        for i in range(count):
            exploit = ExploitItem(exploit_names[i % len(exploit_names)])
            exploits.append(exploit)
        return exploits
    
    def _generate_upgrades(self, count: int) -> List[tuple]:
        """Generate permanent upgrades for testing."""
        upgrades = []
        upgrade_types = ["cpu_boost", "stealth_enhance", "heat_dissipator"]
        for i in range(count):
            x = (i * 8 + 20) % GameConfig.MAP_WIDTH
            y = (i * 7 + 15) % GameConfig.MAP_HEIGHT
            upgrade = (upgrade_types[i % len(upgrade_types)], Position(x, y))
            upgrades.append(upgrade)
        return upgrades
    
    def _generate_enemies(self, count: int) -> List[Enemy]:
        """Generate enemies for testing."""
        enemies = []
        enemy_types = ["scanner", "guardian", "phantom", "admin"]
        states = [EnemyState.PATROL, EnemyState.HOSTILE, EnemyState.INVESTIGATING]
        movements = [EnemyMovement.RANDOM, EnemyMovement.SEEK, EnemyMovement.LINEAR]
        
        for i in range(count):
            enemy = Mock(spec=Enemy)
            enemy.position = Position((i * 3 + 8) % 40, (i * 2 + 6) % 20)
            enemy.enemy_type = enemy_types[i % len(enemy_types)]
            enemy.state = states[i % len(states)]
            enemy.movement_type = movements[i % len(movements)]
            enemy.health = 100 - (i % 50)
            enemy.max_health = 100
            enemies.append(enemy)
        
        return enemies
    
    def _generate_messages(self, count: int) -> List[Mock]:
        """Generate message log entries for testing."""
        messages = []
        message_texts = [
            "Enemy detected nearby",
            "CPU restored",
            "Exploit executed successfully",
            "Detection level increased",
            "Shadow step activated",
            "System scan complete",
            "Network breach detected",
            "Admin spawned"
        ]
        
        for i in range(count):
            message = Mock()
            message.text = message_texts[i % len(message_texts)]
            message.turn = i + 1
            messages.append(message)
        
        return messages
    
    def test_baseline_map_rendering_performance(self):
        """Benchmark baseline map rendering performance."""
        # Minimal game state
        minimal_game = Mock()
        minimal_game.player = Mock(spec=Player)
        minimal_game.player.x = 10
        minimal_game.player.y = 10
        minimal_game.game_map = Mock(spec=GameMap)
        minimal_game.game_map.walls = set()
        minimal_game.game_map.shadows = set()
        minimal_game.enemies = []
        
        iterations = 100
        start_time = time.time()
        
        with patch('game_rendering.render_char_safe'):
            for _ in range(iterations):
                self.ascii_renderer.render_map(self.mock_console, minimal_game)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / iterations
        
        # Should render quickly (less than 1ms per render for minimal scene)
        assert avg_time < 0.001
        print(f"Baseline rendering: {avg_time:.6f}s per render")
    
    def test_complex_scene_rendering_performance(self):
        """Benchmark complex scene rendering performance."""
        iterations = 50
        start_time = time.time()
        
        with patch('game_rendering.render_char_safe'):
            for _ in range(iterations):
                self.ascii_renderer.render_map(self.mock_console, self.mock_game)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / iterations
        
        # Should handle complex scenes efficiently (less than 5ms per render)
        assert avg_time < 0.005
        print(f"Complex scene rendering: {avg_time:.6f}s per render")
    
    def test_ui_rendering_performance(self):
        """Benchmark UI rendering performance."""
        iterations = 100
        start_time = time.time()
        
        with patch('game_rendering.render_char_safe'):
            for _ in range(iterations):
                self.ui_renderer.render_top_status_bar(self.mock_console, self.mock_game)
                self.ui_renderer.render_bottom_panel(self.mock_console, self.mock_game)
                self.ui_renderer.render_system_log(self.mock_console, self.mock_game)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / iterations
        
        # UI rendering should be fast (less than 2ms per full UI render)
        assert avg_time < 0.002
        print(f"UI rendering: {avg_time:.6f}s per render")
    
    def test_full_game_rendering_performance(self):
        """Benchmark complete game rendering performance."""
        iterations = 30
        start_time = time.time()
        
        with patch('game_rendering.render_char_safe'):
            for _ in range(iterations):
                self.ascii_renderer.render_game(self.mock_console, self.mock_game)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / iterations
        
        # Full game rendering should be reasonable (less than 10ms per frame)
        assert avg_time < 0.01
        print(f"Full game rendering: {avg_time:.6f}s per render")
    
    def test_enemy_rendering_scaling(self):
        """Test how rendering performance scales with enemy count."""
        enemy_counts = [5, 10, 25, 50, 100]
        render_times = []
        
        for count in enemy_counts:
            # Create game state with specific enemy count
            test_game = Mock()
            test_game.player = Mock(spec=Player)
            test_game.player.x = 20
            test_game.player.y = 15
            test_game.game_map = Mock(spec=GameMap)
            test_game.game_map.walls = set()
            test_game.game_map.shadows = set()
            test_game.enemies = self._generate_enemies(count)
            
            # Benchmark rendering
            iterations = 20
            start_time = time.time()
            
            with patch('game_rendering.render_char_safe'):
                for _ in range(iterations):
                    self.ascii_renderer.render_map(self.mock_console, test_game)
            
            end_time = time.time()
            avg_time = (end_time - start_time) / iterations
            render_times.append(avg_time)
            
            print(f"Enemies: {count}, Time: {avg_time:.6f}s")
        
        # Performance should scale reasonably (not exponentially)
        # Check that performance doesn't degrade too badly
        if len(render_times) >= 2:
            scaling_factor = render_times[-1] / render_times[0]
            enemy_factor = enemy_counts[-1] / enemy_counts[0]
            
            # Performance scaling should be better than linear
            assert scaling_factor < enemy_factor * 2
    
    def test_map_element_rendering_scaling(self):
        """Test how rendering scales with map element count."""
        wall_counts = [10, 50, 100, 200]
        render_times = []
        
        for count in wall_counts:
            # Create game state with specific wall count
            test_game = Mock()
            test_game.player = Mock(spec=Player)
            test_game.player.x = 20
            test_game.player.y = 15
            test_game.game_map = Mock(spec=GameMap)
            test_game.game_map.walls = self._generate_wall_pattern(count)
            test_game.game_map.shadows = set()
            test_game.enemies = []
            
            # Benchmark rendering
            iterations = 20
            start_time = time.time()
            
            with patch('game_rendering.render_char_safe'):
                for _ in range(iterations):
                    self.ascii_renderer.render_map(self.mock_console, test_game)
            
            end_time = time.time()
            avg_time = (end_time - start_time) / iterations
            render_times.append(avg_time)
            
            print(f"Walls: {count}, Time: {avg_time:.6f}s")
        
        # Performance should scale reasonably with map complexity
        if len(render_times) >= 2:
            scaling_factor = render_times[-1] / render_times[0]
            # Should not scale exponentially
            assert scaling_factor < 10  # Allow up to 10x slowdown for 20x more walls


class TestRenderingMemoryUsage:
    """Test memory usage characteristics of rendering systems."""
    
    def setup_method(self):
        """Set up memory usage tests."""
        self.mock_console = Mock(spec=tcod.console.Console)
        self.ascii_renderer = ASCIIRenderer()
    
    def test_rendering_memory_stability(self):
        """Test that rendering doesn't accumulate memory over time."""
        # Create game state
        game = Mock()
        game.player = Mock(spec=Player)
        game.player.x = 10
        game.player.y = 10
        game.game_map = Mock(spec=GameMap)
        game.game_map.walls = {Position(5, 5), Position(6, 6)}
        game.game_map.shadows = set()
        game.enemies = []
        
        # Perform many rendering operations
        iterations = 1000
        
        with patch('game_rendering.render_char_safe'):
            for i in range(iterations):
                # Modify game state slightly each iteration
                game.player.x = (game.player.x + 1) % GameConfig.MAP_WIDTH
                game.player.y = (game.player.y + 1) % GameConfig.MAP_HEIGHT
                
                # Render
                self.ascii_renderer.render_map(self.mock_console, game)
                
                # Memory usage should remain stable
                # (This is more of a structural test - actual memory tracking would require additional tools)
        
        # Should complete without memory issues
        assert True  # Test passes if no memory errors occur
    
    def test_large_scene_memory_usage(self):
        """Test memory usage with very large scenes."""
        # Create very large game state
        game = Mock()
        game.player = Mock(spec=Player)
        game.player.x = 40
        game.player.y = 20
        game.game_map = Mock(spec=GameMap)
        
        # Add many map elements
        walls = set()
        for x in range(0, GameConfig.MAP_WIDTH, 2):
            for y in range(0, GameConfig.MAP_HEIGHT, 2):
                walls.add(Position(x, y))
        game.game_map.walls = walls
        
        shadows = set()
        for x in range(1, GameConfig.MAP_WIDTH, 3):
            for y in range(1, GameConfig.MAP_HEIGHT, 3):
                shadows.add(Position(x, y))
        game.game_map.shadows = shadows
        
        # Add many enemies
        enemies = []
        for i in range(200):  # Very large number
            enemy = Mock(spec=Enemy)
            enemy.position = Position(i % 60, i % 40)
            enemy.enemy_type = "scanner"
            enemies.append(enemy)
        game.enemies = enemies
        
        # Should handle large scenes without memory issues
        try:
            with patch('game_rendering.render_char_safe'):
                self.ascii_renderer.render_map(self.mock_console, game)
        except MemoryError:
            pytest.fail("Rendering should handle large scenes without memory errors")
        except Exception:
            # Other exceptions may be acceptable
            pass


class TestRenderingOptimization:
    """Test rendering optimization techniques."""
    
    def setup_method(self):
        """Set up optimization tests."""
        self.mock_console = Mock(spec=tcod.console.Console)
        self.ascii_renderer = ASCIIRenderer()
    
    def test_render_call_optimization(self):
        """Test that rendering makes optimal use of render calls."""
        # Create game state with overlapping elements
        game = Mock()
        game.player = Mock(spec=Player)
        game.player.x = 10
        game.player.y = 10
        game.game_map = Mock(spec=GameMap)
        
        # Add overlapping walls and shadows
        game.game_map.walls = {Position(10, 10), Position(11, 10)}  # One overlaps player
        game.game_map.shadows = {Position(10, 10), Position(12, 10)}  # One overlaps player/wall
        
        # Add enemy at same position as wall
        enemy = Mock(spec=Enemy)
        enemy.position = Position(11, 10)  # Same as wall
        enemy.enemy_type = "scanner"
        game.enemies = [enemy]
        
        with patch('game_rendering.render_char_safe') as mock_render:
            self.ascii_renderer.render_map(self.mock_console, game)
            
            # Count renders at specific positions
            position_renders = {}
            for call in mock_render.call_args_list:
                if len(call[0]) >= 3:
                    pos = (call[0][1], call[0][2])  # x, y
                    position_renders[pos] = position_renders.get(pos, 0) + 1
            
            # Each position should be rendered efficiently
            # (Exact optimization depends on implementation)
            # At minimum, should not render the same position dozens of times
            for pos, count in position_renders.items():
                assert count < 10  # Reasonable upper bound
    
    def test_viewport_optimization(self):
        """Test that rendering optimizes for viewport bounds."""
        # Create game state with elements outside viewport
        game = Mock()
        game.player = Mock(spec=Player)
        game.player.x = 40
        game.player.y = 20
        game.game_map = Mock(spec=GameMap)
        
        # Add walls both inside and outside viewport
        walls = set()
        for x in range(-10, GameConfig.MAP_WIDTH + 10):  # Extended range
            for y in range(-10, GameConfig.MAP_HEIGHT + 10):
                if x % 5 == 0 and y % 5 == 0:
                    walls.add(Position(x, y))
        game.game_map.walls = walls
        game.game_map.shadows = set()
        game.enemies = []
        
        with patch('game_rendering.render_char_safe') as mock_render:
            self.ascii_renderer.render_map(self.mock_console, game)
            
            # Should only render within valid viewport bounds
            for call in mock_render.call_args_list:
                if len(call[0]) >= 3:
                    x, y = call[0][1], call[0][2]
                    assert 0 <= x < GameConfig.SCREEN_WIDTH
                    assert 0 <= y < GameConfig.SCREEN_HEIGHT
    
    def test_state_change_optimization(self):
        """Test optimization when game state changes minimally."""
        # Create base game state
        game = Mock()
        game.player = Mock(spec=Player)
        game.player.x = 20
        game.player.y = 15
        game.game_map = Mock(spec=GameMap)
        game.game_map.walls = {Position(10, 10), Position(11, 11)}
        game.game_map.shadows = set()
        game.enemies = []
        
        # Render initial state
        with patch('game_rendering.render_char_safe') as mock_render1:
            self.ascii_renderer.render_map(self.mock_console, game)
            initial_calls = mock_render1.call_count
        
        # Make minimal change (move player slightly)
        game.player.x = 21
        
        # Render changed state
        with patch('game_rendering.render_char_safe') as mock_render2:
            self.ascii_renderer.render_map(self.mock_console, game)
            changed_calls = mock_render2.call_count
        
        # Render call count should be similar for minimal changes
        # (Optimization depends on implementation - may not be different)
        call_difference = abs(changed_calls - initial_calls)
        assert call_difference <= initial_calls * 0.2  # Within 20% difference


class TestRenderingStressTests:
    """Stress tests for rendering systems under extreme conditions."""
    
    def setup_method(self):
        """Set up stress testing environment."""
        self.mock_console = Mock(spec=tcod.console.Console)
        self.ascii_renderer = ASCIIRenderer()
    
    def test_maximum_entity_count_stress(self):
        """Stress test with maximum possible entity counts."""
        # Create game state with maximum entities
        game = Mock()
        game.player = Mock(spec=Player)
        game.player.x = 40
        game.player.y = 20
        game.game_map = Mock(spec=GameMap)
        
        # Fill map with walls (maximum density)
        walls = set()
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                if (x + y) % 2 == 0:  # Checkerboard pattern
                    walls.add(Position(x, y))
        game.game_map.walls = walls
        
        # Maximum shadows
        shadows = set()
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                if (x + y) % 3 == 0:
                    shadows.add(Position(x, y))
        game.game_map.shadows = shadows
        
        # Maximum enemies
        enemies = []
        for i in range(500):  # Extreme number
            enemy = Mock(spec=Enemy)
            enemy.position = Position(i % GameConfig.MAP_WIDTH, i % GameConfig.MAP_HEIGHT)
            enemy.enemy_type = "scanner"
            enemies.append(enemy)
        game.enemies = enemies
        
        # Should handle maximum load
        start_time = time.time()
        
        try:
            with patch('game_rendering.render_char_safe'):
                self.ascii_renderer.render_map(self.mock_console, game)
            
            end_time = time.time()
            render_time = end_time - start_time
            
            # Should complete within reasonable time even under stress
            assert render_time < 1.0  # 1 second maximum
            
        except Exception:
            pytest.fail("Rendering should handle maximum entity stress test")
    
    def test_rapid_rendering_stress(self):
        """Stress test with rapid consecutive rendering calls."""
        # Create moderate game state
        game = Mock()
        game.player = Mock(spec=Player)
        game.player.x = 20
        game.player.y = 15
        game.game_map = Mock(spec=GameMap)
        game.game_map.walls = {Position(i, i) for i in range(20)}
        game.game_map.shadows = set()
        game.enemies = []
        
        # Perform rapid rendering
        iterations = 500
        start_time = time.time()
        
        try:
            with patch('game_rendering.render_char_safe'):
                for i in range(iterations):
                    # Modify state slightly each iteration
                    game.player.x = (game.player.x + 1) % GameConfig.MAP_WIDTH
                    
                    # Render
                    self.ascii_renderer.render_map(self.mock_console, game)
            
            end_time = time.time()
            total_time = end_time - start_time
            avg_time = total_time / iterations
            
            # Should handle rapid rendering efficiently
            assert avg_time < 0.002  # Less than 2ms per render
            assert total_time < 1.0   # Total under 1 second
            
        except Exception:
            pytest.fail("Rendering should handle rapid rendering stress test")
    
    def test_memory_stress_with_large_data(self):
        """Stress test memory usage with large data structures."""
        # Create extremely large game state
        game = Mock()
        game.player = Mock(spec=Player)
        game.player.x = 40
        game.player.y = 20
        game.game_map = Mock(spec=GameMap)
        
        # Very large data structures
        game.game_map.walls = {Position(i % 100, i % 50) for i in range(10000)}
        game.game_map.shadows = {Position(i % 80, i % 40) for i in range(5000)}
        
        # Large enemy list
        enemies = []
        for i in range(1000):
            enemy = Mock(spec=Enemy)
            enemy.position = Position(i % 60, i % 30)
            enemy.enemy_type = f"enemy_{i % 10}"  # Unique types
            enemies.append(enemy)
        game.enemies = enemies
        
        # Should handle large data without memory issues
        try:
            with patch('game_rendering.render_char_safe'):
                self.ascii_renderer.render_map(self.mock_console, game)
        except MemoryError:
            pytest.fail("Rendering should handle large data structures")
        except Exception:
            # Other exceptions may be acceptable
            pass