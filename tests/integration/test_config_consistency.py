"""
Config Consistency Tests

Validates that configuration values are consistent across JSON files:
- No duplicate definitions in multiple files
- Values that should match actually match
- No conflicting or redundant data
- Balance values properly referenced in code

These tests help maintain clean configuration architecture and prevent bugs
from configuration drift or redundancy.
"""

import pytest
import json
from pathlib import Path


class TestConfigRedundancy:
    """Test for duplicate/redundant config values across JSON files."""

    def setup_method(self):
        """Load all config files."""
        self.game_config = self._load_json('game_rules.json')
        self.game_data = self._load_json('game_content.json')
        self.story_content = self._load_json('story_content.json')

    def _load_json(self, filename):
        """Load a JSON file from project root."""
        path = Path(__file__).parent.parent.parent / filename
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_no_duplicate_balance_values(self):
        """Test that balance values are not duplicated between config files."""
        # CRITICAL: cpu_restore_min/max appears in BOTH files - this is redundant!
        game_config_balance = self.game_config.get('balance', {})
        game_data_balance = self.game_data.get('balance', {})

        # Find overlapping keys
        config_keys = set(game_config_balance.keys())
        data_keys = set(game_data_balance.keys())
        duplicates = config_keys.intersection(data_keys)

        # Report duplicates with values
        duplicate_details = {}
        for key in duplicates:
            if key != 'ai_behavior':  # ai_behavior is intentionally in both (nested structure)
                config_value = game_config_balance[key]
                data_value = game_data_balance[key]
                duplicate_details[key] = {
                    'game_config': config_value,
                    'game_data': data_value
                }

        # Assert no duplicates (except ai_behavior which has nested structure)
        assert len(duplicate_details) == 0, (
            f"Found duplicate balance values in both game_rules.json and game_content.json:\n"
            f"{json.dumps(duplicate_details, indent=2)}\n"
            f"These values should exist in only ONE file to maintain single source of truth."
        )

    def test_ai_behavior_values_consistent(self):
        """Test that ai_behavior values match between files if duplicated."""
        config_ai = self.game_config.get('balance', {}).get('ai_behavior', {})
        data_ai = self.game_data.get('balance', {}).get('ai_behavior', {})

        # If both exist, they should match
        if config_ai and data_ai:
            for key in config_ai:
                if key in data_ai:
                    assert config_ai[key] == data_ai[key], (
                        f"AI behavior value '{key}' differs:\n"
                        f"  game_rules.json: {config_ai[key]}\n"
                        f"  game_content.json: {data_ai[key]}\n"
                        f"These should match if duplicated, or exist in only one file."
                    )

    def test_no_duplicate_gameplay_settings(self):
        """Test that gameplay settings are not duplicated."""
        gameplay_config = self.game_config.get('gameplay', {})

        # Check if any gameplay values appear elsewhere
        # For example, max_heat, max_trace_level should only be in gameplay section
        duplicates_found = []

        # Check if balance section has values that should be in gameplay
        balance = self.game_config.get('balance', {})

        # These should ONLY be in gameplay, not balance
        gameplay_only_keys = ['max_heat', 'max_trace_level', 'default_player_cpu', 'default_player_ram']

        for key in gameplay_only_keys:
            if key in balance:
                duplicates_found.append(f"{key} found in both gameplay and balance")

        assert len(duplicates_found) == 0, (
            f"Found settings in wrong sections:\n" + "\n".join(duplicates_found)
        )

    def test_metadata_versions_consistent(self):
        """Test that version numbers are consistent across config files."""
        config_version = self.game_config.get('metadata', {}).get('version')
        data_version = self.game_data.get('metadata', {}).get('version')

        if config_version and data_version:
            assert config_version == data_version, (
                f"Version mismatch:\n"
                f"  game_rules.json: {config_version}\n"
                f"  game_content.json: {data_version}\n"
                f"All config files should have matching versions."
            )


class TestConfigCompleteness:
    """Test that config files contain all required sections."""

    def setup_method(self):
        """Load all config files."""
        self.game_config = self._load_json('game_rules.json')
        self.game_data = self._load_json('game_content.json')

    def _load_json(self, filename):
        """Load a JSON file from project root."""
        path = Path(__file__).parent.parent.parent / filename
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_game_config_has_required_sections(self):
        """Test that game_rules.json has all required top-level sections."""
        required_sections = [
            'display',
            'ui',
            'gameplay',
            'audio',
            'room_generation',
            'balance',
            'colors',
            'message_types',
            'symbols',
            'characters',
            'welcome_messages',
            'metadata'
        ]

        missing = [s for s in required_sections if s not in self.game_config]

        assert len(missing) == 0, (
            f"game_rules.json is missing required sections: {missing}"
        )

    def test_game_data_has_required_sections(self):
        """Test that game_content.json has all required top-level sections."""
        required_sections = [
            'enemy_types',
            'exploits',
            'upgrades',
            'network_configs',
            'difficulty_multipliers',
            'metadata'
        ]

        missing = [s for s in required_sections if s not in self.game_data]

        assert len(missing) == 0, (
            f"game_content.json is missing required sections: {missing}"
        )

    def test_all_enemies_have_required_fields(self):
        """Test that all enemy types have required fields."""
        required_fields = ['symbol', 'cpu', 'vision', 'movement', 'name', 'damage', 'description']

        enemy_types = self.game_data.get('enemy_types', {})

        for enemy_name, enemy_data in enemy_types.items():
            missing = [f for f in required_fields if f not in enemy_data]
            assert len(missing) == 0, (
                f"Enemy type '{enemy_name}' is missing fields: {missing}"
            )

    def test_all_exploits_have_required_fields(self):
        """Test that all exploits have required fields."""
        required_fields = ['name', 'ram', 'heat', 'range', 'category', 'damage', 'targeting', 'description']

        exploits = self.game_data.get('exploits', {})

        for exploit_id, exploit_data in exploits.items():
            missing = [f for f in required_fields if f not in exploit_data]
            assert len(missing) == 0, (
                f"Exploit '{exploit_id}' is missing fields: {missing}"
            )

    def test_all_network_configs_have_required_fields(self):
        """Test that all network configurations have required fields."""
        required_fields = [
            'enemies', 'shadow_coverage', 'name', 'background_trace',
            'trace_alert_to_hostile', 'trace_continuous_hostile',
            'cooling_nodes', 'cpu_nodes', 'ghost_nodes',
            'code_hacks', 'exploit_pickups', 'permanent_upgrades'
        ]

        networks = self.game_data.get('network_configs', {})

        for level, network_data in networks.items():
            missing = [f for f in required_fields if f not in network_data]
            assert len(missing) == 0, (
                f"Network config level '{level}' is missing fields: {missing}"
            )


class TestConfigValueUsage:
    """Test that config values are actually used in the codebase."""

    def setup_method(self):
        """Load config files."""
        self.game_config = self._load_json('game_rules.json')
        self.game_data = self._load_json('game_content.json')

    def _load_json(self, filename):
        """Load a JSON file from project root."""
        path = Path(__file__).parent.parent.parent / filename
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_cpu_restore_values_exist(self):
        """Test that cpu_restore_min/max values exist (used by code hacks)."""
        # These values should exist in ONE file (currently duplicated - see redundancy test)
        config_balance = self.game_config.get('balance', {})
        data_balance = self.game_data.get('balance', {})

        # At least ONE file should have these values
        has_in_config = 'cpu_restore_min' in config_balance and 'cpu_restore_max' in config_balance
        has_in_data = 'cpu_restore_min' in data_balance and 'cpu_restore_max' in data_balance

        assert has_in_config or has_in_data, (
            "cpu_restore_min/max not found in any config file. "
            "These are required for restore_cpu code hack."
        )

    def test_heat_reduction_values_exist(self):
        """Test that heat reduction values exist for various game mechanics."""
        balance = self.game_config.get('balance', {})

        required_heat_values = [
            'heat_reduction_normal',      # Passive cooling
            'heat_reduction_boosted',     # Cooling boost effect
            'heat_reduction_instant',     # Code hack effect
        ]

        missing = [v for v in required_heat_values if v not in balance]

        assert len(missing) == 0, (
            f"Missing required heat reduction values in game_rules.json balance: {missing}"
        )

    def test_trace_management_values_exist(self):
        """Test that trace management values exist."""
        balance = self.game_config.get('balance', {})

        required_trace_values = [
            'trace_increase_interval',     # How often trace increases
            'trace_increase_amount',       # How much trace increases
            'trace_reduction_code_hack',   # Code hack reduction amount
            'ghost_node_trace_reduction_percent',  # Ghost node effect
        ]

        missing = [v for v in required_trace_values if v not in balance]

        assert len(missing) == 0, (
            f"Missing required trace values in game_rules.json balance: {missing}"
        )

    def test_enemy_ai_values_exist(self):
        """Test that enemy AI behavior values exist."""
        balance = self.game_config.get('balance', {})

        required_ai_values = [
            'enemy_memory_turns',           # How long enemies remember player
            'patrol_stuck_threshold',       # When patrol route resets
            'max_movement_queue_size',      # Movement queue limit
            'pathfinding_timeout_attempts', # Pathfinding safety limit
        ]

        missing = [v for v in required_ai_values if v not in balance]

        assert len(missing) == 0, (
            f"Missing required AI values in game_rules.json balance: {missing}"
        )

    def test_vision_system_values_exist(self):
        """Test that vision system values exist."""
        balance = self.game_config.get('balance', {})

        required_vision_values = [
            'enhanced_vision_bonus',         # Range increase from enhanced vision
            'shadow_vision_reduction_factor', # Vision penalty in shadows
            'adjacent_distance_threshold',    # Adjacency threshold for detection
        ]

        missing = [v for v in required_vision_values if v not in balance]

        assert len(missing) == 0, (
            f"Missing required vision values in game_rules.json balance: {missing}"
        )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
