#!/usr/bin/env python3
"""
Unit tests for game_inspection.py - Entity inspection system.

Tests focus on:
- Entity priority system (player > enemies > items > special tiles > terrain)
- Proper formatting of entity information
- Out-of-bounds handling
- Terrain description loading from JSON
- Status effect display
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from game_inspection import EntityInspector
from game_entities import Position, Colors, EnemyState, EnemyMovement


class TestEntityInspectorPriority:
    """Test entity inspection priority system."""

    def test_out_of_bounds_position_handled(self):
        """Test that out-of-bounds positions are handled gracefully."""
        game = Mock()
        game.game_map = Mock()
        game.game_map.width = 50
        game.game_map.height = 50

        # Test position far out of bounds
        oob_position = Position(-10, -10)
        result = EntityInspector.get_entity_at_position(game, oob_position)

        assert result['entity_type'] == 'invalid'
        assert result['name'] == 'Out of Bounds'
        assert result['color'] == Colors.DARK_GRAY

    def test_player_has_highest_priority(self):
        """Test that player is inspected even if other entities at same position."""
        game = Mock()
        game.game_map = Mock()
        game.game_map.width = 50
        game.game_map.height = 50
        game.player = Mock()
        game.player.x = 10
        game.player.y = 10
        game.player.cpu = 100
        game.player.max_cpu = 100
        game.player.heat = 0
        game.player.max_heat = 100
        game.player.ram_total = 10
        game.player.trace_level = 0
        game.player.temporary_effects = {
            'speed_boost_turns': 0,
            'enhanced_vision_turns': 0,
            'exploit_efficiency_turns': 0,
            'invisible_turns': 0,
            'virus_turns': 0,
            'movement_slowed_turns': 0
        }

        position = Position(10, 10)
        result = EntityInspector.get_entity_at_position(game, position)

        assert result['entity_type'] == 'player'
        assert result['name'] == 'Player (You)'
        assert result['color'] == Colors.GREEN

    def test_enemy_priority_over_items(self):
        """Test that enemies are inspected before items."""
        game = Mock()
        game.game_map = Mock()
        game.game_map.width = 50
        game.game_map.height = 50
        game.player = Mock()
        game.player.x = 5  # Player elsewhere
        game.player.y = 5

        # Mock enemy at position
        mock_enemy = Mock()
        mock_enemy.type_data = Mock()
        mock_enemy.type_data.name = "Test Enemy"
        mock_enemy.type_data.description = "A test enemy"
        mock_enemy.type_data.vision = 5
        mock_enemy.type_data.damage = 10
        mock_enemy.type_data.movement = EnemyMovement.RANDOM
        mock_enemy.state = EnemyState.UNAWARE
        mock_enemy.cpu = 50
        mock_enemy.max_cpu = 50
        mock_enemy.disabled_turns = 0

        game.enemy_manager = Mock()
        game.enemy_manager.get_enemy_at_position = Mock(return_value=mock_enemy)

        # Mock item at same position (should be ignored)
        game.game_map.get_code_hack = Mock(return_value=Mock(name="Code Hack"))

        position = Position(10, 10)
        result = EntityInspector.get_entity_at_position(game, position)

        assert result['entity_type'] == 'enemy'
        assert result['name'] == "Test Enemy"

    def test_items_priority_over_terrain(self):
        """Test that items are inspected before terrain."""
        game = Mock()
        game.game_map = Mock()
        game.game_map.width = 50
        game.game_map.height = 50
        game.player = Mock()
        game.player.x = 5
        game.player.y = 5

        game.enemy_manager = Mock()
        game.enemy_manager.get_enemy_at_position = Mock(return_value=None)

        # Mock code hack
        mock_code_hack = Mock()
        mock_code_hack.name = "Blue Code"
        mock_code_hack.color_name = "blue"
        mock_code_hack.discovered = True

        game.game_map.get_code_hack = Mock(return_value=mock_code_hack)
        game.discovered_code_effects = set()
        game.code_hack_effects = {
            'blue': (None, "Test effect")
        }

        # Mock terrain (should be ignored)
        game.game_map.is_wall = Mock(return_value=True)

        position = Position(10, 10)
        result = EntityInspector.get_entity_at_position(game, position)

        assert result['entity_type'] == 'code_hack'
        assert 'Blue Code' in result['name']


class TestPlayerInspection:
    """Test player inspection with various states."""

    def test_player_basic_stats_displayed(self):
        """Test that player's basic stats are shown correctly."""
        game = Mock()
        game.game_map = Mock()
        game.game_map.width = 50
        game.game_map.height = 50
        game.player = Mock()
        game.player.x = 10
        game.player.y = 10
        game.player.cpu = 75
        game.player.max_cpu = 100
        game.player.heat = 40
        game.player.max_heat = 100
        game.player.ram_total = 12
        game.player.trace_level = 25
        game.player.temporary_effects = {
            'speed_boost_turns': 0,
            'enhanced_vision_turns': 0,
            'exploit_efficiency_turns': 0,
            'invisible_turns': 0,
            'virus_turns': 0,
            'movement_slowed_turns': 0
        }

        result = EntityInspector.get_entity_at_position(game, Position(10, 10))

        assert 'CPU: 75/100' in result['details']
        assert 'Heat: 40/100' in result['details']
        assert 'RAM: 12' in result['details']
        assert 'Trace: 25%' in result['details']

    def test_player_with_status_effects(self):
        """Test that player status effects are displayed."""
        game = Mock()
        game.game_map = Mock()
        game.game_map.width = 50
        game.game_map.height = 50
        game.player = Mock()
        game.player.x = 10
        game.player.y = 10
        game.player.cpu = 100
        game.player.max_cpu = 100
        game.player.heat = 0
        game.player.max_heat = 100
        game.player.ram_total = 10
        game.player.trace_level = 0
        game.player.temporary_effects = {
            'speed_boost_turns': 3,
            'enhanced_vision_turns': 5,
            'exploit_efficiency_turns': 0,
            'invisible_turns': 2,
            'virus_turns': 0,
            'movement_slowed_turns': 0
        }

        result = EntityInspector.get_entity_at_position(game, Position(10, 10))

        assert 'Speed Boost (3 turns)' in result['details']
        assert 'Enhanced Vision (5 turns)' in result['details']
        assert 'Invisible (2 turns)' in result['details']

    def test_player_with_negative_effects(self):
        """Test that player negative effects are displayed."""
        game = Mock()
        game.game_map = Mock()
        game.game_map.width = 50
        game.game_map.height = 50
        game.player = Mock()
        game.player.x = 10
        game.player.y = 10
        game.player.cpu = 100
        game.player.max_cpu = 100
        game.player.heat = 0
        game.player.max_heat = 100
        game.player.ram_total = 10
        game.player.trace_level = 0
        game.player.temporary_effects = {
            'speed_boost_turns': 0,
            'enhanced_vision_turns': 0,
            'exploit_efficiency_turns': 0,
            'invisible_turns': 0,
            'virus_turns': 4,
            'movement_slowed_turns': 2
        }

        result = EntityInspector.get_entity_at_position(game, Position(10, 10))

        assert 'VIRUS (4 turns)' in result['details']
        assert 'Slowed (2 turns)' in result['details']

    def test_player_no_status_effects(self):
        """Test that 'None' is shown when no status effects active."""
        game = Mock()
        game.game_map = Mock()
        game.game_map.width = 50
        game.game_map.height = 50
        game.player = Mock()
        game.player.x = 10
        game.player.y = 10
        game.player.cpu = 100
        game.player.max_cpu = 100
        game.player.heat = 0
        game.player.max_heat = 100
        game.player.ram_total = 10
        game.player.trace_level = 0
        game.player.temporary_effects = {
            'speed_boost_turns': 0,
            'enhanced_vision_turns': 0,
            'exploit_efficiency_turns': 0,
            'invisible_turns': 0,
            'virus_turns': 0,
            'movement_slowed_turns': 0
        }

        result = EntityInspector.get_entity_at_position(game, Position(10, 10))

        assert 'Status: None' in result['details']


class TestEnemyInspection:
    """Test enemy inspection with various states."""

    def test_unaware_enemy_display(self):
        """Test that unaware enemies show correct color and state."""
        game = Mock()
        game.game_map = Mock()
        game.game_map.width = 50
        game.game_map.height = 50
        game.player = Mock()
        game.player.x = 5
        game.player.y = 5

        mock_enemy = Mock()
        mock_enemy.type_data = Mock()
        mock_enemy.type_data.name = "Scout"
        mock_enemy.type_data.description = "A scout bot"
        mock_enemy.type_data.vision = 5
        mock_enemy.type_data.damage = 10
        mock_enemy.type_data.movement = EnemyMovement.PATROL
        mock_enemy.state = EnemyState.UNAWARE
        mock_enemy.cpu = 50
        mock_enemy.max_cpu = 50
        mock_enemy.disabled_turns = 0

        game.enemy_manager = Mock()
        game.enemy_manager.get_enemy_at_position = Mock(return_value=mock_enemy)

        result = EntityInspector.get_entity_at_position(game, Position(10, 10))

        assert result['color'] == Colors.ENEMY_UNAWARE
        assert 'State: Unaware' in result['details']

    def test_alert_enemy_display(self):
        """Test that alert enemies show correct color and state."""
        game = Mock()
        game.game_map = Mock()
        game.game_map.width = 50
        game.game_map.height = 50
        game.player = Mock()
        game.player.x = 5
        game.player.y = 5

        mock_enemy = Mock()
        mock_enemy.type_data = Mock()
        mock_enemy.type_data.name = "Guard"
        mock_enemy.type_data.description = "A guard bot"
        mock_enemy.type_data.vision = 6
        mock_enemy.type_data.damage = 15
        mock_enemy.type_data.movement = EnemyMovement.STATIC
        mock_enemy.state = EnemyState.ALERT
        mock_enemy.cpu = 60
        mock_enemy.max_cpu = 60
        mock_enemy.disabled_turns = 0

        game.enemy_manager = Mock()
        game.enemy_manager.get_enemy_at_position = Mock(return_value=mock_enemy)

        result = EntityInspector.get_entity_at_position(game, Position(10, 10))

        assert result['color'] == Colors.ENEMY_ALERT
        assert 'State: Alert' in result['details']

    def test_hostile_enemy_display(self):
        """Test that hostile enemies show correct color and state."""
        game = Mock()
        game.game_map = Mock()
        game.game_map.width = 50
        game.game_map.height = 50
        game.player = Mock()
        game.player.x = 5
        game.player.y = 5

        mock_enemy = Mock()
        mock_enemy.type_data = Mock()
        mock_enemy.type_data.name = "Hunter"
        mock_enemy.type_data.description = "A hunter bot"
        mock_enemy.type_data.vision = 8
        mock_enemy.type_data.damage = 20
        mock_enemy.type_data.movement = EnemyMovement.SEEK
        mock_enemy.state = EnemyState.HOSTILE
        mock_enemy.cpu = 80
        mock_enemy.max_cpu = 80
        mock_enemy.disabled_turns = 0

        game.enemy_manager = Mock()
        game.enemy_manager.get_enemy_at_position = Mock(return_value=mock_enemy)

        result = EntityInspector.get_entity_at_position(game, Position(10, 10))

        assert result['color'] == Colors.ENEMY_HOSTILE
        assert 'State: Hostile' in result['details']

    def test_disabled_enemy_shows_turns(self):
        """Test that disabled enemies show remaining disabled turns."""
        game = Mock()
        game.game_map = Mock()
        game.game_map.width = 50
        game.game_map.height = 50
        game.player = Mock()
        game.player.x = 5
        game.player.y = 5

        mock_enemy = Mock()
        mock_enemy.type_data = Mock()
        mock_enemy.type_data.name = "Disabled Guard"
        mock_enemy.type_data.description = "A disabled guard"
        mock_enemy.type_data.vision = 5
        mock_enemy.type_data.damage = 10
        mock_enemy.type_data.movement = EnemyMovement.STATIC
        mock_enemy.state = EnemyState.UNAWARE
        mock_enemy.cpu = 50
        mock_enemy.max_cpu = 50
        mock_enemy.disabled_turns = 3

        game.enemy_manager = Mock()
        game.enemy_manager.get_enemy_at_position = Mock(return_value=mock_enemy)

        result = EntityInspector.get_entity_at_position(game, Position(10, 10))

        assert 'Disabled for 3 turns' in result['details']

    def test_enemy_movement_descriptions(self):
        """Test that different enemy movement types show correct descriptions."""
        game = Mock()
        game.game_map = Mock()
        game.game_map.width = 50
        game.game_map.height = 50
        game.player = Mock()
        game.player.x = 5
        game.player.y = 5

        movement_tests = [
            (EnemyMovement.STATIC, "Static guard"),
            (EnemyMovement.PATROL, "Patrols route"),
            (EnemyMovement.RANDOM, "Random movement"),
            (EnemyMovement.SEEK, "Actively hunting"),
            (EnemyMovement.ADMIN, "Relentless pursuer"),
            (EnemyMovement.TRACK, "Tracking target"),
            (EnemyMovement.VIRUS, "Unpredictable")
        ]

        for movement_type, expected_desc in movement_tests:
            mock_enemy = Mock()
            mock_enemy.type_data = Mock()
            mock_enemy.type_data.name = "Test Enemy"
            mock_enemy.type_data.description = "Test"
            mock_enemy.type_data.vision = 5
            mock_enemy.type_data.damage = 10
            mock_enemy.type_data.movement = movement_type
            mock_enemy.state = EnemyState.UNAWARE
            mock_enemy.cpu = 50
            mock_enemy.max_cpu = 50
            mock_enemy.disabled_turns = 0

            game.enemy_manager = Mock()
            game.enemy_manager.get_enemy_at_position = Mock(return_value=mock_enemy)

            result = EntityInspector.get_entity_at_position(game, Position(10, 10))

            assert expected_desc in result['details'], f"Expected '{expected_desc}' for movement type {movement_type}"


class TestItemInspection:
    """Test inspection of items (code hacks, exploits, upgrades, story fragments)."""

    def test_discovered_code_hack_shows_effect(self):
        """Test that discovered code hacks show their effect."""
        game = Mock()
        game.game_map = Mock()
        game.game_map.width = 50
        game.game_map.height = 50
        game.player = Mock()
        game.player.x = 5
        game.player.y = 5
        game.enemy_manager = Mock()
        game.enemy_manager.get_enemy_at_position = Mock(return_value=None)

        mock_code_hack = Mock()
        mock_code_hack.name = "Blue Code"
        mock_code_hack.color_name = "blue"
        mock_code_hack.discovered = True

        game.game_map.get_code_hack = Mock(return_value=mock_code_hack)
        game.discovered_code_effects = set()
        game.code_hack_effects = {
            'blue': (None, "Reduces heat by 20")
        }

        result = EntityInspector.get_entity_at_position(game, Position(10, 10))

        assert result['entity_type'] == 'code_hack'
        assert result['description'] == "Reduces heat by 20"

    def test_unknown_code_hack_shows_unknown(self):
        """Test that undiscovered code hacks show 'Unknown effect'."""
        game = Mock()
        game.game_map = Mock()
        game.game_map.width = 50
        game.game_map.height = 50
        game.player = Mock()
        game.player.x = 5
        game.player.y = 5
        game.enemy_manager = Mock()
        game.enemy_manager.get_enemy_at_position = Mock(return_value=None)

        mock_code_hack = Mock()
        mock_code_hack.name = "Red Code"
        mock_code_hack.color_name = "red"
        mock_code_hack.discovered = False

        game.game_map.get_code_hack = Mock(return_value=mock_code_hack)
        game.discovered_code_effects = set()
        game.code_hack_effects = {}

        result = EntityInspector.get_entity_at_position(game, Position(10, 10))

        assert result['description'] == "Unknown effect until used"

    def test_exploit_pickup_shows_stats(self):
        """Test that exploit pickups show their stats."""
        from game_entities import ExploitDefinition

        game = Mock()
        game.game_map = Mock()
        game.game_map.width = 50
        game.game_map.height = 50
        game.player = Mock()
        game.player.x = 5
        game.player.y = 5
        game.enemy_manager = Mock()
        game.enemy_manager.get_enemy_at_position = Mock(return_value=None)
        game.game_map.get_code_hack = Mock(return_value=None)

        mock_pickup = Mock()
        mock_pickup.exploit_key = "test_exploit"

        game.game_map.get_exploit_pickup = Mock(return_value=mock_pickup)

        # Mock exploit definition
        mock_exploit = ExploitDefinition(
            name="Test Exploit",
            ram=5,
            heat=10,
            range=3,
            category="offensive",
            damage=25,
            targeting="single",
            description="A test exploit"
        )

        with patch('game_inspection.GameData') as mock_game_data:
            mock_game_data.EXPLOITS = {'test_exploit': mock_exploit}

            result = EntityInspector.get_entity_at_position(game, Position(10, 10))

            assert result['entity_type'] == 'exploit_pickup'
            assert 'RAM: 5' in result['details']
            assert 'Heat: 10' in result['details']
            assert 'Damage: 25' in result['details']

    def test_story_fragment_shows_index(self):
        """Test that story fragments show their fragment index."""
        game = Mock()
        game.game_map = Mock()
        game.game_map.width = 50
        game.game_map.height = 50
        game.player = Mock()
        game.player.x = 5
        game.player.y = 5
        game.enemy_manager = Mock()
        game.enemy_manager.get_enemy_at_position = Mock(return_value=None)
        game.game_map.get_code_hack = Mock(return_value=None)
        game.game_map.get_exploit_pickup = Mock(return_value=None)
        game.game_map.permanent_upgrades = {}

        mock_fragment = Mock()
        mock_fragment.fragment_index = 5

        game.game_map.story_fragments = {(10, 10): mock_fragment}

        result = EntityInspector.get_entity_at_position(game, Position(10, 10))

        assert result['entity_type'] == 'story_fragment'
        assert 'Fragment #5' in result['details']
        assert result['color'] == Colors.STORY_FRAGMENT


class TestSpecialTileInspection:
    """Test inspection of special tiles (gateway, nodes)."""

    def test_gateway_shows_level_info(self):
        """Test that gateway shows current level exit info."""
        game = Mock()
        game.game_map = Mock()
        game.game_map.width = 50
        game.game_map.height = 50
        game.player = Mock()
        game.player.x = 5
        game.player.y = 5
        game.enemy_manager = Mock()
        game.enemy_manager.get_enemy_at_position = Mock(return_value=None)
        game.game_map.get_code_hack = Mock(return_value=None)
        game.game_map.get_exploit_pickup = Mock(return_value=None)
        game.game_map.permanent_upgrades = {}
        game.game_map.story_fragments = {}
        game.level = 3

        mock_gateway = Mock()
        mock_gateway.x = 10
        mock_gateway.y = 10
        game.game_map.gateway = mock_gateway

        # Mock terrain descriptions
        EntityInspector._terrain_descriptions = {
            'gateway': {
                'name': 'Network Gateway',
                'description': 'Exit to next network level'
            }
        }

        result = EntityInspector.get_entity_at_position(game, Position(10, 10))

        assert result['entity_type'] == 'gateway'
        assert 'Level 3 exit' in result['details']
        assert result['color'] == Colors.GATEWAY

    def test_cooling_node_identified(self):
        """Test that cooling nodes are properly identified."""
        game = Mock()
        game.game_map = Mock()
        game.game_map.width = 50
        game.game_map.height = 50
        game.player = Mock()
        game.player.x = 5
        game.player.y = 5
        game.enemy_manager = Mock()
        game.enemy_manager.get_enemy_at_position = Mock(return_value=None)
        game.game_map.get_code_hack = Mock(return_value=None)
        game.game_map.get_exploit_pickup = Mock(return_value=None)
        game.game_map.permanent_upgrades = {}
        game.game_map.story_fragments = {}
        game.game_map.gateway = None
        game.game_map.is_cooling_node = Mock(return_value=True)

        EntityInspector._terrain_descriptions = {
            'cooling_node': {
                'name': 'Cooling Node',
                'description': 'Reduces heat'
            }
        }

        result = EntityInspector.get_entity_at_position(game, Position(10, 10))

        assert result['entity_type'] == 'cooling_node'
        assert result['color'] == Colors.HEAT_RECOVERY


class TestTerrainInspection:
    """Test terrain inspection (walls, shadows, floors)."""

    def test_wall_identified(self):
        """Test that walls are properly identified."""
        game = Mock()
        game.game_map = Mock()
        game.game_map.width = 50
        game.game_map.height = 50
        game.player = Mock()
        game.player.x = 5
        game.player.y = 5
        game.enemy_manager = Mock()
        game.enemy_manager.get_enemy_at_position = Mock(return_value=None)
        game.game_map.get_code_hack = Mock(return_value=None)
        game.game_map.get_exploit_pickup = Mock(return_value=None)
        game.game_map.permanent_upgrades = {}
        game.game_map.story_fragments = {}
        game.game_map.gateway = None
        game.game_map.is_cooling_node = Mock(return_value=False)
        game.game_map.is_cpu_recovery_node = Mock(return_value=False)
        game.game_map.is_ghost_node = Mock(return_value=False)
        game.game_map.is_wall = Mock(return_value=True)

        EntityInspector._terrain_descriptions = {
            'wall': {
                'name': 'Security Barrier',
                'description': 'Blocks movement and vision'
            }
        }

        result = EntityInspector.get_entity_at_position(game, Position(10, 10))

        assert result['entity_type'] == 'wall'
        assert result['color'] == Colors.WALL

    def test_shadow_identified(self):
        """Test that shadows are properly identified."""
        game = Mock()
        game.game_map = Mock()
        game.game_map.width = 50
        game.game_map.height = 50
        game.player = Mock()
        game.player.x = 5
        game.player.y = 5
        game.enemy_manager = Mock()
        game.enemy_manager.get_enemy_at_position = Mock(return_value=None)
        game.game_map.get_code_hack = Mock(return_value=None)
        game.game_map.get_exploit_pickup = Mock(return_value=None)
        game.game_map.permanent_upgrades = {}
        game.game_map.story_fragments = {}
        game.game_map.gateway = None
        game.game_map.is_cooling_node = Mock(return_value=False)
        game.game_map.is_cpu_recovery_node = Mock(return_value=False)
        game.game_map.is_ghost_node = Mock(return_value=False)
        game.game_map.is_wall = Mock(return_value=False)
        game.game_map.is_blind_spot = Mock(return_value=True)

        EntityInspector._terrain_descriptions = {
            'blind_spot': {
                'name': 'Shadow Zone',
                'description': 'Reduces enemy vision'
            }
        }

        result = EntityInspector.get_entity_at_position(game, Position(10, 10))

        assert result['entity_type'] == 'blind_spot'
        assert 'Stealth bonus' in result['details']
        assert result['color'] == Colors.BLIND_SPOT_VISIBLE

    def test_floor_default(self):
        """Test that empty floor tiles are default."""
        game = Mock()
        game.game_map = Mock()
        game.game_map.width = 50
        game.game_map.height = 50
        game.player = Mock()
        game.player.x = 5
        game.player.y = 5
        game.enemy_manager = Mock()
        game.enemy_manager.get_enemy_at_position = Mock(return_value=None)
        game.game_map.get_code_hack = Mock(return_value=None)
        game.game_map.get_exploit_pickup = Mock(return_value=None)
        game.game_map.permanent_upgrades = {}
        game.game_map.story_fragments = {}
        game.game_map.gateway = None
        game.game_map.is_cooling_node = Mock(return_value=False)
        game.game_map.is_cpu_recovery_node = Mock(return_value=False)
        game.game_map.is_ghost_node = Mock(return_value=False)
        game.game_map.is_wall = Mock(return_value=False)
        game.game_map.is_blind_spot = Mock(return_value=False)

        EntityInspector._terrain_descriptions = {
            'floor': {
                'name': 'Data Corridor',
                'description': 'Open network pathway'
            }
        }

        result = EntityInspector.get_entity_at_position(game, Position(10, 10))

        assert result['entity_type'] == 'floor'
        assert result['color'] == Colors.FLOOR


class TestTerrainDescriptionLoading:
    """Test terrain description loading from JSON config."""

    def test_terrain_descriptions_loaded_from_config(self):
        """Test that terrain descriptions are loaded from game_rules.json."""
        mock_config = {
            'terrain_descriptions': {
                'wall': {
                    'name': 'Test Wall',
                    'description': 'Test wall description'
                }
            }
        }

        with patch('game_inspection.DataLoader.load_config', return_value=mock_config):
            # Reset cache
            EntityInspector._terrain_descriptions = None

            # Trigger loading
            EntityInspector._load_terrain_descriptions()

            assert EntityInspector._terrain_descriptions is not None
            assert 'wall' in EntityInspector._terrain_descriptions
            assert EntityInspector._terrain_descriptions['wall']['name'] == 'Test Wall'

    def test_terrain_descriptions_cached(self):
        """Test that terrain descriptions are cached after first load."""
        mock_config = {
            'terrain_descriptions': {
                'test': {'name': 'Test'}
            }
        }

        with patch('game_inspection.DataLoader.load_config', return_value=mock_config) as mock_load:
            # Reset cache
            EntityInspector._terrain_descriptions = None

            # Load twice
            EntityInspector._load_terrain_descriptions()
            EntityInspector._load_terrain_descriptions()

            # Should only call load_config once (cached)
            assert mock_load.call_count == 1


class TestInfoPanelRendering:
    """Test info panel text rendering and truncation behavior."""

    def test_long_exploit_descriptions_dont_trigger_truncation(self):
        """Verify that properly wrapped exploit descriptions don't get truncated with '...'."""
        from game_info_panel import InfoProvider
        from game_data import GameData

        # Use actual exploit with long description from game data
        game = Mock()
        game.player = Mock()
        game.player.temporary_effects = {'exploit_efficiency_turns': 0}

        # Test all real exploits to ensure none trigger truncation
        for exploit_key, exploit_def in GameData.EXPLOITS.items():
            result = InfoProvider._format_exploit_info(game, exploit_def)

            # Verify no line contains "..." (truncation marker)
            for line in result['lines']:
                assert '...' not in line['text'], \
                    f"Exploit '{exploit_key}' line was truncated: '{line['text']}'"

            # Verify description words are preserved (not cut off mid-word)
            desc_lines = [line['text'] for line in result['lines'] if line['color'] == Colors.LIGHT_GRAY]
            all_desc_text = ' '.join(desc_lines)

            # Check that major words from description appear somewhere
            for word in exploit_def.description.split():
                if len(word) > 3:  # Skip short words like "to", "the", etc.
                    assert word in all_desc_text, \
                        f"Exploit '{exploit_key}' lost word '{word}' in wrapping"

    def test_long_entity_descriptions_dont_trigger_truncation(self):
        """Verify that entity descriptions with details don't get truncated."""
        from game_info_panel import InfoProvider

        game = Mock()

        # Create entity info with long description and details
        entity_info = {
            'name': 'Test Enemy',
            'description': 'This is a very long description that should wrap across multiple lines without triggering the safety truncation mechanism',
            'entity_type': 'enemy',
            'details': 'State: Hostile | CPU: 250/250\nVision: 8 | Damage: 45\nBehavior: Relentless pursuer',
            'color': Colors.RED
        }

        result = InfoProvider._format_entity_info(game, entity_info)

        # Verify no line contains "..." (truncation marker)
        for line in result['lines']:
            assert '...' not in line['text'], f"Line was truncated: '{line['text']}'"

        # Verify all detail lines appear
        all_text = ' '.join(line['text'] for line in result['lines'])
        assert 'Hostile' in all_text
        assert 'CPU: 250/250' in all_text
        assert 'Relentless pursuer' in all_text

    def test_text_wrapping_respects_panel_width(self):
        """Verify that text wrapping produces lines that fit within panel width."""
        from game_info_panel import InfoProvider

        # Panel width is 24 chars, text should wrap at 22 (24 - 2 for padding)
        max_width = 22

        test_cases = [
            "Short text",
            "This is a medium length text that will wrap",
            "This is a very long text with many words that definitely needs to be wrapped across multiple lines to fit properly"
        ]

        for text in test_cases:
            wrapped = InfoProvider._wrap_text(text, max_width)

            # Verify each wrapped line fits within max_width
            for line in wrapped:
                assert len(line) <= max_width, \
                    f"Wrapped line too long ({len(line)} > {max_width}): '{line}'"

    def test_code_hack_descriptions_dont_trigger_truncation(self):
        """Verify code hack effect descriptions wrap properly."""
        from game_info_panel import InfoProvider

        game = Mock()

        # Test discovered code hack with long description
        entity_info = {
            'name': 'Crimson Code Fragment',
            'description': 'Speed boost: 2 moves per turn for 3 enemy turns allowing faster navigation',
            'entity_type': 'code_hack',
            'details': 'Color: Crimson',
            'color': Colors.RED
        }

        result = InfoProvider._format_code_hack_info(game, entity_info)

        # Verify no truncation
        for line in result['lines']:
            assert '...' not in line['text'], f"Line was truncated: '{line['text']}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
