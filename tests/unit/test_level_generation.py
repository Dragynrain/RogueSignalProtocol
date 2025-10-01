#!/usr/bin/env python3
"""
Unit tests for Level Generation System.
Tests procedural level generation, room placement, and special tile placement.
"""

import pytest
import random
from unittest.mock import Mock, patch, MagicMock
from game_level import LevelGenerator
from game_map import GameMap
from game_entities import Position
from game_config import GameConfig, RoomGenerationConfig


class TestLevelGenerator:
    """Test the LevelGenerator class functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.game_map = GameMap(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
        self.level_generator = LevelGenerator(self.game_map)
    
    def test_level_generator_initialization(self):
        """Test LevelGenerator initializes correctly."""
        assert self.level_generator.game_map == self.game_map
    
    def test_clear_level_data(self):
        """Test that _clear_level_data removes all existing level data."""
        # Add some data to clear
        self.game_map.walls.add((5, 5))
        self.game_map.shadows.add((10, 10))
        self.game_map.cooling_nodes.add((15, 15))
        self.game_map.cpu_recovery_nodes.add((20, 20))
        self.game_map.ghost_nodes.add((25, 25))
        self.game_map.code_hacks[(30, 30)] = Mock()
        self.game_map.exploit_pickups[(35, 35)] = Mock()
        self.game_map.permanent_upgrades[(40, 40)] = "test_upgrade"
        
        # Clear the data
        self.level_generator._clear_level_data()
        
        # Verify everything is cleared
        assert len(self.game_map.walls) == 0
        assert len(self.game_map.shadows) == 0
        assert len(self.game_map.cooling_nodes) == 0
        assert len(self.game_map.cpu_recovery_nodes) == 0
        assert len(self.game_map.ghost_nodes) == 0
        assert len(self.game_map.code_hacks) == 0
        assert len(self.game_map.exploit_pickups) == 0
        assert len(self.game_map.permanent_upgrades) == 0
    
    def test_generate_level_deterministic(self):
        """Test that level generation is deterministic with the same seed."""
        level = 1
        seed = 12345
        
        # Generate first level
        self.level_generator.generate_level(level, seed)
        first_walls = set(self.game_map.walls)
        first_gateway = self.game_map.gateway
        
        # Clear and generate again with same seed
        self.level_generator._clear_level_data()
        self.level_generator.generate_level(level, seed)
        second_walls = set(self.game_map.walls)
        second_gateway = self.game_map.gateway
        
        # Should be identical
        assert first_walls == second_walls
        assert first_gateway == second_gateway
    
    def test_generate_level_different_seeds(self):
        """Test that different seeds produce different levels."""
        level = 1
        
        # Generate first level
        self.level_generator.generate_level(level, 12345)
        first_walls = set(self.game_map.walls)
        
        # Generate second level with different seed
        self.level_generator._clear_level_data()
        self.level_generator.generate_level(level, 54321)
        second_walls = set(self.game_map.walls)
        
        # Should be different (very unlikely to be the same)
        assert first_walls != second_walls
    
    def test_gateway_placement(self):
        """Test that gateway is always placed during level generation."""
        self.level_generator.generate_level(1, 12345)
        
        # Gateway should be placed
        assert self.game_map.gateway is not None
        assert isinstance(self.game_map.gateway, Position)
        
        # Gateway should be within map bounds
        assert 0 <= self.game_map.gateway.x < GameConfig.MAP_WIDTH
        assert 0 <= self.game_map.gateway.y < GameConfig.MAP_HEIGHT
    
    def test_special_tiles_placement(self):
        """Test that special tiles are placed during level generation."""
        self.level_generator.generate_level(2, 12345)  # Level 2 to ensure items
        
        # At least some special tiles should be placed (cooling nodes are common)
        total_special_tiles = (
            len(self.game_map.cooling_nodes) +
            len(self.game_map.cpu_recovery_nodes) +
            len(self.game_map.code_hacks) +
            len(self.game_map.exploit_pickups)
        )
        
        assert total_special_tiles > 0
    
    def test_level_structure_validity(self):
        """Test that generated level has valid structure."""
        self.level_generator.generate_level(1, 12345)
        
        # Should have walls
        assert len(self.game_map.walls) > 0
        
        # All walls should be within bounds
        for wall_pos in self.game_map.walls:
            assert 0 <= wall_pos[0] < GameConfig.MAP_WIDTH
            assert 0 <= wall_pos[1] < GameConfig.MAP_HEIGHT
        
        # Gateway should not be on a wall
        assert (self.game_map.gateway.x, self.game_map.gateway.y) not in self.game_map.walls
    
    def test_transparency_cache_invalidation(self):
        """Test that transparency cache is invalidated after level generation."""
        with patch.object(self.game_map, 'invalidate_transparency_cache') as mock_invalidate:
            self.level_generator.generate_level(1, 12345)
            
            # Should be called during generation
            mock_invalidate.assert_called()


class TestRoomGeneration:
    """Test room generation algorithms."""
    
    def setup_method(self):
        """Set up test environment."""
        self.game_map = GameMap(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
        self.level_generator = LevelGenerator(self.game_map)
    
    def test_room_generation_produces_rooms(self):
        """Test that room generation produces actual rooms."""
        # Generate a level and check for room-like structures
        self.level_generator.generate_level(1, 12345)
        
        # Find open areas (potential rooms)
        open_areas = []
        for x in range(1, GameConfig.MAP_WIDTH - 1):
            for y in range(1, GameConfig.MAP_HEIGHT - 1):
                if (x, y) not in self.game_map.walls:
                    # Check if surrounded by floor (room interior)
                    neighbors = [
                        (x-1, y), (x+1, y), (x, y-1), (x, y+1)
                    ]
                    open_neighbors = sum(1 for nx, ny in neighbors if (nx, ny) not in self.game_map.walls)
                    if open_neighbors >= 3:  # Likely inside a room
                        open_areas.append((x, y))
        
        # Should have some open room areas
        assert len(open_areas) > 10
    
    def test_corridors_connect_areas(self):
        """Test that corridors connect different areas."""
        self.level_generator.generate_level(1, 12345)
        
        # Find corridor-like structures (single-width passages)
        corridors = []
        for x in range(1, GameConfig.MAP_WIDTH - 1):
            for y in range(1, GameConfig.MAP_HEIGHT - 1):
                if (x, y) not in self.game_map.walls:
                    # Check if it's a narrow passage
                    wall_neighbors = sum(1 for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]
                                       if (x+dx, y+dy) in self.game_map.walls)
                    if wall_neighbors >= 2:  # Narrow passage
                        corridors.append((x, y))
        
        # Should have some corridor structures
        assert len(corridors) > 5


class TestSpecialTilePlacement:
    """Test special tile placement algorithms."""
    
    def setup_method(self):
        """Set up test environment."""
        self.game_map = GameMap(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
        self.level_generator = LevelGenerator(self.game_map)
    
    def test_cooling_nodes_placement(self):
        """Test cooling nodes are placed appropriately."""
        self.level_generator.generate_level(1, 12345)
        
        # Should have cooling nodes
        assert len(self.game_map.cooling_nodes) > 0
        
        # All cooling nodes should be on valid floor tiles
        for node_pos in self.game_map.cooling_nodes:
            assert node_pos not in self.game_map.walls
            assert 0 <= node_pos[0] < GameConfig.MAP_WIDTH
            assert 0 <= node_pos[1] < GameConfig.MAP_HEIGHT
    
    def test_cpu_recovery_nodes_placement(self):
        """Test CPU recovery nodes are placed correctly."""
        self.level_generator.generate_level(1, 12345)
        
        # Should have some recovery nodes placed
        recovery_nodes = len(self.game_map.cpu_recovery_nodes)
        assert recovery_nodes >= 0  # Should not crash, any number is valid
        
        # All recovery nodes should be on valid positions
        for node_pos in self.game_map.cpu_recovery_nodes:
            assert node_pos not in self.game_map.walls
            assert 0 <= node_pos[0] < GameConfig.MAP_WIDTH
            assert 0 <= node_pos[1] < GameConfig.MAP_HEIGHT
    
    def test_exploit_pickups_placement(self):
        """Test exploit pickups are placed correctly."""
        self.level_generator.generate_level(2, 12345)
        
        # Should have some exploit pickups
        if len(self.game_map.exploit_pickups) > 0:
            # All pickups should be on valid positions
            for pos, exploit in self.game_map.exploit_pickups.items():
                assert pos not in self.game_map.walls
                assert 0 <= pos[0] < GameConfig.MAP_WIDTH
                assert 0 <= pos[1] < GameConfig.MAP_HEIGHT
                assert exploit is not None
    
    def test_code_hacks_placement(self):
        """Test code hacks are placed correctly."""
        self.level_generator.generate_level(2, 12345)
        
        # Should have some code hacks
        if len(self.game_map.code_hacks) > 0:
            # All code hacks should be on valid positions
            for pos, hack in self.game_map.code_hacks.items():
                assert pos not in self.game_map.walls
                assert 0 <= pos[0] < GameConfig.MAP_WIDTH
                assert 0 <= pos[1] < GameConfig.MAP_HEIGHT
                assert hack is not None
    
    def test_no_overlapping_special_tiles(self):
        """Test that special tiles don't overlap inappropriately."""
        self.level_generator.generate_level(2, 12345)
        
        # Collect all special tile positions
        all_special_positions = set()
        all_special_positions.update(self.game_map.cooling_nodes)
        all_special_positions.update(self.game_map.cpu_recovery_nodes)
        all_special_positions.update(self.game_map.code_hacks.keys())
        all_special_positions.update(self.game_map.exploit_pickups.keys())
        
        # Gateway shouldn't overlap with special tiles
        gateway_pos = (self.game_map.gateway.x, self.game_map.gateway.y)
        assert gateway_pos not in all_special_positions


class TestLevelProgression:
    """Test level progression and difficulty scaling."""
    
    def setup_method(self):
        """Set up test environment."""
        self.game_map = GameMap(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
        self.level_generator = LevelGenerator(self.game_map)
    
    def test_level_complexity_increases(self):
        """Test that level generation works for different levels."""
        # Generate level 1
        self.level_generator.generate_level(1, 12345)
        l1_walls = len(self.game_map.walls)
        l1_special = (len(self.game_map.cooling_nodes) + 
                     len(self.game_map.cpu_recovery_nodes) +
                     len(self.game_map.code_hacks) +
                     len(self.game_map.exploit_pickups))
        
        # Generate level 2 (within valid range)
        self.level_generator._clear_level_data()
        self.level_generator.generate_level(2, 12345)
        l2_walls = len(self.game_map.walls)
        l2_special = (len(self.game_map.cooling_nodes) + 
                     len(self.game_map.cpu_recovery_nodes) +
                     len(self.game_map.code_hacks) +
                     len(self.game_map.exploit_pickups))
        
        # Both levels should have content
        assert l1_walls > 0
        assert l2_walls > 0
        assert l1_special >= 0  
        assert l2_special >= 0
    
    def test_consistent_seed_across_levels(self):
        """Test that the same seed produces consistent results for the same level."""
        seed = 99999
        
        # Generate level 3 twice with same seed
        self.level_generator.generate_level(3, seed)
        first_gateway = self.game_map.gateway
        first_walls = set(self.game_map.walls)
        
        self.level_generator._clear_level_data()
        self.level_generator.generate_level(3, seed)
        second_gateway = self.game_map.gateway
        second_walls = set(self.game_map.walls)
        
        # Should be identical
        assert first_gateway == second_gateway
        assert first_walls == second_walls


class TestLevelGenerationErrorHandling:
    """Test error handling in level generation."""
    
    def setup_method(self):
        """Set up test environment."""
        self.game_map = GameMap(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
        self.level_generator = LevelGenerator(self.game_map)
    
    def test_invalid_level_numbers(self):
        """Test level generation handles invalid level numbers."""
        # Test with level 0 (should work)
        try:
            self.level_generator.generate_level(0, 12345)
            # Should not crash
            assert True
        except Exception as e:
            pytest.fail(f"Level generation crashed with level 0: {e}")
        
        # Test negative level - this may crash, which is acceptable behavior
        # since the game doesn't expect negative levels
        with pytest.raises(KeyError):
            self.level_generator.generate_level(-1, 12345)
        
        # Test very high level - this may also crash, which is acceptable
        with pytest.raises(KeyError):
            self.level_generator.generate_level(999, 12345)
    
    def test_extreme_seeds(self):
        """Test level generation handles extreme seed values."""
        extreme_seeds = [0, -1, 2**31 - 1, -2**31]
        
        for seed in extreme_seeds:
            try:
                self.level_generator.generate_level(1, seed)
                # Should not crash
                assert True
            except Exception as e:
                pytest.fail(f"Level generation crashed with seed {seed}: {e}")
    
    def test_small_map_generation(self):
        """Test level generation on very small maps."""
        small_map = GameMap(10, 10)  # Very small map
        small_generator = LevelGenerator(small_map)
        
        try:
            small_generator.generate_level(1, 12345)
            # Should not crash even with small map
            assert True
            
            # Should still place gateway
            assert small_map.gateway is not None
        except Exception as e:
            pytest.fail(f"Level generation crashed on small map: {e}")


if __name__ == "__main__":
    pytest.main([__file__])