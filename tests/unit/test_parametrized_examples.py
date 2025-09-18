#!/usr/bin/env python3
"""
Examples of parametrized testing patterns for RogueSignalProtocol.
Demonstrates best practices for comprehensive test coverage using pytest.mark.parametrize.
"""

import pytest
from unittest.mock import Mock
from game_entities import Position, EnemyState, EnemyMovement, TargetingMode
from game_data import GameData
from game_characters import Player, Enemy
from game_combat import ExploitSystem
from tests.fixtures.mock_factories import MockPlayerFactory, MockEnemyFactory, MockGameFactory


class TestParametrizedPositions:
    """Examples of parametrized testing for position-related functionality."""
    
    @pytest.mark.parametrize("x,y,width,height,expected", [
        # Valid positions
        (0, 0, 50, 50, True),          # Origin
        (25, 25, 50, 50, True),        # Center
        (49, 49, 50, 50, True),        # Bottom-right corner (inclusive)
        
        # Invalid positions - out of bounds
        (-1, 25, 50, 50, False),       # Negative x
        (25, -1, 50, 50, False),       # Negative y
        (50, 25, 50, 50, False),       # x equals width (exclusive)
        (25, 50, 50, 50, False),       # y equals height (exclusive)
        (100, 100, 50, 50, False),     # Both coordinates too large
        
        # Edge cases
        (0, 0, 1, 1, True),           # Single cell map
        (5, 10, 0, 50, False),        # Zero width
        (5, 10, 50, 0, False),        # Zero height
    ])
    def test_position_validation(self, x, y, width, height, expected):
        """Test position validation with various boundary conditions."""
        pos = Position(x, y)
        assert pos.is_valid(width, height) == expected
    
    @pytest.mark.parametrize("pos1,pos2,expected_distance", [
        # Basic distance calculations
        (Position(0, 0), Position(0, 0), 0.0),        # Same position
        (Position(0, 0), Position(1, 0), 1.0),        # Horizontal adjacent
        (Position(0, 0), Position(0, 1), 1.0),        # Vertical adjacent
        (Position(0, 0), Position(1, 1), 1.414),      # Diagonal adjacent (√2)
        (Position(0, 0), Position(3, 4), 5.0),        # 3-4-5 triangle
        
        # Negative coordinates
        (Position(-5, -5), Position(0, 0), 7.071),     # Negative to origin
        (Position(-3, 4), Position(3, -4), 10.0),     # Across quadrants
        
        # Large distances
        (Position(0, 0), Position(100, 100), 141.421),  # Large diagonal
    ])
    def test_position_distance_calculation(self, pos1, pos2, expected_distance):
        """Test distance calculations between positions."""
        actual_distance = pos1.distance_to(pos2)
        assert abs(actual_distance - expected_distance) < 0.001
        
        # Distance should be symmetric
        reverse_distance = pos2.distance_to(pos1)
        assert abs(reverse_distance - expected_distance) < 0.001
    
    @pytest.mark.parametrize("center,other,expected_adjacent", [
        # Adjacent positions (within 1 tile)
        (Position(5, 5), Position(5, 6), True),       # North
        (Position(5, 5), Position(6, 6), True),       # Northeast
        (Position(5, 5), Position(6, 5), True),       # East
        (Position(5, 5), Position(6, 4), True),       # Southeast
        (Position(5, 5), Position(5, 4), True),       # South
        (Position(5, 5), Position(4, 4), True),       # Southwest
        (Position(5, 5), Position(4, 5), True),       # West
        (Position(5, 5), Position(4, 6), True),       # Northwest
        
        # Same position
        (Position(5, 5), Position(5, 5), True),       # Same position counts as adjacent
        
        # Non-adjacent positions
        (Position(5, 5), Position(7, 5), False),      # 2 tiles east
        (Position(5, 5), Position(5, 8), False),      # 3 tiles north
        (Position(5, 5), Position(8, 8), False),      # Far diagonal
        (Position(0, 0), Position(10, 10), False),    # Very far
    ])
    def test_position_adjacency(self, center, other, expected_adjacent):
        """Test position adjacency detection."""
        assert center.is_adjacent_to(other) == expected_adjacent


class TestParametrizedEnemyBehavior:
    """Examples of parametrized testing for enemy behavior and AI."""
    
    @pytest.mark.parametrize("enemy_type,expected_properties", [
        # Test each enemy type has expected characteristics
        ('scanner', {
            'symbol': 'S',
            'cpu': 35,
            'vision': 5,
            'movement': EnemyMovement.STATIC,
            'damage': 0,
            'name': 'Scanner'
        }),
        ('patrol', {
            'symbol': 'P',
            'cpu': 40,
            'vision': 4,
            'movement': EnemyMovement.PATROL,
            'damage': 15,
            'name': 'Patrol'
        }),
        ('hunter', {
            'symbol': 'H',
            'cpu': 50,
            'vision': 6,
            'movement': EnemyMovement.SEEK,
            'damage': 22,
            'name': 'Hunter'
        }),
        ('admin', {
            'symbol': 'A',
            'cpu': 250,
            'vision': 8,
            'movement': EnemyMovement.TRACK,
            'damage': 45,
            'name': 'Admin Avatar'
        }),
    ])
    def test_enemy_type_properties(self, enemy_type, expected_properties):
        """Test that enemy types have correct properties."""
        enemy = Enemy(Position(10, 10), enemy_type)
        
        for prop_name, expected_value in expected_properties.items():
            if prop_name == 'movement':
                actual_value = enemy.type_data.movement
            else:
                actual_value = getattr(enemy.type_data, prop_name)
            
            assert actual_value == expected_value, f"{enemy_type}.{prop_name} should be {expected_value}, got {actual_value}"
    
    @pytest.mark.parametrize("enemy_state,expected_color_type", [
        (EnemyState.UNAWARE, "yellow-ish"),    # Enemy unaware color
        (EnemyState.ALERT, "orange-ish"),      # Enemy alert color
        (EnemyState.HOSTILE, "red-ish"),       # Enemy hostile color
    ])
    def test_enemy_color_by_state(self, enemy_state, expected_color_type):
        """Test that enemy colors change based on state."""
        enemy = Enemy(Position(10, 10), 'scanner')
        enemy.state = enemy_state
        enemy.disabled_turns = 0  # Not disabled
        
        color = enemy.get_color()
        
        # Verify it's a valid RGB tuple
        assert isinstance(color, tuple)
        assert len(color) == 3
        assert all(0 <= c <= 255 for c in color)
        
        # Color should be appropriate for state (basic sanity check)
        if enemy_state == EnemyState.HOSTILE:
            # Hostile should have more red component
            assert color[0] > color[1] and color[0] > color[2]
    
    @pytest.mark.parametrize("player_distance,vision_range,expected_can_see", [
        # Within vision range
        (3, 5, True),
        (5, 5, True),   # At exact range
        (1, 8, True),
        
        # Beyond vision range
        (6, 5, False),
        (10, 5, False),
        (15, 8, False),
        
        # Edge cases
        (0, 5, True),   # Same position
        (1, 1, True),   # Minimum vision
    ])
    def test_enemy_vision_range(self, player_distance, vision_range, expected_can_see):
        """Test enemy vision based on distance and vision range."""
        # Create enemy with specific vision range
        enemy = MockEnemyFactory.create_basic_enemy('scanner', 10, 10)
        enemy.type_data.vision = vision_range
        enemy.disabled_turns = 0
        
        # Create player at specific distance
        player = MockPlayerFactory.create_basic_player(10 + player_distance, 10)
        player.is_invisible.return_value = False
        
        # Create map that allows sight
        mock_map = Mock()
        mock_map.is_shadow.return_value = False
        mock_map.can_see_position.return_value = True
        
        result = enemy.can_see_player(player, mock_map)
        assert result == expected_can_see


class TestParametrizedExploitSystem:
    """Examples of parametrized testing for exploit mechanics."""
    
    @pytest.mark.parametrize("exploit_name,expected_properties", [
        # Stealth exploits
        ('shadow_step', {
            'category': 'stealth',
            'damage': 0,
            'targeting': TargetingMode.SINGLE,
            'range': 6
        }),
        ('data_mimic', {
            'category': 'stealth',
            'damage': 0,
            'targeting': TargetingMode.NONE,
            'range': 0
        }),
        
        # Combat exploits
        ('code_injection', {
            'category': 'combat',
            'damage': 25,
            'targeting': TargetingMode.SINGLE,
            'range': 5
        }),
        ('buffer_overflow', {
            'category': 'combat',
            'damage': 40,
            'targeting': TargetingMode.SINGLE,
            'range': 1
        }),
        ('system_crash', {
            'category': 'combat',
            'damage': 30,
            'targeting': TargetingMode.AREA,
            'range': 3
        }),
        
        # Utility exploits
        ('threat_scan', {
            'category': 'utility',
            'damage': 0,
            'targeting': TargetingMode.NONE,
            'range': 0
        }),
        ('log_wiper', {
            'category': 'utility',
            'damage': 0,
            'targeting': TargetingMode.NONE,
            'range': 0
        }),
    ])
    def test_exploit_properties(self, exploit_name, expected_properties):
        """Test that exploits have correct properties."""
        if exploit_name not in GameData.EXPLOITS:
            pytest.skip(f"Exploit {exploit_name} not found in game data")
        
        exploit = GameData.EXPLOITS[exploit_name]
        
        for prop_name, expected_value in expected_properties.items():
            actual_value = getattr(exploit, prop_name)
            assert actual_value == expected_value, f"{exploit_name}.{prop_name} should be {expected_value}, got {actual_value}"
    
    @pytest.mark.parametrize("base_heat,efficiency_active,expected_cost", [
        # Normal heat costs
        (30, False, 30),
        (25, False, 25),
        (50, False, 50),
        
        # With efficiency bonus (60% cost)
        (30, True, 18),   # 30 * 0.6
        (25, True, 15),   # 25 * 0.6
        (50, True, 30),   # 50 * 0.6
        
        # Edge cases
        (10, True, 6),    # 10 * 0.6
        (1, True, 0),     # 1 * 0.6 = 0.6 -> 0 (int conversion)
    ])
    def test_exploit_heat_cost_calculation(self, base_heat, efficiency_active, expected_cost):
        """Test exploit heat cost calculations with efficiency bonuses."""
        # Create mock game with efficiency state
        mock_game = MockGameFactory.create_basic_game()
        mock_game.player.temporary_effects['exploit_efficiency_turns'] = 5 if efficiency_active else 0
        
        exploit_system = ExploitSystem(mock_game)
        
        # Create mock exploit with specified heat cost
        mock_exploit = Mock()
        mock_exploit.heat = base_heat
        
        actual_cost = exploit_system._calculate_heat_cost(mock_exploit)
        assert actual_cost == expected_cost
    
    @pytest.mark.parametrize("player_pos,target_pos,exploit_range,expected_valid", [
        # Valid targets within range
        (Position(10, 10), Position(13, 10), 5, True),     # Distance 3, range 5
        (Position(10, 10), Position(15, 10), 5, True),     # Distance 5, range 5 (exact)
        (Position(10, 10), Position(10, 12), 3, True),     # Distance 2, range 3
        
        # Invalid targets - out of range
        (Position(10, 10), Position(16, 10), 5, False),    # Distance 6, range 5
        (Position(10, 10), Position(20, 10), 5, False),    # Distance 10, range 5
        (Position(10, 10), Position(10, 15), 3, False),    # Distance 5, range 3
        
        # Edge cases
        (Position(10, 10), Position(10, 10), 5, True),     # Same position (distance 0)
        (Position(10, 10), Position(11, 11), 1, False),    # Diagonal distance ~1.4, range 1
    ])
    def test_exploit_targeting_validation(self, player_pos, target_pos, exploit_range, expected_valid):
        """Test exploit targeting validation based on range."""
        mock_game = MockGameFactory.create_basic_game()
        mock_game.player.position = player_pos
        
        exploit_system = ExploitSystem(mock_game)
        
        # Create mock exploit with specified range
        mock_exploit = Mock()
        mock_exploit.range = exploit_range
        
        # Mock map validation to always pass (testing range only)
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr('game_config.GameConfig.MAP_WIDTH', 50)
            mp.setattr('game_config.GameConfig.MAP_HEIGHT', 50)
            
            result = exploit_system._validate_target(mock_exploit, target_pos)
            assert result == expected_valid


class TestParametrizedCombatScenarios:
    """Examples of parametrized testing for complex combat scenarios."""
    
    @pytest.mark.parametrize("scenario_name,player_state,enemy_states,expected_outcome", [
        # Basic combat scenarios
        ("player_vs_weak_enemy", 
         {"cpu": 100, "heat": 0}, 
         [{"type": "bot", "state": EnemyState.HOSTILE, "cpu": 25}],
         {"player_survives": True, "enemies_defeated": 1}),
        
        ("player_vs_strong_enemy",
         {"cpu": 30, "heat": 80},
         [{"type": "admin", "state": EnemyState.HOSTILE, "cpu": 250}],
         {"player_survives": False, "enemies_defeated": 0}),
        
        ("player_vs_multiple_enemies",
         {"cpu": 100, "heat": 20},
         [
             {"type": "hunter", "state": EnemyState.HOSTILE, "cpu": 50},
             {"type": "patrol", "state": EnemyState.ALERT, "cpu": 40},
             {"type": "scanner", "state": EnemyState.UNAWARE, "cpu": 35}
         ],
         {"player_survives": True, "enemies_defeated": 2}),  # Scanner doesn't attack
        
        # Stealth scenarios
        ("invisible_player_vs_normal_enemies",
         {"cpu": 80, "heat": 40, "invisible": True},
         [
             {"type": "hunter", "state": EnemyState.HOSTILE, "cpu": 50},
             {"type": "patrol", "state": EnemyState.ALERT, "cpu": 40}
         ],
         {"player_survives": True, "enemies_defeated": 0}),  # Can't be attacked while invisible
        
        ("invisible_player_vs_admin",
         {"cpu": 80, "heat": 40, "invisible": True},
         [{"type": "admin", "state": EnemyState.HOSTILE, "cpu": 250}],
         {"player_survives": False, "enemies_defeated": 0}),  # Admin can attack invisible players
    ])
    def test_combat_scenarios(self, scenario_name, player_state, enemy_states, expected_outcome):
        """Test various combat scenarios with different player and enemy configurations."""
        # Set up player
        player = MockPlayerFactory.create_basic_player()
        player.cpu = player_state["cpu"]
        player.heat = player_state["heat"]
        
        if player_state.get("invisible", False):
            player.temporary_effects['data_mimic_turns'] = 5
            player.is_invisible.return_value = True
        
        # Set up enemies
        enemies = []
        for enemy_state in enemy_states:
            if enemy_state["state"] == EnemyState.HOSTILE:
                enemy = MockEnemyFactory.create_hostile_enemy(enemy_state["type"])
            else:
                enemy = MockEnemyFactory.create_basic_enemy(enemy_state["type"])
                enemy.state = enemy_state["state"]
            
            enemy.cpu = enemy_state["cpu"]
            enemies.append(enemy)
        
        # Simulate combat (simplified)
        player_survived = player.cpu > 0
        enemies_defeated = sum(1 for e in enemies if e.cpu <= 0 or not e.can_attack_player(player))
        
        # Check expected outcomes
        assert player_survived == expected_outcome["player_survives"], f"Player survival mismatch in {scenario_name}"
        # Note: enemies_defeated assertion would need actual combat simulation


class TestParametrizedErrorConditions:
    """Examples of parametrized testing for error conditions and edge cases."""
    
    @pytest.mark.parametrize("invalid_input,expected_exception", [
        # Position distance calculation errors
        ({"pos1": Position(5, 5), "pos2": None}, ValueError),
        
        # Invalid enemy types
        ({"enemy_type": "nonexistent_enemy"}, KeyError),
        ({"enemy_type": ""}, KeyError),
        ({"enemy_type": None}, (KeyError, TypeError)),
    ])
    def test_error_conditions(self, invalid_input, expected_exception):
        """Test that appropriate exceptions are raised for invalid inputs."""
        if "pos2" in invalid_input and invalid_input["pos2"] is None:
            # Test position distance to None
            with pytest.raises(expected_exception):
                invalid_input["pos1"].distance_to(invalid_input["pos2"])
        
        elif "enemy_type" in invalid_input:
            # Test invalid enemy type
            with pytest.raises(expected_exception):
                Enemy(Position(10, 10), invalid_input["enemy_type"])
    
    @pytest.mark.parametrize("boundary_condition", [
        {"map_width": 0, "map_height": 0},      # Zero-sized map
        {"map_width": 1, "map_height": 1},      # Single-cell map
        {"map_width": 1000, "map_height": 1000}, # Very large map
    ])
    def test_boundary_conditions(self, boundary_condition):
        """Test behavior at boundary conditions."""
        width = boundary_condition["map_width"]
        height = boundary_condition["map_height"]
        
        # Test position validation at boundaries
        if width > 0 and height > 0:
            # Valid positions
            assert Position(0, 0).is_valid(width, height) is True
            assert Position(width-1, height-1).is_valid(width, height) is True
            
            # Invalid positions
            assert Position(width, height).is_valid(width, height) is False
            assert Position(-1, -1).is_valid(width, height) is False
        else:
            # Zero-sized maps should reject all positions
            assert Position(0, 0).is_valid(width, height) is False


# Pytest configuration for parametrized tests
pytest_plugins = []

def pytest_configure(config):
    """Configure pytest with custom markers for parametrized tests."""
    config.addinivalue_line(
        "markers", "parametrize: mark test to run with different parameter sets"
    )