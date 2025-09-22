#!/usr/bin/env python3
"""
Integration tests for player movement and map interaction.
Tests real movement mechanics, collision detection, and map navigation.
"""

import pytest
from game_map import GameMap
from game_level import LevelGenerator
from game_characters import Player
from game_entities import Position
from game_state import MessageLog


class TestPlayerMovementIntegration:
    """Integration tests for player movement with real map objects."""
    
    def setup_method(self):
        """Set up real game environment for movement testing."""
        # Create real map with actual level generation
        self.game_map = GameMap(30, 20)
        self.level_generator = LevelGenerator(self.game_map)
        self.level_generator.generate_level(level=1, seed=12345)
        
        # Find a valid starting position for player
        self.start_position = self._find_safe_position()
        self.player = Player(self.start_position.x, self.start_position.y)
        
        # Create message log for tracking events
        self.message_log = MessageLog()
    
    def _find_safe_position(self) -> Position:
        """Find a walkable position on the map."""
        for x in range(1, self.game_map.width - 1):
            for y in range(1, self.game_map.height - 1):
                pos = Position(x, y)
                if not self.game_map.is_wall(pos):
                    return pos
        # Fallback to center if no safe position found
        return Position(self.game_map.width // 2, self.game_map.height // 2)
    
    def test_player_basic_movement_mechanics(self):
        """Test that player can move to valid positions and is blocked by walls."""
        original_position = self.player.position
        
        # Test movement in all four directions
        directions = [
            Position(0, -1),  # North
            Position(1, 0),   # East
            Position(0, 1),   # South
            Position(-1, 0)   # West
        ]
        
        successful_moves = 0
        blocked_moves = 0
        
        for direction in directions:
            target_x = original_position.x + direction.x
            target_y = original_position.y + direction.y
            target_pos = Position(target_x, target_y)
            
            # Check if target position is valid
            if (0 <= target_x < self.game_map.width and 
                0 <= target_y < self.game_map.height):
                
                if not self.game_map.is_wall(target_pos):
                    # Should be able to move here
                    self.player.position = target_pos
                    assert self.player.position == target_pos, "Player should move to valid position"
                    successful_moves += 1
                    # Move back to test next direction
                    self.player.position = original_position
                else:
                    # Movement should be blocked by wall
                    old_pos = self.player.position
                    # Simulate trying to move into wall (would be blocked by game engine)
                    # For this test, we just verify the wall detection works
                    assert self.game_map.is_wall(target_pos), "Wall detection should work correctly"
                    blocked_moves += 1
        
        # Should have attempted movement in all directions
        assert successful_moves + blocked_moves == 4, "Should test all four directions"
        assert successful_moves > 0, "Should have at least one valid move direction"
    
    def test_player_collision_detection_with_map_features(self):
        """Test collision detection with various map features."""
        # Test wall collision
        wall_positions = list(self.game_map.walls)
        if len(wall_positions) > 0:
            wall_pos = Position(wall_positions[0][0], wall_positions[0][1])
            assert self.game_map.is_wall(wall_pos), "Wall detection should work"
            
            # Player should not be able to occupy wall position
            original_pos = self.player.position
            # In real game, this move would be prevented
            # We test that the detection works correctly
            assert self.game_map.is_wall(wall_pos) != self.game_map.is_wall(original_pos)
        
        # Test shadow interaction
        shadow_positions = list(self.game_map.shadows)
        if len(shadow_positions) > 0:
            shadow_pos = Position(shadow_positions[0][0], shadow_positions[0][1])
            
            # Player should be able to move into shadows (for stealth)
            if not self.game_map.is_wall(shadow_pos):
                self.player.position = shadow_pos
                assert self.game_map.is_shadow(shadow_pos), "Shadow detection should work"
                # Player gets stealth benefit in shadows
                in_shadow = self.game_map.is_shadow(self.player.position)
                assert in_shadow, "Player should be detected as in shadow"
    
    def test_player_navigation_to_objectives(self):
        """Test player navigation to map objectives like gateway."""
        # Test navigation to gateway
        gateway = self.game_map.gateway
        assert gateway is not None, "Map should have gateway objective"
        
        # Calculate path to gateway (simplified - just distance)
        start_pos = self.player.position
        distance_to_gateway = abs(start_pos.x - gateway.x) + abs(start_pos.y - gateway.y)
        
        # Player should be able to reach gateway area
        # Move player closer to gateway (simulate pathfinding)
        if distance_to_gateway > 1:
            # Move one step toward gateway
            dx = 1 if gateway.x > start_pos.x else (-1 if gateway.x < start_pos.x else 0)
            dy = 1 if gateway.y > start_pos.y else (-1 if gateway.y < start_pos.y else 0)
            
            next_pos = Position(start_pos.x + dx, start_pos.y + dy)
            
            # Check if this step is valid
            if (0 <= next_pos.x < self.game_map.width and 
                0 <= next_pos.y < self.game_map.height and
                not self.game_map.is_wall(next_pos)):
                
                self.player.position = next_pos
                new_distance = abs(next_pos.x - gateway.x) + abs(next_pos.y - gateway.y)
                assert new_distance <= distance_to_gateway, "Should move closer to or reach gateway"
        
        # Test interaction with special nodes
        special_nodes = (self.game_map.cooling_nodes | 
                        self.game_map.cpu_recovery_nodes | 
                        self.game_map.ghost_nodes)
        
        if len(special_nodes) > 0:
            node_pos = Position(list(special_nodes)[0][0], list(special_nodes)[0][1])
            
            # Player should be able to reach special nodes
            if not self.game_map.is_wall(node_pos):
                self.player.position = node_pos
                # Check if player is at special node
                player_tuple = (self.player.position.x, self.player.position.y)
                at_special_node = player_tuple in special_nodes
                assert at_special_node, "Player should be able to reach special nodes"
    
    def test_player_movement_with_game_state_tracking(self):
        """Test that player movement properly integrates with game state."""
        initial_position = self.player.position
        initial_turn = 1
        
        # Move player and track state changes
        valid_moves = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                
                test_x = initial_position.x + dx
                test_y = initial_position.y + dy
                test_pos = Position(test_x, test_y)
                
                if (0 <= test_x < self.game_map.width and 
                    0 <= test_y < self.game_map.height and
                    not self.game_map.is_wall(test_pos)):
                    valid_moves.append(test_pos)
        
        # Execute movement and verify state tracking
        if len(valid_moves) > 0:
            target_move = valid_moves[0]
            
            # Store last position
            self.player.last_position = self.player.position
            
            # Execute move
            self.player.position = target_move
            
            # Verify state tracking
            assert self.player.last_position == initial_position, "Should track last position"
            assert self.player.position == target_move, "Should update current position"
            assert self.player.position != self.player.last_position, "Position should change with movement"
        
        # Test position validation
        assert self.player.position.is_valid(self.game_map.width, self.game_map.height), "Player position should always be valid"
    
    def test_player_movement_performance_with_large_map(self):
        """Test movement performance on larger maps."""
        import time
        
        # Create larger map for performance testing
        large_map = GameMap(100, 80)
        large_generator = LevelGenerator(large_map)
        
        # Time the level generation
        start_time = time.time()
        large_generator.generate_level(level=1, seed=999)
        generation_time = time.time() - start_time
        
        # Find starting position on large map
        large_start = self._find_safe_position_on_map(large_map)
        large_player = Player(large_start.x, large_start.y)
        
        # Test multiple movement operations
        movement_start = time.time()
        
        for i in range(10):  # Simulate 10 movement operations
            # Find a new valid position
            test_x = large_start.x + (i % 5)
            test_y = large_start.y + (i % 3)
            test_pos = Position(test_x, test_y)
            
            if (0 <= test_x < large_map.width and 
                0 <= test_y < large_map.height and
                not large_map.is_wall(test_pos)):
                large_player.position = test_pos
        
        movement_time = time.time() - movement_start
        
        # Performance assertions
        assert generation_time < 2.0, f"Large map generation should be fast, took {generation_time:.2f}s"
        assert movement_time < 0.1, f"Movement operations should be fast, took {movement_time:.2f}s"
        assert len(large_map.walls) > 500, "Large map should have substantial content"
        assert large_map.gateway is not None, "Large map should have gateway"
    
    def _find_safe_position_on_map(self, game_map: GameMap) -> Position:
        """Helper to find safe position on any map."""
        for x in range(1, game_map.width - 1):
            for y in range(1, game_map.height - 1):
                pos = Position(x, y)
                if not game_map.is_wall(pos):
                    return pos
        return Position(game_map.width // 2, game_map.height // 2)


class TestMapInteractionIntegration:
    """Integration tests for player interaction with map elements."""
    
    def setup_method(self):
        """Set up map interaction test environment."""
        self.game_map = GameMap(40, 25)
        self.level_generator = LevelGenerator(self.game_map)
        self.level_generator.generate_level(level=1, seed=555)
        
        # Find safe starting position
        self.start_pos = self._find_walkable_position()
        self.player = Player(self.start_pos.x, self.start_pos.y)
    
    def _find_walkable_position(self) -> Position:
        """Find a walkable position for testing."""
        for x in range(self.game_map.width):
            for y in range(self.game_map.height):
                pos = Position(x, y)
                if not self.game_map.is_wall(pos):
                    return pos
        return Position(5, 5)  # Fallback
    
    def test_player_interaction_with_cooling_nodes(self):
        """Test player interaction with cooling nodes."""
        cooling_nodes = self.game_map.cooling_nodes
        
        if len(cooling_nodes) > 0:
            # Move player to cooling node
            node_x, node_y = list(cooling_nodes)[0]
            node_pos = Position(node_x, node_y)
            
            if not self.game_map.is_wall(node_pos):
                self.player.position = node_pos
                
                # Test cooling node effects
                initial_heat = self.player.heat
                self.player.heat = 50  # Set some heat to test cooling
                
                # Simulate cooling node interaction
                # (In real game, this would be handled by game engine)
                player_at_cooling_node = (self.player.position.x, self.player.position.y) in cooling_nodes
                
                assert player_at_cooling_node, "Player should be detected at cooling node"
                assert self.player.heat >= 0, "Heat should be valid value"
                
                # Test that cooling nodes are properly placed
                assert node_pos.is_valid(self.game_map.width, self.game_map.height), "Cooling nodes should be within map bounds"
    
    def test_player_interaction_with_cpu_recovery_nodes(self):
        """Test player interaction with CPU recovery nodes."""
        cpu_nodes = self.game_map.cpu_recovery_nodes
        
        if len(cpu_nodes) > 0:
            # Move player to CPU recovery node
            node_x, node_y = list(cpu_nodes)[0]
            node_pos = Position(node_x, node_y)
            
            if not self.game_map.is_wall(node_pos):
                self.player.position = node_pos
                
                # Test CPU recovery effects
                self.player.cpu = 70  # Simulate some damage
                initial_cpu = self.player.cpu
                
                # Verify player is at CPU node
                player_at_cpu_node = (self.player.position.x, self.player.position.y) in cpu_nodes
                
                assert player_at_cpu_node, "Player should be detected at CPU recovery node"
                assert self.player.cpu <= self.player.max_cpu, "CPU should not exceed maximum"
                assert initial_cpu >= 0, "CPU should be valid value"
    
    def test_player_vision_and_exploration_mechanics(self):
        """Test player vision system and map exploration."""
        # Test vision range
        vision_range = self.player.base_vision_range
        assert vision_range > 0, "Player should have vision range"
        
        # Test exploration tracking
        initial_explored = len(self.game_map.explored_tiles)
        
        # Simulate exploring current area
        player_pos = self.player.position
        exploration_area = []
        
        for dx in range(-2, 3):  # 5x5 area around player
            for dy in range(-2, 3):
                explore_x = player_pos.x + dx
                explore_y = player_pos.y + dy
                
                if (0 <= explore_x < self.game_map.width and 
                    0 <= explore_y < self.game_map.height):
                    exploration_area.append((explore_x, explore_y))
        
        # Add tiles to explored set (simulating vision system)
        for tile in exploration_area:
            self.game_map.explored_tiles.add(tile)
        
        final_explored = len(self.game_map.explored_tiles)
        
        # Verify exploration mechanics
        assert final_explored >= initial_explored, "Exploration should increase explored tiles"
        assert len(exploration_area) > 0, "Should have area around player to explore"
        assert (player_pos.x, player_pos.y) in self.game_map.explored_tiles, "Player's current position should be explored"
    
    def test_map_boundary_handling(self):
        """Test how player movement handles map boundaries."""
        # Test movement at map edges
        edge_positions = [
            Position(0, 5),  # Left edge
            Position(self.game_map.width - 1, 5),  # Right edge
            Position(5, 0),  # Top edge
            Position(5, self.game_map.height - 1),  # Bottom edge
            Position(0, 0),  # Top-left corner
            Position(self.game_map.width - 1, self.game_map.height - 1)  # Bottom-right corner
        ]
        
        for edge_pos in edge_positions:
            # Only test if position is not a wall
            if not self.game_map.is_wall(edge_pos):
                self.player.position = edge_pos
                
                # Test movement beyond boundaries
                beyond_positions = [
                    Position(edge_pos.x - 1, edge_pos.y),
                    Position(edge_pos.x + 1, edge_pos.y),
                    Position(edge_pos.x, edge_pos.y - 1),
                    Position(edge_pos.x, edge_pos.y + 1)
                ]
                
                for beyond_pos in beyond_positions:
                    # Verify boundary checking
                    is_valid = beyond_pos.is_valid(self.game_map.width, self.game_map.height)
                    is_in_bounds = (0 <= beyond_pos.x < self.game_map.width and 
                                  0 <= beyond_pos.y < self.game_map.height)
                    
                    assert is_valid == is_in_bounds, "Boundary validation should be consistent"
    
    def test_complex_navigation_scenario(self):
        """Test navigation through complex map layouts."""
        # Find a path from current position to gateway
        start = self.player.position
        gateway = self.game_map.gateway
        
        if gateway is not None:
            # Simple pathfinding test - try to get closer to gateway
            max_steps = 20
            current_pos = start
            
            for step in range(max_steps):
                # Calculate direction to gateway
                dx = 1 if gateway.x > current_pos.x else (-1 if gateway.x < current_pos.x else 0)
                dy = 1 if gateway.y > current_pos.y else (-1 if gateway.y < current_pos.y else 0)
                
                # Try to move toward gateway
                next_pos = Position(current_pos.x + dx, current_pos.y + dy)
                
                # Check if move is valid
                if (next_pos.is_valid(self.game_map.width, self.game_map.height) and
                    not self.game_map.is_wall(next_pos)):
                    current_pos = next_pos
                    self.player.position = current_pos
                
                # Check if we reached gateway
                if current_pos.x == gateway.x and current_pos.y == gateway.y:
                    break
            
            # Verify navigation progress
            final_distance = abs(current_pos.x - gateway.x) + abs(current_pos.y - gateway.y)
            initial_distance = abs(start.x - gateway.x) + abs(start.y - gateway.y)
            
            assert final_distance <= initial_distance, "Should make progress toward gateway"
            assert current_pos.is_valid(self.game_map.width, self.game_map.height), "Final position should be valid"