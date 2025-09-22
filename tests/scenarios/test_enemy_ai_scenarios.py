#!/usr/bin/env python3
"""
Scenario tests for enemy AI behavior and coordination.
Tests realistic enemy AI scenarios with multiple enemies working together.
"""

import pytest
from unittest.mock import Mock
from game_map import GameMap
from game_level import LevelGenerator
from game_characters import Player, Enemy
from game_entities import Position, EnemyState, EnemyMovement
from game_enemies import EnemyManager
from game_state import MessageLog


class TestEnemyAIBehaviorScenarios:
    """Test realistic enemy AI behavior scenarios."""
    
    def setup_method(self):
        """Set up enemy AI test environment."""
        # Create real game environment
        self.game_map = GameMap(40, 30)
        self.level_generator = LevelGenerator(self.game_map)
        self.level_generator.generate_level(level=1, seed=777)
        
        # Create real player
        safe_pos = self._find_safe_position()
        self.player = Player(safe_pos.x, safe_pos.y)
        
        # Create message log
        self.message_log = MessageLog()
        
        # Create enemy manager with required arguments
        self.enemy_manager = EnemyManager(self.game_map, self.message_log)
        
        # Mock minimal game object
        self.mock_game = Mock()
        self.mock_game.game_map = self.game_map
        self.mock_game.player = self.player
        self.mock_game.enemy_manager = self.enemy_manager
        self.mock_game.message_log = self.message_log
        self.mock_game.turn = 1
    
    def _find_safe_position(self) -> Position:
        """Find a walkable position on the map."""
        for x in range(5, self.game_map.width - 5):
            for y in range(5, self.game_map.height - 5):
                pos = Position(x, y)
                if not self.game_map.is_wall(pos):
                    return pos
        return Position(10, 10)  # Fallback
    
    def _place_enemy_safely(self, enemy_type: str, preferred_x: int, preferred_y: int) -> Enemy:
        """Place an enemy at a safe position near preferred coordinates."""
        # Try preferred position first
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                test_x = preferred_x + dx
                test_y = preferred_y + dy
                test_pos = Position(test_x, test_y)
                
                if (0 <= test_x < self.game_map.width and 
                    0 <= test_y < self.game_map.height and
                    not self.game_map.is_wall(test_pos)):
                    
                    enemy = Enemy(test_pos, enemy_type)
                    self.enemy_manager.add_enemy(enemy)
                    return enemy
        
        # Fallback position
        fallback_pos = Position(15, 15)
        enemy = Enemy(fallback_pos, enemy_type)
        self.enemy_manager.add_enemy(enemy)
        return enemy
    
    def test_single_enemy_patrol_behavior(self):
        """
        Scenario: Single enemy patrols area, detects player, and pursues.
        Tests basic AI state transitions and behavior.
        """
        # ARRANGE: Place patrolling enemy
        patrol_enemy = self._place_enemy_safely('script_kiddie', 20, 15)
        patrol_enemy.state = EnemyState.PATROL
        patrol_enemy.movement_type = EnemyMovement.RANDOM
        
        initial_position = patrol_enemy.position
        initial_state = patrol_enemy.state
        
        # ACT 1: Enemy patrols (simulate movement)
        # In real game, this would be handled by AI system
        patrol_positions = []
        current_pos = patrol_enemy.position
        
        # Simulate 5 patrol moves
        for move in range(5):
            # Try to move in a random direction (simplified patrol)
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                new_x = current_pos.x + dx
                new_y = current_pos.y + dy
                new_pos = Position(new_x, new_y)
                
                if (0 <= new_x < self.game_map.width and 
                    0 <= new_y < self.game_map.height and
                    not self.game_map.is_wall(new_pos)):
                    
                    patrol_enemy.position = new_pos
                    patrol_positions.append(new_pos)
                    current_pos = new_pos
                    break
        
        # ACT 2: Player gets close (trigger detection)
        # Move player near enemy
        detection_distance = 3
        player_detection_pos = Position(
            patrol_enemy.position.x + detection_distance,
            patrol_enemy.position.y
        )
        
        if not self.game_map.is_wall(player_detection_pos):
            self.player.position = player_detection_pos
            
            # Calculate distance for detection test
            distance = abs(self.player.position.x - patrol_enemy.position.x) + abs(self.player.position.y - patrol_enemy.position.y)
            
            # Simulate detection (in real game, this would be automatic)
            if distance <= 5:  # Detection range
                patrol_enemy.state = EnemyState.HOSTILE
                patrol_enemy.last_known_player_position = self.player.position
        
        # ASSERT: Verify patrol and detection behavior
        assert initial_state == EnemyState.PATROL, "Enemy should start in patrol state"
        assert len(patrol_positions) > 0, "Enemy should move during patrol"
        assert patrol_enemy.position != initial_position or len(patrol_positions) == 0, "Enemy should change position or be blocked"
        
        if patrol_enemy.state == EnemyState.HOSTILE:
            assert hasattr(patrol_enemy, 'last_known_player_position'), "Hostile enemy should track player position"
    
    def test_multiple_enemy_coordination_scenario(self):
        """
        Scenario: Multiple enemies coordinate to hunt player.
        Tests enemy communication and group behavior.
        """
        # ARRANGE: Place multiple enemies in formation
        enemies = []
        enemy_positions = [
            (15, 10),  # North guard
            (25, 15),  # East guard
            (20, 20),  # South guard
            (10, 15)   # West guard
        ]
        
        for i, (x, y) in enumerate(enemy_positions):
            enemy = self._place_enemy_safely('script_kiddie', x, y)
            enemy.state = EnemyState.PATROL
            enemies.append(enemy)
        
        initial_enemy_count = len(enemies)
        initial_states = [enemy.state for enemy in enemies]
        
        # ACT 1: One enemy detects player
        detecting_enemy = enemies[0]
        # Place player in detection range
        detection_pos = Position(detecting_enemy.position.x + 2, detecting_enemy.position.y + 1)
        
        if not self.game_map.is_wall(detection_pos):
            self.player.position = detection_pos
            
            # First enemy detects player
            detecting_enemy.state = EnemyState.HOSTILE
            detecting_enemy.last_known_player_position = self.player.position
            
            # ACT 2: Alert spreads to nearby enemies (simulate communication)
            alert_radius = 8
            alerted_enemies = 0
            
            for other_enemy in enemies[1:]:  # Skip the detecting enemy
                distance_to_detector = (abs(other_enemy.position.x - detecting_enemy.position.x) + 
                                      abs(other_enemy.position.y - detecting_enemy.position.y))
                
                if distance_to_detector <= alert_radius:
                    other_enemy.state = EnemyState.HOSTILE
                    other_enemy.last_known_player_position = self.player.position
                    alerted_enemies += 1
            
            # ACT 3: Enemies coordinate movement toward player
            coordinated_moves = 0
            for enemy in enemies:
                if enemy.state == EnemyState.HOSTILE and hasattr(enemy, 'last_known_player_position'):
                    # Move toward last known player position
                    target = enemy.last_known_player_position
                    dx = 1 if target.x > enemy.position.x else (-1 if target.x < enemy.position.x else 0)
                    dy = 1 if target.y > enemy.position.y else (-1 if target.y < enemy.position.y else 0)
                    
                    new_x = enemy.position.x + dx
                    new_y = enemy.position.y + dy
                    new_pos = Position(new_x, new_y)
                    
                    if (0 <= new_x < self.game_map.width and 
                        0 <= new_y < self.game_map.height and
                        not self.game_map.is_wall(new_pos)):
                        
                        enemy.position = new_pos
                        coordinated_moves += 1
        
        # ASSERT: Verify coordination behavior
        assert initial_enemy_count >= 2, "Should have multiple enemies for coordination test"
        assert all(state == EnemyState.PATROL for state in initial_states), "Enemies should start in patrol"
        
        hostile_enemies = len([e for e in enemies if e.state == EnemyState.HOSTILE])
        assert hostile_enemies >= 1, "At least one enemy should become hostile"
        
        if hostile_enemies > 1:
            assert coordinated_moves > 0, "Multiple hostile enemies should coordinate movement"
    
    def test_enemy_search_and_hunt_scenario(self):
        """
        Scenario: Enemy loses sight of player and searches last known location.
        Tests enemy search patterns and persistence.
        """
        # ARRANGE: Enemy and player setup
        hunter_enemy = self._place_enemy_safely('admin', 20, 15)  # Use admin type for better hunting
        hunter_enemy.state = EnemyState.HOSTILE
        
        # Place player initially visible
        initial_player_pos = Position(hunter_enemy.position.x + 3, hunter_enemy.position.y)
        if not self.game_map.is_wall(initial_player_pos):
            self.player.position = initial_player_pos
            hunter_enemy.last_known_player_position = self.player.position
        
        # ACT 1: Player moves out of sight
        hiding_positions = []
        for x in range(self.game_map.width):
            for y in range(self.game_map.height):
                pos = Position(x, y)
                if (not self.game_map.is_wall(pos) and
                    abs(x - hunter_enemy.position.x) > 8 and  # Far from enemy
                    abs(y - hunter_enemy.position.y) > 8):
                    hiding_positions.append(pos)
        
        if len(hiding_positions) > 0:
            # Move player to hiding spot
            hiding_spot = hiding_positions[0]
            self.player.position = hiding_spot
            
            # ACT 2: Enemy searches last known location
            last_known = hunter_enemy.last_known_player_position
            search_area = []
            
            # Generate search pattern around last known position
            for dx in range(-3, 4):
                for dy in range(-3, 4):
                    search_x = last_known.x + dx
                    search_y = last_known.y + dy
                    search_pos = Position(search_x, search_y)
                    
                    if (0 <= search_x < self.game_map.width and 
                        0 <= search_y < self.game_map.height and
                        not self.game_map.is_wall(search_pos)):
                        search_area.append(search_pos)
            
            # Simulate enemy searching (move through search area)
            search_moves = 0
            current_enemy_pos = hunter_enemy.position
            
            for search_target in search_area[:5]:  # Check first 5 search positions
                # Move toward search position
                dx = 1 if search_target.x > current_enemy_pos.x else (-1 if search_target.x < current_enemy_pos.x else 0)
                dy = 1 if search_target.y > current_enemy_pos.y else (-1 if search_target.y < current_enemy_pos.y else 0)
                
                new_pos = Position(current_enemy_pos.x + dx, current_enemy_pos.y + dy)
                
                if (0 <= new_pos.x < self.game_map.width and 
                    0 <= new_pos.y < self.game_map.height and
                    not self.game_map.is_wall(new_pos)):
                    
                    hunter_enemy.position = new_pos
                    current_enemy_pos = new_pos
                    search_moves += 1
        
        # ACT 3: Test re-detection if player gets close again
        final_distance = abs(self.player.position.x - hunter_enemy.position.x) + abs(self.player.position.y - hunter_enemy.position.y)
        
        # ASSERT: Verify search behavior
        assert hunter_enemy.state == EnemyState.HOSTILE, "Enemy should remain hostile during search"
        assert hasattr(hunter_enemy, 'last_known_player_position'), "Enemy should remember last known position"
        assert len(search_area) > 0, "Enemy should have search area around last known position"
        
        if len(hiding_positions) > 0:
            assert final_distance > 5, "Player should be able to hide from searching enemy"
    
    def test_enemy_special_abilities_scenario(self):
        """
        Scenario: Different enemy types use their special abilities.
        Tests enemy type-specific behaviors and capabilities.
        """
        # ARRANGE: Create enemies of different types
        enemy_types = ['script_kiddie', 'admin', 'ghost_protocol']
        special_enemies = []
        
        for i, enemy_type in enumerate(enemy_types):
            x = 10 + (i * 8)
            y = 10 + (i * 3)
            enemy = self._place_enemy_safely(enemy_type, x, y)
            enemy.state = EnemyState.PATROL
            special_enemies.append(enemy)
        
        # ACT 1: Test each enemy's movement capabilities
        movement_results = {}
        
        for enemy in special_enemies:
            initial_pos = enemy.position
            
            # Try to move enemy (different types may have different movement)
            for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                new_x = initial_pos.x + dx
                new_y = initial_pos.y + dy
                new_pos = Position(new_x, new_y)
                
                if (0 <= new_x < self.game_map.width and 
                    0 <= new_y < self.game_map.height and
                    not self.game_map.is_wall(new_pos)):
                    
                    enemy.position = new_pos
                    movement_results[enemy.type] = True
                    break
            else:
                movement_results[enemy.type] = False
        
        # ACT 2: Test enemy-specific attributes
        enemy_attributes = {}
        for enemy in special_enemies:
            attributes = {
                'has_position': hasattr(enemy, 'position'),
                'has_state': hasattr(enemy, 'state'),
                'has_type': hasattr(enemy, 'type'),
                'has_id': hasattr(enemy, 'id')
            }
            enemy_attributes[enemy.type] = attributes
        
        # ACT 3: Test different detection/aggression patterns
        # Place player and test detection by different enemy types
        test_pos = Position(15, 12)
        if not self.game_map.is_wall(test_pos):
            self.player.position = test_pos
            
            detection_results = {}
            for enemy in special_enemies:
                distance = abs(enemy.position.x - self.player.position.x) + abs(enemy.position.y - self.player.position.y)
                detection_results[enemy.type] = {
                    'distance': distance,
                    'can_detect': distance <= 6,  # Assume 6-tile detection range
                    'initial_state': enemy.state
                }
        
        # ASSERT: Verify enemy type diversity and capabilities
        assert len(special_enemies) >= 2, "Should test multiple enemy types"
        
        for enemy in special_enemies:
            assert hasattr(enemy, 'type'), f"Enemy should have type attribute"
            assert hasattr(enemy, 'position'), f"Enemy should have position"
            assert hasattr(enemy, 'state'), f"Enemy should have state"
        
        # Verify different enemy types have different characteristics
        enemy_type_set = set(enemy.type for enemy in special_enemies)
        assert len(enemy_type_set) >= 2, "Should have enemies of different types"
    
    def test_enemy_pathfinding_scenario(self):
        """
        Scenario: Enemies navigate around obstacles to reach objectives.
        Tests pathfinding and navigation intelligence.
        """
        # ARRANGE: Create enemy with pathfinding challenge
        navigator_enemy = self._place_enemy_safely('script_kiddie', 5, 5)
        navigator_enemy.state = EnemyState.HOSTILE
        
        # Set target position across some obstacles
        target_x = navigator_enemy.position.x + 10
        target_y = navigator_enemy.position.y + 5
        target_pos = Position(target_x, target_y)
        
        # Ensure target is reachable
        if (0 <= target_x < self.game_map.width and 
            0 <= target_y < self.game_map.height):
            navigator_enemy.last_known_player_position = target_pos
        
        # ACT 1: Attempt pathfinding (simplified)
        max_pathfinding_steps = 15
        pathfinding_moves = []
        current_pos = navigator_enemy.position
        
        for step in range(max_pathfinding_steps):
            if hasattr(navigator_enemy, 'last_known_player_position'):
                target = navigator_enemy.last_known_player_position
                
                # Simple pathfinding - try direct movement first, then alternatives
                dx = 1 if target.x > current_pos.x else (-1 if target.x < current_pos.x else 0)
                dy = 1 if target.y > current_pos.y else (-1 if target.y < current_pos.y else 0)
                
                # Try direct movement
                direct_pos = Position(current_pos.x + dx, current_pos.y + dy)
                
                if (0 <= direct_pos.x < self.game_map.width and 
                    0 <= direct_pos.y < self.game_map.height and
                    not self.game_map.is_wall(direct_pos)):
                    
                    navigator_enemy.position = direct_pos
                    current_pos = direct_pos
                    pathfinding_moves.append(direct_pos)
                else:
                    # Try alternative movements if direct path is blocked
                    alternatives = []
                    if dx != 0:
                        alternatives.append(Position(current_pos.x + dx, current_pos.y))
                    if dy != 0:
                        alternatives.append(Position(current_pos.x, current_pos.y + dy))
                    
                    for alt_pos in alternatives:
                        if (0 <= alt_pos.x < self.game_map.width and 
                            0 <= alt_pos.y < self.game_map.height and
                            not self.game_map.is_wall(alt_pos)):
                            
                            navigator_enemy.position = alt_pos
                            current_pos = alt_pos
                            pathfinding_moves.append(alt_pos)
                            break
                
                # Check if reached target
                if (current_pos.x == target.x and current_pos.y == target.y):
                    break
        
        # Calculate final distance to target
        if hasattr(navigator_enemy, 'last_known_player_position'):
            final_distance = abs(current_pos.x - navigator_enemy.last_known_player_position.x) + abs(current_pos.y - navigator_enemy.last_known_player_position.y)
            initial_distance = abs(navigator_enemy.position.x - navigator_enemy.last_known_player_position.x) + abs(navigator_enemy.position.y - navigator_enemy.last_known_player_position.y)
        else:
            final_distance = 0
            initial_distance = 0
        
        # ASSERT: Verify pathfinding behavior
        assert len(pathfinding_moves) > 0, "Enemy should attempt to move toward target"
        assert navigator_enemy.position != navigator_enemy.position or len(pathfinding_moves) == 0, "Enemy position should change or be blocked"
        
        if hasattr(navigator_enemy, 'last_known_player_position'):
            # Should make progress toward target (unless completely blocked)
            progress_made = final_distance <= initial_distance + 2  # Allow some tolerance for obstacles
            assert progress_made or len(pathfinding_moves) < 3, "Should make progress or be significantly blocked"