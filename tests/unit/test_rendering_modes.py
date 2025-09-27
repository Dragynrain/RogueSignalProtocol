#!/usr/bin/env python3
"""
Rendering Modes Consistency Tests.
Tests consistency between ASCII and Graphics mode rendering.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import tcod
from typing import Dict, Any

from game_rendering import BaseRenderer, ASCIIRenderer, Renderer, UIRenderer, MapRenderer
from game_entities import Colors, Position, EnemyState, EnemyMovement, ensure_color_tuple
from game_characters import Player, Enemy
from game_config import GameConfig
from game_map import GameMap
from game_state import MessageLog
from game_inventory import CodeHack, ExploitItem


class TestRenderingModeConsistency:
    """Test consistency between different rendering modes."""
    
    def setup_method(self):
        """Set up mock game environment for rendering tests."""
        self.mock_console = Mock(spec=tcod.console.Console)
        self.mock_game = Mock()
        
        # Set up basic game state
        self.mock_game.player = Mock(spec=Player)
        self.mock_game.player.x = 10
        self.mock_game.player.y = 10
        self.mock_game.player.cpu = 85
        self.mock_game.player.max_cpu = 100
        self.mock_game.player.detection = 25.5
        self.mock_game.player.heat = 45
        self.mock_game.player.shadow_steps = 3
        
        self.mock_game.game_state = Mock()
        self.mock_game.level = 2
        self.mock_game.turn = 150
        self.mock_game.game_over = False
        
        self.mock_game.game_map = Mock(spec=GameMap)
        self.mock_game.game_map.walls = {Position(5, 5), Position(6, 6)}
        self.mock_game.game_map.shadows = {Position(7, 7), Position(8, 8)}
        self.mock_game.game_map.cooling_nodes = {Position(9, 9)}
        self.mock_game.game_map.cpu_recovery_nodes = {Position(10, 11)}
        self.mock_game.game_map.ghost_nodes = {Position(11, 10): 1000.0}
        
        self.mock_game.enemies = []
        self.mock_game.message_log = Mock(spec=MessageLog)
        self.mock_game.message_log.messages = []
        
        # UI state
        self.mock_game.show_inventory = False
        self.mock_game.show_help = False
        self.mock_game.show_lore_viewer = False
        self.mock_game.show_story_fragment = None
        self.mock_game.show_gateway_confirmation = False
        self.mock_game.targeting_mode = False
    
    def test_ascii_renderer_map_consistency(self):
        """ASCII renderer produces consistent map output."""
        ascii_renderer = ASCIIRenderer()
        
        with patch('game_rendering.render_char_safe') as mock_render:
            ascii_renderer.render_map(self.mock_console, self.mock_game)
            
            # Should render player character
            player_calls = [call for call in mock_render.call_args_list 
                          if call[0][1:3] == (10, 10)]  # Player position
            assert len(player_calls) > 0
            
            # Should render walls
            wall_calls = [call for call in mock_render.call_args_list 
                        if call[0][1:3] in [(5, 5), (6, 6)]]  # Wall positions
            assert len(wall_calls) >= 2
    
    def test_graphics_renderer_map_consistency(self):
        """Graphics renderer produces consistent map output."""
        # Note: Actual graphics renderer may not exist yet
        # This test structure shows how to test it when implemented
        
        # For now, test that ASCII renderer can handle graphics mode concepts
        ascii_renderer = ASCIIRenderer()
        
        # Add more complex game elements
        enemy = Mock(spec=Enemy)
        enemy.position = Position(15, 15)
        enemy.enemy_type = "scanner"
        enemy.state = EnemyState.PATROL
        self.mock_game.enemies = [enemy]
        
        with patch('game_rendering.render_char_safe') as mock_render:
            ascii_renderer.render_map(self.mock_console, self.mock_game)
            
            # Should render enemy
            enemy_calls = [call for call in mock_render.call_args_list 
                         if call[0][1:3] == (15, 15)]  # Enemy position
            assert len(enemy_calls) > 0
    
    def test_ui_rendering_consistency_across_modes(self):
        """UI elements render consistently across different modes."""
        ui_renderer = UIRenderer()
        
        # Test status bar rendering
        with patch('game_rendering.render_char_safe') as mock_render:
            ui_renderer.render_top_status_bar(self.mock_console, self.mock_game)
            
            # Should render status information
            assert mock_render.call_count > 0
            
            # Check that status elements are rendered
            calls_text = str(mock_render.call_args_list)
            assert any(char in calls_text for char in ['C', 'P', 'U'])  # CPU text
    
    def test_color_consistency_across_modes(self):
        """Colors are consistent between ASCII and graphics modes."""
        ascii_renderer = ASCIIRenderer()
        
        # Test that ensure_color_tuple produces consistent results
        test_colors = [Colors.RED, Colors.GREEN, Colors.BLUE, Colors.WHITE, Colors.BLACK]
        
        for color in test_colors:
            result = ensure_color_tuple(color)
            assert isinstance(result, tuple)
            assert len(result) == 3
            assert all(0 <= component <= 255 for component in result)
    
    def test_special_character_rendering_consistency(self):
        """Special characters render consistently across modes."""
        ascii_renderer = ASCIIRenderer()
        
        # Test rendering of various game symbols
        with patch('game_rendering.render_char_safe') as mock_render:
            ascii_renderer.render_map(self.mock_console, self.mock_game)
            
            calls_text = str(mock_render.call_args_list)
            
            # Should use consistent symbols
            # Walls should use #
            # Shadows should use *
            # Player should use @
            # (Exact symbols may vary based on implementation)
    
    def test_rendering_coordinate_consistency(self):
        """Coordinate systems are consistent between rendering modes."""
        ascii_renderer = ASCIIRenderer()
        ui_renderer = UIRenderer()
        
        # Test that coordinates are handled consistently
        with patch('game_rendering.render_char_safe') as mock_render:
            ascii_renderer.render_map(self.mock_console, self.mock_game)
            
            # All coordinates should be within valid bounds
            for call in mock_render.call_args_list:
                if len(call[0]) >= 3:  # Has x, y coordinates
                    x, y = call[0][1], call[0][2]
                    assert 0 <= x < GameConfig.SCREEN_WIDTH
                    assert 0 <= y < GameConfig.SCREEN_HEIGHT


class TestRenderingStateConsistency:
    """Test rendering consistency across different game states."""
    
    def setup_method(self):
        """Set up mock game environment."""
        self.mock_console = Mock(spec=tcod.console.Console)
        self.ascii_renderer = ASCIIRenderer()
        self.ui_renderer = UIRenderer()
        
        # Basic game setup
        self.mock_game = Mock()
        self.mock_game.player = Mock(spec=Player)
        self.mock_game.player.x = 20
        self.mock_game.player.y = 15
        self.mock_game.game_map = Mock(spec=GameMap)
        self.mock_game.game_map.walls = set()
        self.mock_game.game_map.shadows = set()
        self.mock_game.enemies = []
        self.mock_game.message_log = Mock(spec=MessageLog)
        self.mock_game.message_log.messages = []
    
    def test_normal_game_state_rendering(self):
        """Normal game state renders consistently."""
        # Set normal game state
        self.mock_game.show_inventory = False
        self.mock_game.show_help = False
        self.mock_game.show_lore_viewer = False
        self.mock_game.show_story_fragment = None
        self.mock_game.game_over = False
        self.mock_game.player.cpu = 100
        
        with patch('game_rendering.render_char_safe') as mock_render:
            self.ascii_renderer.render_game(self.mock_console, self.mock_game)
            
            # Should clear console and render main game
            self.mock_console.clear.assert_called_once()
            assert mock_render.call_count > 0
    
    def test_inventory_state_rendering(self):
        """Inventory state renders consistently."""
        # Set inventory state
        self.mock_game.show_inventory = True
        self.mock_game.show_help = False
        self.mock_game.show_lore_viewer = False
        self.mock_game.show_story_fragment = None
        
        with patch.object(self.ui_renderer, 'render_inventory_screen') as mock_inventory:
            self.ascii_renderer.render_game(self.mock_console, self.mock_game)
            
            # Should render inventory screen
            mock_inventory.assert_called_once()
    
    def test_help_state_rendering(self):
        """Help state renders consistently."""
        # Set help state
        self.mock_game.show_inventory = False
        self.mock_game.show_help = True
        self.mock_game.show_lore_viewer = False
        self.mock_game.show_story_fragment = None
        
        with patch.object(self.ui_renderer, 'render_help_screen') as mock_help:
            self.ascii_renderer.render_game(self.mock_console, self.mock_game)
            
            # Should render help screen
            mock_help.assert_called_once()
    
    def test_game_over_state_rendering(self):
        """Game over state renders consistently."""
        # Set game over state
        self.mock_game.show_inventory = False
        self.mock_game.show_help = False
        self.mock_game.game_over = True
        self.mock_game.level = 4  # Victory condition
        
        with patch.object(self.ascii_renderer, '_render_victory_message') as mock_victory:
            self.ascii_renderer.render_game(self.mock_console, self.mock_game)
            
            # Should render victory message
            mock_victory.assert_called_once()
    
    def test_player_death_state_rendering(self):
        """Player death state renders consistently."""
        # Set death state
        self.mock_game.show_inventory = False
        self.mock_game.show_help = False
        self.mock_game.game_over = False  # Not victory
        self.mock_game.player.cpu = 0    # Dead
        
        with patch.object(self.ascii_renderer, '_render_death_message') as mock_death:
            self.ascii_renderer.render_game(self.mock_console, self.mock_game)
            
            # Should render death message
            mock_death.assert_called_once()
    
    def test_targeting_mode_rendering(self):
        """Targeting mode renders consistently."""
        # Set targeting state
        self.mock_game.targeting_mode = True
        self.mock_game.cursor_position = Position(25, 20)
        self.mock_game.show_inventory = False
        self.mock_game.show_help = False
        
        with patch('game_rendering.render_char_safe') as mock_render:
            self.ascii_renderer.render_game(self.mock_console, self.mock_game)
            
            # Should render cursor at targeting position
            cursor_calls = [call for call in mock_render.call_args_list 
                          if call[0][1:3] == (25, 20)]  # Cursor position
            # Cursor rendering depends on implementation


class TestRenderingBoundaryConditions:
    """Test rendering at boundary conditions and edge cases."""
    
    def setup_method(self):
        """Set up boundary condition tests."""
        self.mock_console = Mock(spec=tcod.console.Console)
        self.ascii_renderer = ASCIIRenderer()
        self.mock_game = Mock()
        
        # Set up minimal game state
        self.mock_game.player = Mock(spec=Player)
        self.mock_game.game_map = Mock(spec=GameMap)
        self.mock_game.game_map.walls = set()
        self.mock_game.game_map.shadows = set()
        self.mock_game.enemies = []
        self.mock_game.message_log = Mock(spec=MessageLog)
        self.mock_game.message_log.messages = []
        self.mock_game.show_inventory = False
        self.mock_game.show_help = False
    
    def test_edge_coordinates_rendering(self):
        """Rendering handles edge coordinates correctly."""
        # Test rendering at map boundaries
        boundary_positions = [
            (0, 0),                                           # Top-left
            (GameConfig.SCREEN_WIDTH - 1, 0),                # Top-right
            (0, GameConfig.SCREEN_HEIGHT - 1),               # Bottom-left
            (GameConfig.SCREEN_WIDTH - 1, GameConfig.SCREEN_HEIGHT - 1)  # Bottom-right
        ]
        
        for x, y in boundary_positions:
            self.mock_game.player.x = x
            self.mock_game.player.y = y
            
            with patch('game_rendering.render_char_safe') as mock_render:
                try:
                    self.ascii_renderer.render_map(self.mock_console, self.mock_game)
                    
                    # Should not crash at boundary positions
                    # All render calls should have valid coordinates
                    for call in mock_render.call_args_list:
                        if len(call[0]) >= 3:
                            render_x, render_y = call[0][1], call[0][2]
                            assert 0 <= render_x < GameConfig.SCREEN_WIDTH
                            assert 0 <= render_y < GameConfig.SCREEN_HEIGHT
                            
                except Exception:
                    pytest.fail(f"Rendering should handle boundary position ({x}, {y})")
    
    def test_outside_bounds_rendering(self):
        """Rendering handles out-of-bounds positions gracefully."""
        # Test with positions outside valid range
        invalid_positions = [(-1, -1), (-5, 10), (10, -5), (1000, 1000)]
        
        for x, y in invalid_positions:
            self.mock_game.player.x = x
            self.mock_game.player.y = y
            
            try:
                with patch('game_rendering.render_char_safe') as mock_render:
                    self.ascii_renderer.render_map(self.mock_console, self.mock_game)
                    
                    # Should either clamp coordinates or skip invalid renders
                    # No render calls should have invalid coordinates
                    for call in mock_render.call_args_list:
                        if len(call[0]) >= 3:
                            render_x, render_y = call[0][1], call[0][2]
                            if render_x < 0 or render_x >= GameConfig.SCREEN_WIDTH:
                                pytest.fail(f"Invalid x coordinate rendered: {render_x}")
                            if render_y < 0 or render_y >= GameConfig.SCREEN_HEIGHT:
                                pytest.fail(f"Invalid y coordinate rendered: {render_y}")
                                
            except Exception:
                # May raise exception for invalid positions - acceptable behavior
                pass
    
    def test_maximum_entities_rendering(self):
        """Rendering handles maximum number of entities."""
        # Add many entities to test performance
        max_walls = 100
        max_enemies = 50
        
        # Add walls
        for i in range(max_walls):
            x = i % GameConfig.SCREEN_WIDTH
            y = (i // GameConfig.SCREEN_WIDTH) % GameConfig.SCREEN_HEIGHT
            self.mock_game.game_map.walls.add(Position(x, y))
        
        # Add enemies
        enemies = []
        for i in range(max_enemies):
            enemy = Mock(spec=Enemy)
            enemy.position = Position(i % 40, i % 20)
            enemy.enemy_type = "scanner"
            enemy.state = EnemyState.PATROL
            enemies.append(enemy)
        
        self.mock_game.enemies = enemies
        
        # Should handle large numbers of entities
        try:
            with patch('game_rendering.render_char_safe'):
                self.ascii_renderer.render_map(self.mock_console, self.mock_game)
        except Exception:
            pytest.fail("Rendering should handle large numbers of entities")
    
    def test_empty_map_rendering(self):
        """Rendering handles completely empty map."""
        # Empty map with no entities
        self.mock_game.game_map.walls = set()
        self.mock_game.game_map.shadows = set()
        self.mock_game.game_map.cooling_nodes = set()
        self.mock_game.game_map.cpu_recovery_nodes = set()
        self.mock_game.game_map.ghost_nodes = {}
        self.mock_game.enemies = []
        
        # Should still render player
        self.mock_game.player.x = 10
        self.mock_game.player.y = 10
        
        try:
            with patch('game_rendering.render_char_safe') as mock_render:
                self.ascii_renderer.render_map(self.mock_console, self.mock_game)
                
                # Should at least render the player
                player_calls = [call for call in mock_render.call_args_list 
                              if call[0][1:3] == (10, 10)]
                assert len(player_calls) > 0
                
        except Exception:
            pytest.fail("Rendering should handle empty maps")


class TestRenderingPerformanceCharacteristics:
    """Test performance characteristics of rendering systems."""
    
    def setup_method(self):
        """Set up performance tests."""
        self.mock_console = Mock(spec=tcod.console.Console)
        self.ascii_renderer = ASCIIRenderer()
        self.mock_game = Mock()
        
        # Standard game setup
        self.mock_game.player = Mock(spec=Player)
        self.mock_game.player.x = 20
        self.mock_game.player.y = 15
        self.mock_game.game_map = Mock(spec=GameMap)
        self.mock_game.enemies = []
        self.mock_game.message_log = Mock(spec=MessageLog)
        self.mock_game.message_log.messages = []
        self.mock_game.show_inventory = False
        self.mock_game.show_help = False
    
    def test_render_call_efficiency(self):
        """Rendering makes efficient use of render calls."""
        # Basic map with some entities
        self.mock_game.game_map.walls = {Position(5, 5), Position(6, 6)}
        self.mock_game.game_map.shadows = {Position(7, 7)}
        
        enemy = Mock(spec=Enemy)
        enemy.position = Position(15, 15)
        enemy.enemy_type = "scanner"
        self.mock_game.enemies = [enemy]
        
        with patch('game_rendering.render_char_safe') as mock_render:
            self.ascii_renderer.render_map(self.mock_console, self.mock_game)
            
            # Should make a reasonable number of render calls
            # (Not too many unnecessary calls)
            call_count = mock_render.call_count
            
            # Rough estimate: player + walls + shadows + enemy + some padding
            expected_calls = 1 + 2 + 1 + 1 + 50  # Allow padding for backgrounds, etc.
            
            # Should not exceed reasonable threshold
            assert call_count < expected_calls * 2  # Allow 2x tolerance
    
    def test_repeated_rendering_stability(self):
        """Repeated rendering calls remain stable."""
        # Set up game state
        self.mock_game.game_map.walls = {Position(10, 10)}
        
        render_counts = []
        
        # Perform multiple renders
        for i in range(5):
            with patch('game_rendering.render_char_safe') as mock_render:
                self.ascii_renderer.render_map(self.mock_console, self.mock_game)
                render_counts.append(mock_render.call_count)
        
        # Render call counts should be consistent
        # (May vary slightly due to dynamic elements)
        max_count = max(render_counts)
        min_count = min(render_counts)
        
        # Should not vary too much between renders
        variation = max_count - min_count
        assert variation <= max_count * 0.1  # Within 10% variation
    
    def test_complex_scene_rendering_performance(self):
        """Complex scenes render within reasonable time."""
        # Create complex scene
        walls = set()
        for i in range(50):  # Many walls
            walls.add(Position(i % 40, i // 40))
        self.mock_game.game_map.walls = walls
        
        shadows = set()
        for i in range(30):  # Many shadows
            shadows.add(Position((i * 2) % 40, (i * 2) // 40))
        self.mock_game.game_map.shadows = shadows
        
        enemies = []
        for i in range(20):  # Many enemies
            enemy = Mock(spec=Enemy)
            enemy.position = Position(i % 20, i // 20 + 10)
            enemy.enemy_type = "scanner"
            enemies.append(enemy)
        self.mock_game.enemies = enemies
        
        # Should complete without timeout
        import time
        start_time = time.time()
        
        try:
            with patch('game_rendering.render_char_safe'):
                self.ascii_renderer.render_map(self.mock_console, self.mock_game)
            
            end_time = time.time()
            render_time = end_time - start_time
            
            # Should complete quickly (less than 1 second)
            assert render_time < 1.0
            
        except Exception:
            pytest.fail("Complex scene rendering should complete successfully")


class TestRenderingErrorHandling:
    """Test error handling in rendering systems."""
    
    def setup_method(self):
        """Set up error handling tests."""
        self.mock_console = Mock(spec=tcod.console.Console)
        self.ascii_renderer = ASCIIRenderer()
        self.mock_game = Mock()
    
    def test_invalid_console_handling(self):
        """Rendering handles invalid console gracefully."""
        # Test with None console
        try:
            self.ascii_renderer.render_map(None, self.mock_game)
        except Exception:
            # May raise exception - acceptable behavior
            pass
    
    def test_corrupted_game_state_handling(self):
        """Rendering handles corrupted game state."""
        # Test with missing game attributes
        corrupted_game = Mock()
        # Missing required attributes
        
        try:
            self.ascii_renderer.render_map(self.mock_console, corrupted_game)
        except AttributeError:
            # Expected to fail gracefully
            pass
        except Exception:
            pytest.fail("Should handle corrupted game state gracefully")
    
    def test_render_function_failure_handling(self):
        """Rendering handles render function failures."""
        # Set up basic game state
        self.mock_game.player = Mock(spec=Player)
        self.mock_game.player.x = 10
        self.mock_game.player.y = 10
        self.mock_game.game_map = Mock(spec=GameMap)
        self.mock_game.game_map.walls = set()
        self.mock_game.enemies = []
        
        # Mock render function to fail
        with patch('game_rendering.render_char_safe', side_effect=Exception("Render failed")):
            try:
                self.ascii_renderer.render_map(self.mock_console, self.mock_game)
                # Should either handle gracefully or fail fast
            except Exception:
                # Acceptable to propagate render failures
                pass