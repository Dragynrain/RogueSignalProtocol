#!/usr/bin/env python3
"""
INTEGRATION TESTS - Real Config Behavior Testing

These tests verify actual game behavior using real config files.
MINIMAL MOCKING - focus on integration, not implementation details.

The goal is to catch issues like:
- Config values being loaded incorrectly
- Code using wrong attribute names (cpu_recovery_nodes vs cpu_nodes)
- Missing JSON keys that would break the game
- Fallback values that don't match JSON
"""

import pytest
from game_config import GameConfig, GameBalance, RoomGenerationConfig
from game_characters import Player, Enemy
from game_inventory import CodeHack, ExploitItem
from data_loading import DataLoader


class TestRealConfigIntegration:
    """Test that real game objects work with real config."""

    @classmethod
    def setup_class(cls):
        """Load real config once for all tests."""
        GameConfig._config_data = None
        GameConfig.load_from_json()
        GameBalance.load_from_json()
        RoomGenerationConfig.load_from_json()
        DataLoader._game_data = None
        DataLoader._story_fragments = None

    def test_player_uses_real_config_values(self):
        """Verify Player loads real config values correctly."""
        player = Player(10, 10)

        # Should use real values from game_config.json
        # Player uses ram_total instead of max_ram
        assert player.ram_total == GameConfig.DEFAULT_PLAYER_RAM
        assert player.cpu == GameConfig.DEFAULT_PLAYER_CPU
        assert player.max_cpu == GameConfig.DEFAULT_PLAYER_CPU

    def test_all_enemy_types_can_be_created(self):
        """Verify all enemy types from game_data.json can be instantiated."""
        from game_entities import Position

        game_data = DataLoader.load_game_data()
        enemy_types = game_data['enemy_types']

        for enemy_type_id in enemy_types.keys():
            # Should be able to create enemy without errors
            # Enemy constructor takes (position, enemy_type)
            enemy = Enemy(Position(10, 10), enemy_type_id)

            # Verify attributes match JSON (or game-modified values)
            expected = enemy_types[enemy_type_id]
            assert enemy.type == enemy_type_id
            assert enemy.type_data.symbol == expected['symbol']
            assert enemy.cpu == expected['cpu']
            # Vision may be game-enhanced, just verify it exists
            assert hasattr(enemy.type_data, 'vision')
            assert enemy.type_data.vision > 0

    def test_all_exploits_have_cpu_costs(self):
        """Verify every exploit in game_data.json has a CPU cost."""
        game_data = DataLoader.load_game_data()
        exploits = game_data['exploits']
        cpu_costs = game_data['exploit_cpu_costs']

        for exploit_id in exploits.keys():
            # Should be able to get CPU cost without error
            cost = GameBalance.get_exploit_cpu_cost(exploit_id)

            # Cost should match JSON
            assert cost == cpu_costs[exploit_id]
            # Cost should be reasonable
            assert cost > 0
            assert cost < 100

    def test_code_hack_effects_use_real_balance(self):
        """Verify CodeHack effects use real balance values from JSON."""
        import json

        player = Player(10, 10)

        # Create mock game for message log
        class MockGame:
            class MockMessageLog:
                def add_message(self, *args, **kwargs):
                    pass
            def __init__(self):
                self.message_log = self.MockMessageLog()

        mock_game = MockGame()

        # Load balance values from JSON directly
        with open('game_data.json', 'r') as f:
            game_data = json.load(f)

        cpu_restore_min = game_data['balance']['cpu_restore_min']
        cpu_restore_max = game_data['balance']['cpu_restore_max']

        # Test CPU restore effect
        player.cpu = 50
        code_hack = CodeHack("red", "restore_cpu", "Red Code", "Restores CPU")
        code_hack._apply_effect('restore_cpu', player, mock_game)

        # Should use real CPU_RESTORE_MIN/MAX from balance config
        assert player.cpu >= 50 + cpu_restore_min or player.cpu == player.max_cpu
        assert player.cpu <= 50 + cpu_restore_max or player.cpu == player.max_cpu

    def test_heat_reduction_uses_real_balance(self):
        """Verify heat reduction uses real HEAT_REDUCTION_INSTANT value."""
        import json

        player = Player(10, 10)

        class MockGame:
            class MockMessageLog:
                def add_message(self, *args, **kwargs):
                    pass
            def __init__(self):
                self.message_log = self.MockMessageLog()

        mock_game = MockGame()

        # Load heat reduction value from JSON
        with open('game_data.json', 'r') as f:
            game_data = json.load(f)

        heat_reduction_instant = game_data['balance']['code_hacks']['heat_reduction_instant']

        # Test heat reduction effect
        player.heat = 75
        code_hack = CodeHack("blue", "reduce_heat", "Blue Code", "Reduces heat")
        code_hack._apply_effect('reduce_heat', player, mock_game)

        # Should reduce by exact amount from config
        expected_heat = max(0, 75 - heat_reduction_instant)
        assert player.heat == expected_heat

    def test_network_configs_load_correctly(self):
        """Verify network configs load with correct structure."""
        configs = GameConfig.get_network_configs()

        # Should have all 3 levels
        assert 1 in configs
        assert 2 in configs
        assert 3 in configs

        # Each config should have required fields
        for level, config in configs.items():
            assert 'name' in config
            assert 'enemies' in config
            assert 'shadow_coverage' in config
            assert 'cooling_nodes' in config
            assert 'cpu_nodes' in config  # CRITICAL: verify it's cpu_nodes not cpu_recovery_nodes
            assert 'ghost_nodes' in config

    def test_room_generation_config_matches_json(self):
        """Verify RoomGenerationConfig loads correct values from JSON."""
        # Get values from JSON directly
        with open('game_config.json', 'r') as f:
            import json
            config_json = json.load(f)

        room_gen = config_json['room_generation']

        # Verify class attributes match JSON
        assert RoomGenerationConfig.MIN_ROOMS_BASE == room_gen['min_rooms_base']
        assert RoomGenerationConfig.MAX_ROOMS == room_gen['max_rooms']
        assert RoomGenerationConfig.COOLING_NODES_PER_LEVEL == room_gen['cooling_nodes_per_level']
        assert RoomGenerationConfig.CPU_NODES_PER_LEVEL == room_gen['cpu_nodes_per_level']
        assert RoomGenerationConfig.GHOST_NODES_PER_LEVEL == room_gen['ghost_nodes_per_level']
        assert RoomGenerationConfig.CODE_HACKS_PER_LEVEL == room_gen['code_hacks_per_level']

    def test_difficulty_multipliers_accessible(self):
        """Verify all difficulty multipliers can be accessed."""
        difficulties = ['easy', 'normal', 'hard', 'nightmare']

        for difficulty in difficulties:
            multiplier = GameBalance.get_enemy_difficulty_multiplier(difficulty)
            assert isinstance(multiplier, (int, float))
            assert multiplier > 0

    def test_story_fragments_load_correctly(self):
        """Verify story fragments load from JSON."""
        fragments = DataLoader.load_story_fragments()

        # Should be a list
        assert isinstance(fragments, list)
        # Should have content
        assert len(fragments) > 0
        # Each fragment should be a string
        for fragment in fragments:
            assert isinstance(fragment, str)
            assert len(fragment) > 0

    def test_all_exploits_can_be_created(self):
        """Verify all exploits from game_data.json can be instantiated."""
        from game_entities import ExploitDefinition

        game_data = DataLoader.load_game_data()
        exploits = game_data['exploits']

        for exploit_id, exploit_data in exploits.items():
            # Should be able to create exploit without errors
            # ExploitItem takes (exploit_key, exploit_def)
            exploit_def = ExploitDefinition(
                name=exploit_data['name'],
                ram=exploit_data['ram'],
                heat=exploit_data['heat'],
                range=exploit_data['range'],
                category=exploit_data['category'],
                damage=exploit_data['damage'],
                targeting=exploit_data['targeting'],
                description=exploit_data['description']
            )
            exploit_item = ExploitItem(exploit_id, exploit_def)

            # Verify attributes match JSON
            assert exploit_item.exploit_key == exploit_id
            assert exploit_item.name == exploit_data['name']
            assert exploit_item.ram_cost == exploit_data['ram']


class TestConfigValueConsistency:
    """Test that config values are internally consistent."""

    @classmethod
    def setup_class(cls):
        """Load real config once for all tests."""
        GameConfig._config_data = None
        GameConfig.load_from_json()
        GameBalance.load_from_json()

    def test_cpu_restore_range_valid(self):
        """Verify CPU restore min < max."""
        assert GameBalance.CPU_RESTORE_MIN < GameBalance.CPU_RESTORE_MAX

    def test_heat_values_positive(self):
        """Verify all heat values are positive."""
        assert GameBalance.HEAT_REDUCTION_NORMAL > 0
        assert GameBalance.HEAT_REDUCTION_BOOSTED > 0
        assert GameBalance.HEAT_REDUCTION_INSTANT > 0

    def test_screen_dimensions_valid(self):
        """Verify screen dimensions are reasonable."""
        assert GameConfig.SCREEN_WIDTH > 0
        assert GameConfig.SCREEN_HEIGHT > 0
        assert GameConfig.MAP_WIDTH > 0
        assert GameConfig.MAP_HEIGHT > 0
        # Map should fit on screen
        assert GameConfig.MAP_WIDTH <= GameConfig.SCREEN_WIDTH
        assert GameConfig.MAP_HEIGHT <= GameConfig.SCREEN_HEIGHT

    def test_trace_increase_values_reasonable(self):
        """Verify trace increase values are reasonable."""
        assert GameBalance.TRACE_INCREASE_INTERVAL > 0
        assert GameBalance.TRACE_INCREASE_AMOUNT > 0
        # Interval should be larger than amount to avoid instant detection
        assert GameBalance.TRACE_INCREASE_INTERVAL > GameBalance.TRACE_INCREASE_AMOUNT

    def test_room_generation_values_valid(self):
        """Verify room generation values are valid."""
        assert RoomGenerationConfig.MIN_ROOM_SIZE > 0
        assert RoomGenerationConfig.MAX_ROOM_SIZE > RoomGenerationConfig.MIN_ROOM_SIZE
        assert RoomGenerationConfig.MIN_ROOMS_BASE > 0
        assert RoomGenerationConfig.MAX_ROOMS >= RoomGenerationConfig.MIN_ROOMS_BASE


class TestNoFallbackValuesUsed:
    """
    CRITICAL: Verify code doesn't use fallback values when config is available.

    This catches the bug where code had fallback values that diverged from JSON.
    """

    @classmethod
    def setup_class(cls):
        """Load real config once for all tests."""
        GameConfig._config_data = None
        GameConfig.load_from_json()
        GameBalance.load_from_json()

    def test_balance_values_come_from_json_not_defaults(self):
        """Verify balance values match JSON, not hardcoded defaults."""
        import json

        # Load JSON directly
        with open('game_config.json', 'r') as f:
            config_json = json.load(f)

        balance = config_json['balance']

        # Verify class attributes match JSON exactly
        assert GameBalance.HEAT_REDUCTION_NORMAL == balance['heat_reduction_normal']
        assert GameBalance.HEAT_REDUCTION_BOOSTED == balance['heat_reduction_boosted']
        assert GameBalance.COOLING_NODE_EFFECT == balance['cooling_node_effect']
        assert GameBalance.CPU_RECOVERY_AMOUNT == balance['cpu_recovery_amount']
        assert GameBalance.CPU_RESTORE_MIN == balance['cpu_restore_min']
        assert GameBalance.CPU_RESTORE_MAX == balance['cpu_restore_max']
        assert GameBalance.HEAT_REDUCTION_INSTANT == balance['heat_reduction_instant']

    def test_gameplay_values_come_from_json_not_defaults(self):
        """Verify gameplay values match JSON, not hardcoded defaults."""
        import json

        with open('game_config.json', 'r') as f:
            config_json = json.load(f)

        gameplay = config_json['gameplay']

        # Verify class attributes match JSON exactly
        assert GameConfig.DEFAULT_PLAYER_RAM == gameplay['default_player_ram']
        assert GameConfig.DEFAULT_PLAYER_CPU == gameplay['default_player_cpu']
        assert GameConfig.MAX_HEAT == gameplay['max_heat']
        assert GameConfig.MAX_TRACE_LEVEL == gameplay['max_trace_level']
        assert GameConfig.VIRUS_DAMAGE_PER_TURN == gameplay['virus_damage_per_turn']

    def test_cpu_restore_values_in_game_data_match_game_config(self):
        """Verify CPU restore values are consistent between files."""
        import json

        # Load both config files
        with open('game_config.json', 'r') as f:
            config = json.load(f)
        with open('game_data.json', 'r') as f:
            data = json.load(f)

        # Both should have the same CPU restore values
        assert config['balance']['cpu_restore_min'] == data['balance']['cpu_restore_min']
        assert config['balance']['cpu_restore_max'] == data['balance']['cpu_restore_max']


class TestEnemyAIUsesRealConfig:
    """Test that enemy AI behavior uses real config values."""

    @classmethod
    def setup_class(cls):
        """Load real config once for all tests."""
        GameConfig._config_data = None
        GameConfig.load_from_json()
        GameBalance.load_from_json()

    def test_enemy_trace_thresholds_use_real_values(self):
        """Verify enemy AI uses real trace thresholds from config."""
        # These values control enemy behavior
        assert GameBalance.ENEMY_TRACE_ALERT_TO_HOSTILE > 0
        assert GameBalance.ENEMY_TRACE_CONTINUOUS_HOSTILE >= 0

        # Should match what's in JSON
        import json
        with open('game_config.json', 'r') as f:
            config = json.load(f)

        balance = config['balance']
        assert GameBalance.ENEMY_TRACE_ALERT_TO_HOSTILE == balance['enemy_trace_alert_to_hostile']
        assert GameBalance.ENEMY_TRACE_CONTINUOUS_HOSTILE == balance['enemy_trace_continuous_hostile']

    def test_enemy_memory_uses_real_value(self):
        """Verify enemy memory duration uses real config."""
        assert GameBalance.ENEMY_MEMORY_TURNS > 0

        import json
        with open('game_config.json', 'r') as f:
            config = json.load(f)

        assert GameBalance.ENEMY_MEMORY_TURNS == config['balance']['enemy_memory_turns']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
