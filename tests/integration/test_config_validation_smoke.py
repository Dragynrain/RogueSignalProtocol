#!/usr/bin/env python3
"""
CRITICAL SMOKE TESTS - Configuration Validation and JSON Structure

These tests verify that:
1. All required JSON files exist and are valid
2. All required keys are present in config files
3. Config values match what the code expects
4. Real objects can be instantiated with real config

These tests use MINIMAL MOCKING - they test real integration.
"""

import pytest
import json
import os


class TestJSONFilesExist:
    """Verify all required JSON files exist and are valid."""

    def test_game_config_json_exists(self):
        """Verify game_config.json exists."""
        assert os.path.exists('game_config.json'), "Required file game_config.json is missing"

    def test_game_data_json_exists(self):
        """Verify game_data.json exists."""
        assert os.path.exists('game_data.json'), "Required file game_data.json is missing"

    def test_story_content_json_exists(self):
        """Verify story_content.json exists."""
        assert os.path.exists('story_content.json'), "Required file story_content.json is missing"

    def test_game_config_json_is_valid(self):
        """Verify game_config.json contains valid JSON."""
        with open('game_config.json', 'r', encoding='utf-8') as f:
            data = json.load(f)  # Will raise JSONDecodeError if invalid
        assert isinstance(data, dict), "game_config.json should contain a JSON object"

    def test_game_data_json_is_valid(self):
        """Verify game_data.json contains valid JSON."""
        with open('game_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)  # Will raise JSONDecodeError if invalid
        assert isinstance(data, dict), "game_data.json should contain a JSON object"

    def test_story_content_json_is_valid(self):
        """Verify story_content.json contains valid JSON."""
        with open('story_content.json', 'r', encoding='utf-8') as f:
            data = json.load(f)  # Will raise JSONDecodeError if invalid
        assert isinstance(data, dict), "story_content.json should contain a JSON object"


class TestGameConfigStructure:
    """Verify game_config.json has all required sections and keys."""

    @pytest.fixture(scope='class')
    def config_data(self):
        """Load game_config.json once for all tests."""
        with open('game_config.json', 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_has_display_section(self, config_data):
        """Verify display section exists."""
        assert 'display' in config_data, "Missing required 'display' section in game_config.json"

    def test_display_has_required_keys(self, config_data):
        """Verify display section has all required keys."""
        display = config_data['display']
        required_keys = ['screen_width', 'screen_height', 'map_width', 'map_height',
                        'ui_height', 'sidebar_width', 'log_width', 'panel_height']

        for key in required_keys:
            assert key in display, f"Missing required key 'display.{key}' in game_config.json"

    def test_has_ui_section(self, config_data):
        """Verify ui section exists."""
        assert 'ui' in config_data, "Missing required 'ui' section in game_config.json"

    def test_ui_has_required_keys(self, config_data):
        """Verify ui section has all required keys."""
        ui = config_data['ui']
        required_keys = ['message_center_offset_large', 'message_center_offset_medium',
                        'message_center_offset_small', 'message_center_offset_tiny',
                        'message_line_spacing', 'message_button_spacing']

        for key in required_keys:
            assert key in ui, f"Missing required key 'ui.{key}' in game_config.json"

    def test_has_gameplay_section(self, config_data):
        """Verify gameplay section exists."""
        assert 'gameplay' in config_data, "Missing required 'gameplay' section in game_config.json"

    def test_gameplay_has_required_keys(self, config_data):
        """Verify gameplay section has all required keys."""
        gameplay = config_data['gameplay']
        required_keys = ['default_player_ram', 'default_player_cpu', 'max_heat',
                        'max_trace_level', 'trace_reduction_on_level', 'dungeon_seed_range',
                        'default_vision_range', 'max_save_attempts', 'nearby_enemy_alert_radius',
                        'virus_damage_per_turn']

        for key in required_keys:
            assert key in gameplay, f"Missing required key 'gameplay.{key}' in game_config.json"

    def test_has_audio_section(self, config_data):
        """Verify audio section exists."""
        assert 'audio' in config_data, "Missing required 'audio' section in game_config.json"

    def test_audio_has_required_keys(self, config_data):
        """Verify audio section has all required keys."""
        audio = config_data['audio']
        required_keys = ['default_fade_time']

        for key in required_keys:
            assert key in audio, f"Missing required key 'audio.{key}' in game_config.json"

    def test_has_room_generation_section(self, config_data):
        """Verify room_generation section exists."""
        assert 'room_generation' in config_data, "Missing required 'room_generation' section in game_config.json"

    def test_room_generation_has_required_keys(self, config_data):
        """Verify room_generation section has all required keys."""
        room_gen = config_data['room_generation']
        required_keys = ['min_rooms_base', 'room_level_multiplier', 'max_rooms',
                        'max_placement_attempts', 'min_room_size', 'max_room_size',
                        'room_padding', 'cooling_nodes_per_level', 'cpu_nodes_per_level',
                        'ghost_nodes_per_level', 'code_hacks_per_level',
                        'exploit_pickups_per_level', 'permanent_upgrades_per_level']

        for key in required_keys:
            assert key in room_gen, f"Missing required key 'room_generation.{key}' in game_config.json"

    def test_has_balance_section(self, config_data):
        """Verify balance section exists."""
        assert 'balance' in config_data, "Missing required 'balance' section in game_config.json"

    def test_balance_has_required_keys(self, config_data):
        """Verify balance section has all required keys."""
        balance = config_data['balance']
        required_keys = ['heat_reduction_normal', 'heat_reduction_boosted',
                        'trace_increase_interval', 'trace_increase_amount',
                        'cooling_node_effect', 'ghost_node_trace_reduction_percent',
                        'cpu_recovery_amount', 'enemy_elimination_cpu_reward',
                        'cpu_restore_min', 'cpu_restore_max', 'heat_reduction_instant',
                        'adjacent_distance_threshold', 'patrol_stuck_threshold',
                        'pathfinding_timeout_attempts', 'enhanced_vision_bonus',
                        'shadow_vision_reduction_factor', 'enemy_trace_alert_to_hostile',
                        'enemy_trace_continuous_hostile', 'enemy_memory_turns']

        for key in required_keys:
            assert key in balance, f"Missing required key 'balance.{key}' in game_config.json"


class TestGameDataStructure:
    """Verify game_data.json has all required sections and keys."""

    @pytest.fixture(scope='class')
    def game_data(self):
        """Load game_data.json once for all tests."""
        with open('game_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_has_enemy_types_section(self, game_data):
        """Verify enemy_types section exists."""
        assert 'enemy_types' in game_data, "Missing required 'enemy_types' section in game_data.json"

    def test_enemy_types_not_empty(self, game_data):
        """Verify enemy_types section has entries."""
        enemy_types = game_data['enemy_types']
        assert len(enemy_types) > 0, "enemy_types section is empty in game_data.json"

    def test_each_enemy_type_has_required_keys(self, game_data):
        """Verify each enemy type has required attributes."""
        enemy_types = game_data['enemy_types']
        required_keys = ['symbol', 'cpu', 'vision', 'movement', 'name', 'damage', 'description']

        for enemy_id, enemy_data in enemy_types.items():
            for key in required_keys:
                assert key in enemy_data, f"Enemy '{enemy_id}' missing required key '{key}' in game_data.json"

    def test_has_exploits_section(self, game_data):
        """Verify exploits section exists."""
        assert 'exploits' in game_data, "Missing required 'exploits' section in game_data.json"

    def test_exploits_not_empty(self, game_data):
        """Verify exploits section has entries."""
        exploits = game_data['exploits']
        assert len(exploits) > 0, "exploits section is empty in game_data.json"

    def test_each_exploit_has_required_keys(self, game_data):
        """Verify each exploit has required attributes."""
        exploits = game_data['exploits']
        required_keys = ['name', 'ram', 'heat', 'range', 'category', 'damage', 'targeting', 'description']

        for exploit_id, exploit_data in exploits.items():
            for key in required_keys:
                assert key in exploit_data, f"Exploit '{exploit_id}' missing required key '{key}' in game_data.json"

    def test_has_exploit_cpu_costs_section(self, game_data):
        """Verify exploit_cpu_costs section exists."""
        assert 'exploit_cpu_costs' in game_data, "Missing required 'exploit_cpu_costs' section in game_data.json"

    def test_exploit_cpu_costs_match_exploits(self, game_data):
        """Verify every exploit has a CPU cost defined."""
        exploits = game_data['exploits']
        cpu_costs = game_data['exploit_cpu_costs']

        for exploit_id in exploits.keys():
            assert exploit_id in cpu_costs, f"Exploit '{exploit_id}' missing from exploit_cpu_costs in game_data.json"

    def test_has_upgrades_section(self, game_data):
        """Verify upgrades section exists."""
        assert 'upgrades' in game_data, "Missing required 'upgrades' section in game_data.json"

    def test_upgrades_not_empty(self, game_data):
        """Verify upgrades section has entries."""
        upgrades = game_data['upgrades']
        assert len(upgrades) > 0, "upgrades section is empty in game_data.json"

    def test_has_network_configs_section(self, game_data):
        """Verify network_configs section exists."""
        assert 'network_configs' in game_data, "Missing required 'network_configs' section in game_data.json"

    def test_network_configs_has_all_levels(self, game_data):
        """Verify network configs exist for all 3 levels."""
        network_configs = game_data['network_configs']

        for level in ['1', '2', '3']:
            assert level in network_configs, f"Missing network config for level {level} in game_data.json"

    def test_each_network_config_has_required_keys(self, game_data):
        """Verify each network config has required attributes."""
        network_configs = game_data['network_configs']
        required_keys = ['enemies', 'shadow_coverage', 'name', 'background_trace',
                        'trace_alert_to_hostile', 'trace_continuous_hostile',
                        'cooling_nodes', 'cpu_nodes', 'ghost_nodes', 'code_hacks',
                        'exploit_pickups', 'permanent_upgrades']

        for level, config in network_configs.items():
            for key in required_keys:
                assert key in config, f"Network config level {level} missing required key '{key}' in game_data.json"

    def test_has_difficulty_multipliers_section(self, game_data):
        """Verify difficulty_multipliers section exists."""
        assert 'difficulty_multipliers' in game_data, "Missing required 'difficulty_multipliers' section in game_data.json"

    def test_difficulty_multipliers_has_all_levels(self, game_data):
        """Verify difficulty multipliers exist for all difficulty levels."""
        multipliers = game_data['difficulty_multipliers']

        for difficulty in ['easy', 'normal', 'hard', 'nightmare']:
            assert difficulty in multipliers, f"Missing difficulty multiplier for '{difficulty}' in game_data.json"

    def test_has_balance_section(self, game_data):
        """Verify balance section exists in game_data.json."""
        assert 'balance' in game_data, "Missing required 'balance' section in game_data.json"

    def test_balance_has_ai_behavior(self, game_data):
        """Verify balance.ai_behavior section exists."""
        balance = game_data['balance']
        assert 'ai_behavior' in balance, "Missing required 'balance.ai_behavior' section in game_data.json"

    def test_balance_has_cpu_restore_values(self, game_data):
        """Verify balance section exists (cpu_restore values moved to game_config.json)."""
        balance = game_data['balance']
        # NOTE: cpu_restore_min/max moved to game_config.json (single source of truth)
        # This test now just verifies the balance section exists
        assert 'ai_behavior' in balance or 'code_hacks' in balance, \
            "Balance section should have ai_behavior or code_hacks subsections"

    def test_balance_has_code_hacks_section(self, game_data):
        """Verify balance.code_hacks section exists."""
        balance = game_data['balance']
        assert 'code_hacks' in balance, "Missing required 'balance.code_hacks' section in game_data.json"


class TestStoryContentStructure:
    """Verify story_content.json has required structure."""

    @pytest.fixture(scope='class')
    def story_data(self):
        """Load story_content.json once for all tests."""
        with open('story_content.json', 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_has_fragments_key(self, story_data):
        """Verify fragments key exists."""
        assert 'fragments' in story_data, "Missing required 'fragments' key in story_content.json"

    def test_fragments_is_list(self, story_data):
        """Verify fragments is a list."""
        assert isinstance(story_data['fragments'], list), "fragments should be a list in story_content.json"

    def test_fragments_not_empty(self, story_data):
        """Verify fragments list is not empty."""
        assert len(story_data['fragments']) > 0, "fragments list is empty in story_content.json"


class TestConfigRealObjectInstantiation:
    """
    CRITICAL SMOKE TESTS - Instantiate real objects with real config.

    These tests verify that real game objects can be created using real config files.
    NO MOCKING - this catches real integration issues.
    """

    def test_game_config_loads_successfully(self):
        """Verify GameConfig can load from real JSON file."""
        from game_config import GameConfig

        # Force reload to ensure fresh load
        GameConfig._config_data = None
        GameConfig.load_from_json()

        # Verify some values loaded correctly
        assert GameConfig.SCREEN_WIDTH > 0
        assert GameConfig.SCREEN_HEIGHT > 0
        assert GameConfig.DEFAULT_PLAYER_RAM > 0
        assert GameConfig.DEFAULT_PLAYER_CPU > 0

    def test_game_balance_loads_successfully(self):
        """Verify GameBalance can load from real JSON file."""
        from game_config import GameBalance, GameConfig

        # Ensure GameConfig is loaded first
        GameConfig._config_data = None
        GameConfig.load_from_json()

        # Load GameBalance
        GameBalance.load_from_json()

        # Verify values loaded correctly
        assert GameBalance.HEAT_REDUCTION_NORMAL > 0
        assert GameBalance.CPU_RESTORE_MIN > 0
        assert GameBalance.CPU_RESTORE_MAX > GameBalance.CPU_RESTORE_MIN
        assert GameBalance.HEAT_REDUCTION_INSTANT > 0

    def test_room_generation_config_loads_successfully(self):
        """Verify RoomGenerationConfig can load from real JSON file."""
        from game_config import RoomGenerationConfig, GameConfig

        # Ensure GameConfig is loaded first
        GameConfig._config_data = None
        GameConfig.load_from_json()

        # Load RoomGenerationConfig
        RoomGenerationConfig.load_from_json()

        # Verify values loaded correctly
        assert RoomGenerationConfig.MIN_ROOMS_BASE > 0
        assert RoomGenerationConfig.MAX_ROOMS > 0
        assert RoomGenerationConfig.CPU_NODES_PER_LEVEL >= 0
        assert RoomGenerationConfig.COOLING_NODES_PER_LEVEL >= 0

    def test_data_loader_loads_game_data_successfully(self):
        """Verify DataLoader can load game_data.json."""
        from data_loading import DataLoader

        # Clear cache to force fresh load
        DataLoader._game_data = None

        game_data = DataLoader.load_game_data()

        # Verify structure
        assert 'enemy_types' in game_data
        assert 'exploits' in game_data
        assert 'exploit_cpu_costs' in game_data
        assert 'network_configs' in game_data

    def test_data_loader_loads_story_fragments_successfully(self):
        """Verify DataLoader can load story_content.json."""
        from data_loading import DataLoader

        # Clear cache to force fresh load
        DataLoader._story_fragments = None

        fragments = DataLoader.load_story_fragments()

        # Verify structure
        assert isinstance(fragments, list)
        assert len(fragments) > 0

    def test_player_creation_with_real_config(self):
        """Verify Player can be created with real config values."""
        from game_characters import Player
        from game_config import GameConfig
        from game_entities import Position

        # Ensure config is loaded
        GameConfig._config_data = None
        GameConfig.load_from_json()

        # Create player - should use real config values
        player = Player(10, 10)

        # Verify player was created successfully
        assert player is not None
        assert player.position == Position(10, 10)
        assert player.ram_total > 0  # Player uses ram_total not max_ram
        assert player.cpu > 0

    def test_enemy_creation_with_real_config(self):
        """Verify Enemy can be created with real config data."""
        from game_characters import Enemy
        from game_entities import Position

        # Create enemy with real enemy type from JSON
        # Enemy constructor takes (position, enemy_type)
        enemy = Enemy(Position(15, 15), "scanner")

        # Verify enemy was created successfully
        assert enemy is not None
        assert enemy.position == Position(15, 15)
        assert enemy.type == "scanner"
        assert enemy.cpu > 0

    def test_code_hack_with_real_balance_values(self):
        """Verify CodeHack uses real balance values from JSON."""
        from game_inventory import CodeHack
        from game_config import GameConfig, GameBalance
        from game_characters import Player

        # Ensure config is loaded
        GameConfig._config_data = None
        GameConfig.load_from_json()
        GameBalance.load_from_json()  # CRITICAL: Load balance config too

        # Get cpu_restore_min from GameBalance (now in game_config.json)
        cpu_restore_min = GameBalance.CPU_RESTORE_MIN

        # Create code hack
        code_hack = CodeHack("red", "restore_cpu", "Red Code", "Restores CPU")

        # Create player with low CPU
        player = Player(10, 10)
        player.cpu = 50

        # Create mock game object for message log
        class MockGame:
            class MockMessageLog:
                def add_message(self, *args, **kwargs):
                    pass

            def __init__(self):
                self.message_log = self.MockMessageLog()

        mock_game = MockGame()

        # Apply effect - should use real balance values
        initial_cpu = player.cpu
        code_hack._apply_effect('restore_cpu', player, mock_game)

        # Verify CPU was restored using real values
        assert player.cpu > initial_cpu
        assert player.cpu >= initial_cpu + cpu_restore_min or player.cpu == player.max_cpu

    def test_exploit_cpu_cost_lookup(self):
        """Verify exploit CPU costs can be looked up from real data."""
        from game_config import GameBalance

        # Test a few known exploits
        exploits_to_test = ['shadow_step', 'buffer_overflow', 'threat_scan']

        for exploit_name in exploits_to_test:
            cost = GameBalance.get_exploit_cpu_cost(exploit_name)
            assert isinstance(cost, int), f"CPU cost for {exploit_name} should be an integer"
            assert cost > 0, f"CPU cost for {exploit_name} should be positive"


class TestConfigValueConsistency:
    """Verify config values are consistent and reasonable."""

    @pytest.fixture(scope='class')
    def config_data(self):
        """Load game_config.json once for all tests."""
        with open('game_config.json', 'r', encoding='utf-8') as f:
            return json.load(f)

    @pytest.fixture(scope='class')
    def game_data(self):
        """Load game_data.json once for all tests."""
        with open('game_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_cpu_restore_min_less_than_max(self, config_data):
        """Verify CPU restore min is less than max (now in game_config.json)."""
        balance = config_data['balance']
        assert balance['cpu_restore_min'] < balance['cpu_restore_max'], \
            "cpu_restore_min should be less than cpu_restore_max"

    def test_screen_dimensions_positive(self, config_data):
        """Verify screen dimensions are positive."""
        display = config_data['display']
        assert display['screen_width'] > 0
        assert display['screen_height'] > 0
        assert display['map_width'] > 0
        assert display['map_height'] > 0

    def test_gameplay_values_positive(self, config_data):
        """Verify gameplay values are positive."""
        gameplay = config_data['gameplay']
        assert gameplay['default_player_ram'] > 0
        assert gameplay['default_player_cpu'] > 0
        assert gameplay['max_heat'] > 0
        assert gameplay['max_trace_level'] > 0

    def test_balance_values_positive(self, config_data):
        """Verify balance values are positive."""
        balance = config_data['balance']
        assert balance['heat_reduction_normal'] > 0
        assert balance['heat_reduction_boosted'] > 0
        assert balance['cooling_node_effect'] > 0
        assert balance['cpu_recovery_amount'] > 0

    def test_difficulty_multipliers_reasonable(self, game_data):
        """Verify difficulty multipliers are in reasonable range."""
        multipliers = game_data['difficulty_multipliers']

        # Easy should be < 1.0, normal = 1.0, hard/nightmare > 1.0
        assert multipliers['easy'] < 1.0
        assert multipliers['normal'] == 1.0
        assert multipliers['hard'] > 1.0
        assert multipliers['nightmare'] > multipliers['hard']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
