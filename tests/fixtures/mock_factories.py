#!/usr/bin/env python3
"""
Mock factories for creating test objects with realistic data.
Provides standardized mock objects for testing across the RogueSignalProtocol test suite.
"""

import random
from unittest.mock import Mock, MagicMock
from typing import List, Dict, Any, Optional
from game_entities import Position, EnemyState, EnemyMovement, TargetingMode
from game_entities import EnemyTypeDefinition, ExploitDefinition, UpgradeDefinition
from game_data import GameData
from game_characters import Player, Enemy


class MockPlayerFactory:
    """Factory for creating mock Player objects with realistic data."""
    
    @staticmethod
    def create_basic_player(x: int = 10, y: int = 10) -> Mock:
        """Create a basic mock player with standard stats."""
        mock_player = Mock()
        mock_player.position = Position(x, y)
        mock_player.x = x
        mock_player.y = y
        mock_player.cpu = 100
        mock_player.max_cpu = 100
        mock_player.heat = 0
        mock_player.max_heat = 100
        mock_player.detection = 0
        mock_player.ram_total = 8
        mock_player.ram_used = 0
        mock_player.base_vision_range = 15
        
        # Temporary effects
        mock_player.temporary_effects = {
            'data_mimic_turns': 0,
            'speed_boost_turns': 0,
            'movement_slowed_turns': 0,
            'enhanced_vision_turns': 0,
            'exploit_efficiency_turns': 0,
            'virus_turns': 0
        }
        mock_player.speed_moves_remaining = 0
        
        # Mock methods
        mock_player.is_invisible.return_value = False
        mock_player.get_vision_range.return_value = 15
        mock_player.can_see_through_walls.return_value = False
        mock_player.take_damage.return_value = 0
        mock_player.move.return_value = True
        mock_player.update_effects.return_value = None
        
        return mock_player
    
    @staticmethod
    def create_damaged_player(x: int = 10, y: int = 10, cpu: int = 50) -> Mock:
        """Create a mock player with reduced CPU."""
        mock_player = MockPlayerFactory.create_basic_player(x, y)
        mock_player.cpu = cpu
        return mock_player
    
    @staticmethod
    def create_invisible_player(x: int = 10, y: int = 10) -> Mock:
        """Create a mock player with invisibility active."""
        mock_player = MockPlayerFactory.create_basic_player(x, y)
        mock_player.temporary_effects['data_mimic_turns'] = 5
        mock_player.is_invisible.return_value = True
        return mock_player
    
    @staticmethod
    def create_enhanced_vision_player(x: int = 10, y: int = 10) -> Mock:
        """Create a mock player with enhanced vision active."""
        mock_player = MockPlayerFactory.create_basic_player(x, y)
        mock_player.temporary_effects['enhanced_vision_turns'] = 5
        mock_player.get_vision_range.return_value = 17  # +2 bonus
        mock_player.can_see_through_walls.return_value = True
        return mock_player


class MockEnemyFactory:
    """Factory for creating mock Enemy objects with realistic data."""
    
    @staticmethod
    def create_basic_enemy(enemy_type: str = 'scanner', x: int = 15, y: int = 15) -> Mock:
        """Create a basic mock enemy of specified type."""
        if enemy_type not in GameData.ENEMY_TYPES:
            enemy_type = 'scanner'
        
        type_data = GameData.ENEMY_TYPES[enemy_type]
        
        mock_enemy = Mock()
        mock_enemy.id = random.randint(1, 1000)
        mock_enemy.position = Position(x, y)
        mock_enemy.x = x
        mock_enemy.y = y
        mock_enemy.type = enemy_type
        mock_enemy.type_data = type_data
        mock_enemy.cpu = type_data.cpu
        mock_enemy.max_cpu = type_data.cpu
        mock_enemy.state = EnemyState.UNAWARE
        mock_enemy.alert_timer = 0
        mock_enemy.disabled_turns = 0
        mock_enemy.move_cooldown = 0
        
        # Movement data
        mock_enemy.patrol_points = []
        mock_enemy.patrol_index = 0
        mock_enemy.patrol_stuck_counter = 0
        mock_enemy.last_seen_player = None
        mock_enemy.movement_queue = []
        mock_enemy.last_queue_state = None
        mock_enemy.last_queue_target = None
        mock_enemy.last_target = None
        mock_enemy.original_patrol_index = 0
        
        # Mock methods
        mock_enemy.get_color.return_value = (255, 255, 60)  # Default yellow
        mock_enemy.can_see_player.return_value = False
        mock_enemy.can_attack_player.return_value = False
        mock_enemy.attack_player.return_value = 0
        mock_enemy.take_damage.return_value = False
        mock_enemy.move.return_value = False
        
        return mock_enemy
    
    @staticmethod
    def create_hostile_enemy(enemy_type: str = 'hunter', x: int = 15, y: int = 15) -> Mock:
        """Create a mock enemy in hostile state."""
        mock_enemy = MockEnemyFactory.create_basic_enemy(enemy_type, x, y)
        mock_enemy.state = EnemyState.HOSTILE
        mock_enemy.last_seen_player = Position(10, 10)  # Default player position
        mock_enemy.can_see_player.return_value = True
        mock_enemy.can_attack_player.return_value = True
        mock_enemy.attack_player.return_value = mock_enemy.type_data.damage
        return mock_enemy
    
    @staticmethod
    def create_disabled_enemy(enemy_type: str = 'bot', x: int = 15, y: int = 15, disabled_turns: int = 3) -> Mock:
        """Create a mock enemy that is disabled."""
        mock_enemy = MockEnemyFactory.create_basic_enemy(enemy_type, x, y)
        mock_enemy.disabled_turns = disabled_turns
        mock_enemy.can_see_player.return_value = False
        mock_enemy.can_attack_player.return_value = False
        return mock_enemy
    
    @staticmethod
    def create_patrol_enemy(x: int = 15, y: int = 15, patrol_points: Optional[List[Position]] = None) -> Mock:
        """Create a mock patrol enemy with patrol points."""
        mock_enemy = MockEnemyFactory.create_basic_enemy('patrol', x, y)
        if patrol_points is None:
            patrol_points = [Position(10, 10), Position(20, 20), Position(15, 25)]
        mock_enemy.patrol_points = patrol_points
        mock_enemy.patrol_index = 0
        return mock_enemy
    
    @staticmethod
    def create_admin_enemy(x: int = 25, y: int = 25) -> Mock:
        """Create a mock admin enemy (boss)."""
        mock_enemy = MockEnemyFactory.create_basic_enemy('admin', x, y)
        mock_enemy.state = EnemyState.HOSTILE
        mock_enemy.can_see_player.return_value = True  # Admin can always see player
        mock_enemy.can_attack_player.return_value = True
        mock_enemy.attack_player.return_value = 45  # High damage
        return mock_enemy


class MockGameMapFactory:
    """Factory for creating mock game map objects."""
    
    @staticmethod
    def create_basic_map(width: int = 50, height: int = 50) -> Mock:
        """Create a basic mock game map."""
        mock_map = Mock()
        mock_map.width = width
        mock_map.height = height
        mock_map.is_valid_position.return_value = True
        mock_map.is_shadow.return_value = False
        mock_map.can_see_position.return_value = True
        mock_map.explored_tiles = set()
        mock_map.last_known_enemy_positions = {}
        
        # Special nodes
        mock_map.cooling_nodes = []
        mock_map.cpu_recovery_nodes = []
        mock_map.ghost_nodes = []
        
        return mock_map
    
    @staticmethod
    def create_map_with_shadows(width: int = 50, height: int = 50, shadow_positions: Optional[List[Position]] = None) -> Mock:
        """Create a mock map with shadow zones."""
        mock_map = MockGameMapFactory.create_basic_map(width, height)
        
        if shadow_positions is None:
            shadow_positions = [Position(5, 5), Position(10, 10), Position(15, 15)]
        
        def is_shadow_check(pos):
            return pos in shadow_positions
        
        mock_map.is_shadow.side_effect = is_shadow_check
        return mock_map
    
    @staticmethod
    def create_map_with_obstacles(width: int = 50, height: int = 50, blocked_positions: Optional[List[Position]] = None) -> Mock:
        """Create a mock map with obstacles."""
        mock_map = MockGameMapFactory.create_basic_map(width, height)
        
        if blocked_positions is None:
            blocked_positions = [Position(25, 25), Position(30, 30)]
        
        def is_valid_check(pos):
            return pos not in blocked_positions and 0 <= pos.x < width and 0 <= pos.y < height
        
        mock_map.is_valid_position.side_effect = is_valid_check
        return mock_map


class MockGameFactory:
    """Factory for creating mock game objects."""
    
    @staticmethod
    def create_basic_game() -> Mock:
        """Create a basic mock game object."""
        mock_game = Mock()
        mock_game.player = MockPlayerFactory.create_basic_player()
        mock_game.enemies = []
        mock_game.game_map = MockGameMapFactory.create_basic_map()
        mock_game.level = 1
        mock_game.turn = 1
        mock_game.game_over = False
        
        # Game state
        mock_game.targeting_mode = False
        mock_game.targeting_exploit = None
        mock_game.cursor_position = Position(0, 0)
        mock_game.overclock_confirmation = False
        mock_game.overclock_exploit = None
        
        # Systems
        mock_game.message_log = Mock()
        mock_game.sound_manager = Mock()
        mock_game.game_state = Mock()
        
        # Mock methods
        mock_game._get_enemy_at.return_value = None
        mock_game.maybe_process_turn = Mock()
        
        return mock_game
    
    @staticmethod
    def create_game_with_enemies(enemy_types: List[str], positions: Optional[List[Position]] = None) -> Mock:
        """Create a mock game with specified enemies."""
        mock_game = MockGameFactory.create_basic_game()
        
        if positions is None:
            positions = [Position(15 + i * 5, 15) for i in range(len(enemy_types))]
        
        enemies = []
        for i, enemy_type in enumerate(enemy_types):
            pos = positions[i] if i < len(positions) else Position(15 + i * 5, 15)
            enemy = MockEnemyFactory.create_basic_enemy(enemy_type, pos.x, pos.y)
            enemies.append(enemy)
        
        mock_game.enemies = enemies
        
        def get_enemy_at(position):
            for enemy in enemies:
                if enemy.position.x == position.x and enemy.position.y == position.y:
                    return enemy
            return None
        
        mock_game._get_enemy_at.side_effect = get_enemy_at
        return mock_game


class MockInventoryFactory:
    """Factory for creating mock inventory objects."""
    
    @staticmethod
    def create_basic_inventory_manager() -> Mock:
        """Create a basic mock inventory manager."""
        mock_inventory = Mock()
        mock_inventory.equipped_exploits = []
        mock_inventory.get_ram_usage.return_value = 0
        mock_inventory.add_exploit.return_value = True
        mock_inventory.remove_exploit.return_value = True
        mock_inventory.equip_exploit.return_value = True
        mock_inventory.unequip_exploit.return_value = True
        return mock_inventory
    
    @staticmethod
    def create_inventory_with_exploits(exploit_names: List[str]) -> Mock:
        """Create a mock inventory with specific exploits equipped."""
        mock_inventory = MockInventoryFactory.create_basic_inventory_manager()
        mock_inventory.equipped_exploits = exploit_names
        
        # Calculate RAM usage
        total_ram = 0
        for exploit_name in exploit_names:
            if exploit_name in GameData.EXPLOITS:
                total_ram += GameData.EXPLOITS[exploit_name].ram
        
        mock_inventory.get_ram_usage.return_value = total_ram
        return mock_inventory


class MockExploitFactory:
    """Factory for creating mock exploit objects."""
    
    @staticmethod
    def create_exploit_definition(
        name: str = "Test Exploit",
        ram: int = 2,
        heat: int = 25,
        range: int = 5,
        category: str = "utility",
        damage: int = 0,
        targeting: TargetingMode = TargetingMode.NONE,
        description: str = "Test exploit for testing"
    ) -> ExploitDefinition:
        """Create a custom exploit definition for testing."""
        return ExploitDefinition(
            name=name,
            ram=ram,
            heat=heat,
            range=range,
            category=category,
            damage=damage,
            targeting=targeting,
            description=description
        )
    
    @staticmethod
    def create_offensive_exploit() -> ExploitDefinition:
        """Create a mock offensive exploit."""
        return MockExploitFactory.create_exploit_definition(
            name="Test Attack",
            ram=3,
            heat=35,
            range=6,
            category="combat",
            damage=25,
            targeting=TargetingMode.SINGLE
        )
    
    @staticmethod
    def create_area_exploit() -> ExploitDefinition:
        """Create a mock area effect exploit."""
        return MockExploitFactory.create_exploit_definition(
            name="Test Area",
            ram=4,
            heat=45,
            range=3,
            category="combat",
            damage=20,
            targeting=TargetingMode.AREA
        )


class MockSystemFactory:
    """Factory for creating mock system objects."""
    
    @staticmethod
    def create_mock_sound_manager() -> Mock:
        """Create a mock sound manager."""
        mock_sound = Mock()
        mock_sound.play_sound = Mock()
        mock_sound.play_music = Mock()
        mock_sound.stop_music = Mock()
        mock_sound.set_volume = Mock()
        mock_sound.preload_sounds = Mock()
        return mock_sound
    
    @staticmethod
    def create_mock_message_log() -> Mock:
        """Create a mock message log."""
        mock_log = Mock()
        mock_log.add_message = Mock()
        mock_log.get_messages = Mock(return_value=[])
        mock_log.clear = Mock()
        return mock_log
    
    @staticmethod
    def create_mock_game_state() -> Mock:
        """Create a mock game state."""
        mock_state = Mock()
        mock_state.level = 1
        mock_state.turn = 1
        mock_state.game_over = False
        mock_state.admin_spawned = False
        mock_state.threat_scan_turns = 0
        mock_state.revealed_special_nodes = {}
        return mock_state


class MockTestScenarios:
    """Pre-built test scenarios using the factories."""
    
    @staticmethod
    def combat_scenario() -> Dict[str, Any]:
        """Create a combat test scenario."""
        player = MockPlayerFactory.create_basic_player(10, 10)
        enemies = [
            MockEnemyFactory.create_hostile_enemy('hunter', 11, 10),  # Adjacent
            MockEnemyFactory.create_basic_enemy('scanner', 15, 15)    # Distant
        ]
        game_map = MockGameMapFactory.create_basic_map()
        
        return {
            'player': player,
            'enemies': enemies,
            'game_map': game_map,
            'description': 'Player adjacent to hostile hunter, with distant scanner'
        }
    
    @staticmethod
    def stealth_scenario() -> Dict[str, Any]:
        """Create a stealth test scenario."""
        shadow_positions = [Position(10, 10), Position(15, 15)]
        player = MockPlayerFactory.create_invisible_player(10, 10)  # In shadow, invisible
        enemies = [
            MockEnemyFactory.create_basic_enemy('patrol', 12, 10),   # Nearby
            MockEnemyFactory.create_basic_enemy('scanner', 15, 15)   # In shadow
        ]
        game_map = MockGameMapFactory.create_map_with_shadows(shadow_positions=shadow_positions)
        
        return {
            'player': player,
            'enemies': enemies,
            'game_map': game_map,
            'shadow_positions': shadow_positions,
            'description': 'Invisible player in shadow with nearby enemies'
        }
    
    @staticmethod
    def boss_scenario() -> Dict[str, Any]:
        """Create a boss fight test scenario."""
        player = MockPlayerFactory.create_damaged_player(10, 10, cpu=60)  # Damaged
        enemies = [
            MockEnemyFactory.create_admin_enemy(15, 15),              # Admin boss
            MockEnemyFactory.create_hostile_enemy('hunter', 8, 12),   # Support enemy
            MockEnemyFactory.create_disabled_enemy('bot', 20, 20, 2)  # Disabled enemy
        ]
        game_map = MockGameMapFactory.create_basic_map()
        
        return {
            'player': player,
            'enemies': enemies,
            'game_map': game_map,
            'description': 'Damaged player facing admin boss with support enemies'
        }
    
    @staticmethod
    def exploration_scenario() -> Dict[str, Any]:
        """Create an exploration test scenario."""
        player = MockPlayerFactory.create_enhanced_vision_player(10, 10)
        enemies = [
            MockEnemyFactory.create_patrol_enemy(20, 20),  # Patrolling
            MockEnemyFactory.create_basic_enemy('scanner', 30, 30)  # Stationary
        ]
        game_map = MockGameMapFactory.create_map_with_obstacles()
        
        return {
            'player': player,
            'enemies': enemies,
            'game_map': game_map,
            'description': 'Enhanced vision player exploring map with obstacles'
        }


class MockSaveDataFactory:
    """Factory for creating mock save data for testing persistence systems."""
    
    @staticmethod
    def create_basic_save_data() -> Dict[str, Any]:
        """Create basic save data structure."""
        return {
            "version": "dev",
            "timestamp": 1640995200.0,  # 2022-01-01 00:00:00
            "level": 1,
            "turn": 1,
            "game_over": False,
            "admin_spawned": False,
            "dungeon_seed": 12345,
            "player": {
                "x": 10,
                "y": 10,
                "last_x": 9,
                "last_y": 9,
                "cpu": 50,
                "max_cpu": 100,
                "heat": 30,
                "max_heat": 100,
                "detection": 0,
                "ram_total": 20,
                "speed_moves_remaining": 0,
                "temporary_effects": {},
                "equipped_exploits": ["shadow_step"],
                "max_equipped_exploits": 5,
                "inventory_items": []
            },
            "game_effects": {
                "threat_scan_turns": 0,
                "noise_locations": [],
                "distraction_points": {}
            },
            "map_state": {
                "code_hacks": {},
                "exploit_pickups": {},
                "permanent_upgrades": {},
                "story_fragments": {},
                "gateway": {"x": 45, "y": 25},
                "explored_tiles": [],
                "last_known_enemy_positions": {}
            },
            "enemies": [],
            "enemy_next_id": 1,
            "code_hack_effects": {},
            "discovered_code_effects": {},
            "overclock_confirmation": False,
            "overclock_exploit": None,
            "ui_state": {
                "inventory_selection": 0,
                "lore_viewer_selection": 0
            }
        }
    
    @staticmethod
    def create_complex_save_data() -> Dict[str, Any]:
        """Create complex save data with multiple systems active."""
        save_data = MockSaveDataFactory.create_basic_save_data()
        save_data.update({
            "level": 3,
            "turn": 45,
            "player": {
                **save_data["player"],
                "cpu": 35,
                "heat": 60,
                "detection": 25,
                "temporary_effects": {"enhanced_vision_turns": 3},
                "equipped_exploits": ["shadow_step", "code_injection"],
                "inventory_items": [
                    {
                        "type": "code_hack",
                        "name": "Red Code",
                        "color": "red",
                        "effect": "restore_cpu",
                        "quantity": 2,
                        "discovered": True
                    }
                ]
            },
            "enemies": [
                {
                    "id": 1,
                    "type": "patrol",
                    "x": 15,
                    "y": 15,
                    "cpu": 40,
                    "state": "alert",
                    "move_cooldown": 0,
                    "disabled_turns": 0,
                    "alert_timer": 2,
                    "patrol_index": 1,
                    "patrol_stuck_counter": 0,
                    "movement_queue": [{"x": 20, "y": 15}],
                    "last_target": None,
                    "last_seen_player": {"x": 12, "y": 12},
                    "patrol_points": [
                        {"x": 15, "y": 15},
                        {"x": 20, "y": 15},
                        {"x": 20, "y": 20},
                        {"x": 15, "y": 20}
                    ]
                }
            ],
            "discovered_code_effects": {
                "red": "restore_cpu",
                "blue": "reduce_heat"
            }
        })
        return save_data
    
    @staticmethod
    def create_corrupted_save_data() -> str:
        """Create intentionally corrupted JSON for testing error handling."""
        return '{"version": "dev", "level": 1, "incomplete": true'  # Missing closing brace
    
    @staticmethod
    def create_empty_save_data() -> str:
        """Create empty save data for testing edge cases."""
        return ""


class MockLevelGeneratorFactory:
    """Factory for creating mock level generator objects."""
    
    @staticmethod
    def create_basic_generator() -> Mock:
        """Create a basic level generator mock."""
        mock_generator = Mock()
        mock_generator.width = 50
        mock_generator.height = 30
        mock_generator.rooms = []
        mock_generator.carve_room = Mock(return_value=True)
        mock_generator.find_room_position = Mock(return_value=(10, 10))
        mock_generator.rooms_overlap = Mock(return_value=False)
        mock_generator.place_special_tiles = Mock()
        mock_generator.generate_map = Mock(return_value=MockGameMapFactory.create_basic_map())
        return mock_generator
    
    @staticmethod
    def create_generator_with_rooms(room_count: int) -> Mock:
        """Create a level generator with specific number of rooms."""
        mock_generator = MockLevelGeneratorFactory.create_basic_generator()
        
        # Create mock rooms
        rooms = []
        for i in range(room_count):
            room = Mock()
            room.x = 5 + (i * 10)
            room.y = 5 + (i * 5)
            room.width = 8
            room.height = 6
            rooms.append(room)
        
        mock_generator.rooms = rooms
        return mock_generator


class MockConfigFactory:
    """Factory for creating mock configuration objects."""
    
    @staticmethod
    def create_test_config() -> Mock:
        """Create a test configuration with realistic values."""
        mock_config = Mock()
        mock_config.MAP_WIDTH = 50
        mock_config.MAP_HEIGHT = 30
        mock_config.MIN_ROOMS = 8
        mock_config.MAX_ROOMS = 15
        mock_config.ROOM_MIN_SIZE = 6
        mock_config.ROOM_MAX_SIZE = 12
        mock_config.ENEMY_BASE_COUNT = 2
        mock_config.ENEMY_SCALING_FACTOR = 0.8
        mock_config.MAX_SAVE_ATTEMPTS = 3
        mock_config.SAVE_RETRY_DELAY = 0.1
        return mock_config