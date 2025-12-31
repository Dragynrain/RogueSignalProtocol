#!/usr/bin/env python3
"""
Configuration Validation and Consistency Tests

CRITICAL SMOKE TESTS + ARCHITECTURE VALIDATION
- Minimal mocking - tests real integration
- Prevents config drift and redundancy
- Verifies real objects can be instantiated with real config

Test Tiers:
1. JSON existence and validity (fail fast)
2. Structure validation (required keys)
3. Cross-file consistency (no duplicates/drift)
4. Value validation (sanity checks)
5. Real object instantiation (integration)
"""

import json
import os
from pathlib import Path

import pytest

# ============================================================================
# TIER 1: FOUNDATIONAL TESTS (Must pass first)
# ============================================================================


class TestJSONFilesExist:
    """Verify all required JSON files exist and are valid."""

    def test_game_config_json_exists(self):
        """Verify game_rules.json exists."""
        assert os.path.exists("game_rules.json"), "Required file game_rules.json is missing"

    def test_game_data_json_exists(self):
        """Verify game_content.json exists."""
        assert os.path.exists("game_content.json"), "Required file game_content.json is missing"

    def test_narrative_content_json_exists(self):
        """Verify narrative_content.json exists."""
        assert os.path.exists(
            "narrative_content.json"
        ), "Required file narrative_content.json is missing"

    def test_game_config_json_is_valid(self):
        """Verify game_rules.json contains valid JSON."""
        with open("game_rules.json", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict), "game_rules.json should contain a JSON object"

    def test_game_data_json_is_valid(self):
        """Verify game_content.json contains valid JSON."""
        with open("game_content.json", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict), "game_content.json should contain a JSON object"

    def test_narrative_content_json_is_valid(self):
        """Verify narrative_content.json contains valid JSON."""
        with open("narrative_content.json", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict), "narrative_content.json should contain a JSON object"


# ============================================================================
# TIER 2: STRUCTURE VALIDATION
# ============================================================================


class TestGameRulesStructure:
    """Verify game_rules.json has all required sections and keys."""

    @pytest.fixture(scope="class")
    def config_data(self):
        """Load game_rules.json once for all tests."""
        with open("game_rules.json", encoding="utf-8") as f:
            return json.load(f)

    def test_has_display_section(self, config_data):
        """Verify display section exists."""
        assert "display" in config_data, "Missing required 'display' section in game_rules.json"

    def test_display_has_required_keys(self, config_data):
        """Verify display section has all required keys."""
        display = config_data["display"]
        required_keys = [
            "screen_width",
            "screen_height",
            "map_width",
            "map_height",
            "ui_height",
            "sidebar_width",
            "log_width",
            "panel_height",
        ]

        for key in required_keys:
            assert key in display, f"Missing required key 'display.{key}' in game_rules.json"

    def test_has_ui_section(self, config_data):
        """Verify ui section exists."""
        assert "ui" in config_data, "Missing required 'ui' section in game_rules.json"

    def test_ui_has_required_keys(self, config_data):
        """Verify ui section has all required keys."""
        ui = config_data["ui"]
        required_keys = [
            "message_center_offset_large",
            "message_center_offset_medium",
            "message_center_offset_small",
            "message_center_offset_tiny",
            "message_line_spacing",
            "message_button_spacing",
        ]

        for key in required_keys:
            assert key in ui, f"Missing required key 'ui.{key}' in game_rules.json"

    def test_has_gameplay_section(self, config_data):
        """Verify gameplay section exists."""
        assert "gameplay" in config_data, "Missing required 'gameplay' section in game_rules.json"

    def test_gameplay_has_required_keys(self, config_data):
        """Verify gameplay section has all required keys."""
        gameplay = config_data["gameplay"]
        required_keys = [
            "default_player_ram",
            "default_player_cpu",
            "max_heat",
            "max_trace_level",
            "trace_reduction_on_level",
            "dungeon_seed_range",
            "default_vision_range",
            "max_save_attempts",
            "nearby_enemy_alert_radius",
            "virus_damage_per_turn",
        ]

        for key in required_keys:
            assert key in gameplay, f"Missing required key 'gameplay.{key}' in game_rules.json"

    def test_has_audio_section(self, config_data):
        """Verify audio section exists."""
        assert "audio" in config_data, "Missing required 'audio' section in game_rules.json"

    def test_audio_has_required_keys(self, config_data):
        """Verify audio section has all required keys."""
        audio = config_data["audio"]
        required_keys = ["default_fade_time"]

        for key in required_keys:
            assert key in audio, f"Missing required key 'audio.{key}' in game_rules.json"

    def test_has_room_generation_section(self, config_data):
        """Verify room_generation section exists."""
        assert (
            "room_generation" in config_data
        ), "Missing required 'room_generation' section in game_rules.json"

    def test_room_generation_has_required_keys(self, config_data):
        """Verify room_generation section has all required keys."""
        room_gen = config_data["room_generation"]
        required_keys = [
            "min_rooms_base",
            "room_level_multiplier",
            "max_rooms",
            "max_placement_attempts",
            "min_room_size",
            "max_room_size",
            "room_padding",
        ]

        for key in required_keys:
            assert (
                key in room_gen
            ), f"Missing required key 'room_generation.{key}' in game_rules.json"

    def test_has_balance_section(self, config_data):
        """Verify balance section exists."""
        assert "balance" in config_data, "Missing required 'balance' section in game_rules.json"

    def test_balance_has_required_keys(self, config_data):
        """Verify balance section has all required keys."""
        balance = config_data["balance"]
        required_keys = [
            "heat_reduction_normal",
            "heat_reduction_boosted",
            "trace_increase_interval",
            "trace_increase_amount",
            "cooling_node_effect",
            "ghost_node_trace_reduction_percent",
            "cpu_recovery_amount",
            "enemy_elimination_cpu_reward",
            "cpu_restore_min",
            "cpu_restore_max",
            "heat_reduction_instant",
            "adjacent_distance_threshold",
            "patrol_stuck_threshold",
            "pathfinding_timeout_attempts",
            "enhanced_vision_bonus",
            "blind_spot_vision_reduction_factor",
            "enemy_memory_turns",
        ]

        for key in required_keys:
            assert key in balance, f"Missing required key 'balance.{key}' in game_rules.json"

        # AI behavior keys are in a subsection
        assert (
            "ai_behavior" in balance
        ), "Missing required 'balance.ai_behavior' subsection in game_rules.json"
        ai_behavior = balance["ai_behavior"]
        ai_keys = ["enemy_trace_alert_to_hostile", "enemy_trace_continuous_hostile"]
        for key in ai_keys:
            assert (
                key in ai_behavior
            ), f"Missing required key 'balance.ai_behavior.{key}' in game_rules.json"


class TestGameContentStructure:
    """Verify game_content.json has all required sections and keys."""

    @pytest.fixture(scope="class")
    def game_data(self):
        """Load game_content.json once for all tests."""
        with open("game_content.json", encoding="utf-8") as f:
            return json.load(f)

    def test_has_enemy_types_section(self, game_data):
        """Verify enemy_types section exists."""
        assert (
            "enemy_types" in game_data
        ), "Missing required 'enemy_types' section in game_content.json"

    def test_enemy_types_not_empty(self, game_data):
        """Verify enemy_types section has entries."""
        enemy_types = game_data["enemy_types"]
        assert len(enemy_types) > 0, "enemy_types section is empty in game_content.json"

    def test_each_enemy_type_has_required_keys(self, game_data):
        """Verify each enemy type has required attributes."""
        enemy_types = game_data["enemy_types"]
        required_keys = ["symbol", "cpu", "vision", "movement", "name", "damage", "description"]

        for enemy_id, enemy_data in enemy_types.items():
            for key in required_keys:
                assert (
                    key in enemy_data
                ), f"Enemy '{enemy_id}' missing required key '{key}' in game_content.json"

    def test_has_exploits_section(self, game_data):
        """Verify exploits section exists."""
        assert "exploits" in game_data, "Missing required 'exploits' section in game_content.json"

    def test_exploits_not_empty(self, game_data):
        """Verify exploits section has entries."""
        exploits = game_data["exploits"]
        assert len(exploits) > 0, "exploits section is empty in game_content.json"

    def test_each_exploit_has_required_keys(self, game_data):
        """Verify each exploit has required attributes."""
        exploits = game_data["exploits"]
        required_keys = [
            "name",
            "ram",
            "heat",
            "range",
            "category",
            "damage",
            "targeting",
            "description",
        ]

        for exploit_id, exploit_data in exploits.items():
            for key in required_keys:
                assert (
                    key in exploit_data
                ), f"Exploit '{exploit_id}' missing required key '{key}' in game_content.json"

    def test_has_upgrades_section(self, game_data):
        """Verify upgrades section exists."""
        assert "upgrades" in game_data, "Missing required 'upgrades' section in game_content.json"

    def test_upgrades_not_empty(self, game_data):
        """Verify upgrades section has entries."""
        upgrades = game_data["upgrades"]
        assert len(upgrades) > 0, "upgrades section is empty in game_content.json"

    def test_has_network_configs_section(self, game_data):
        """Verify network_configs section exists."""
        assert (
            "network_configs" in game_data
        ), "Missing required 'network_configs' section in game_content.json"

    def test_network_configs_has_all_levels(self, game_data):
        """Verify network configs exist for all 3 levels."""
        network_configs = game_data["network_configs"]

        for level in ["1", "2", "3"]:
            assert (
                level in network_configs
            ), f"Missing network config for level {level} in game_content.json"

    def test_each_network_config_has_required_keys(self, game_data):
        """Verify each network config has required attributes."""
        network_configs = game_data["network_configs"]
        required_keys = [
            "enemies",
            "blind_spot_coverage",
            "name",
            "background_trace",
            "trace_alert_to_hostile",
            "trace_continuous_hostile",
            "cooling_nodes",
            "cpu_nodes",
            "ghost_nodes",
            "code_hacks",
            "exploit_pickups",
            "permanent_upgrades",
        ]

        for level, config in network_configs.items():
            for key in required_keys:
                assert (
                    key in config
                ), f"Network config level {level} missing required key '{key}' in game_content.json"

    def test_has_difficulty_multipliers_section(self, game_data):
        """Verify difficulty_multipliers section exists."""
        assert (
            "difficulty_multipliers" in game_data
        ), "Missing required 'difficulty_multipliers' section in game_content.json"

    def test_difficulty_multipliers_has_all_levels(self, game_data):
        """Verify difficulty multipliers exist for all difficulty levels."""
        multipliers = game_data["difficulty_multipliers"]

        for difficulty in ["easy", "normal", "hard", "nightmare"]:
            assert (
                difficulty in multipliers
            ), f"Missing difficulty multiplier for '{difficulty}' in game_content.json"


class TestNarrativeContentStructure:
    """Verify narrative_content.json has required structure."""

    @pytest.fixture(scope="class")
    def story_data(self):
        """Load narrative_content.json once for all tests."""
        with open("narrative_content.json", encoding="utf-8") as f:
            return json.load(f)

    def test_has_fragments_key(self, story_data):
        """Verify fragments key exists."""
        assert (
            "fragments" in story_data
        ), "Missing required 'fragments' key in narrative_content.json"

    def test_fragments_is_list(self, story_data):
        """Verify fragments is a list."""
        assert isinstance(
            story_data["fragments"], list
        ), "fragments should be a list in narrative_content.json"

    def test_fragments_not_empty(self, story_data):
        """Verify fragments list is not empty."""
        assert len(story_data["fragments"]) > 0, "fragments list is empty in narrative_content.json"


# ============================================================================
# TIER 3: CROSS-FILE VALIDATION
# ============================================================================


class TestConfigCompleteness:
    """Verify all required top-level sections exist across files."""

    def _load_json(self, filename):
        """Load a JSON file from project root."""
        path = Path(__file__).parent.parent.parent / filename
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def test_game_config_has_all_top_level_sections(self):
        """Test that game_rules.json has all required top-level sections."""
        game_config = self._load_json("game_rules.json")

        required_sections = [
            "display",
            "ui",
            "gameplay",
            "audio",
            "room_generation",
            "balance",
            "colors",
            "message_types",
            "symbols",
            "characters",
            "welcome_messages",
            "metadata",
        ]

        missing = [s for s in required_sections if s not in game_config]

        assert len(missing) == 0, f"game_rules.json is missing required sections: {missing}"

    def test_game_data_has_all_top_level_sections(self):
        """Test that game_content.json has all required top-level sections."""
        game_data = self._load_json("game_content.json")

        required_sections = [
            "enemy_types",
            "exploits",
            "upgrades",
            "network_configs",
            "difficulty_multipliers",
            "metadata",
        ]

        missing = [s for s in required_sections if s not in game_data]

        assert len(missing) == 0, f"game_content.json is missing required sections: {missing}"


class TestConfigRedundancy:
    """Test for duplicate/redundant config values across JSON files."""

    def setup_method(self):
        """Load all config files."""
        self.game_config = self._load_json("game_rules.json")
        self.game_data = self._load_json("game_content.json")
        self.story_content = self._load_json("narrative_content.json")

    def _load_json(self, filename):
        """Load a JSON file from project root."""
        path = Path(__file__).parent.parent.parent / filename
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def test_no_duplicate_balance_values(self):
        """Test that balance values are not duplicated between config files."""
        game_config_balance = self.game_config.get("balance", {})
        game_data_balance = self.game_data.get("balance", {})

        # Find overlapping keys
        config_keys = set(game_config_balance.keys())
        data_keys = set(game_data_balance.keys())
        duplicates = config_keys.intersection(data_keys)

        # Report duplicates with values
        duplicate_details = {}
        for key in duplicates:
            if key != "ai_behavior":  # ai_behavior is intentionally in both (nested structure)
                config_value = game_config_balance[key]
                data_value = game_data_balance[key]
                duplicate_details[key] = {"game_config": config_value, "game_data": data_value}

        assert len(duplicate_details) == 0, (
            f"Found duplicate balance values in both game_rules.json and game_content.json:\n"
            f"{json.dumps(duplicate_details, indent=2)}\n"
            f"These values should exist in only ONE file to maintain single source of truth."
        )

    def test_ai_behavior_values_consistent(self):
        """Test that ai_behavior values match between files if duplicated."""
        config_ai = self.game_config.get("balance", {}).get("ai_behavior", {})
        data_ai = self.game_data.get("balance", {}).get("ai_behavior", {})

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
        balance = self.game_config.get("balance", {})

        # These should ONLY be in gameplay, not balance
        gameplay_only_keys = [
            "max_heat",
            "max_trace_level",
            "default_player_cpu",
            "default_player_ram",
        ]

        duplicates_found = []
        for key in gameplay_only_keys:
            if key in balance:
                duplicates_found.append(f"{key} found in both gameplay and balance")

        assert len(duplicates_found) == 0, "Found settings in wrong sections:\n" + "\n".join(
            duplicates_found
        )

    def test_metadata_versions_consistent(self):
        """Test that version numbers are consistent across config files."""
        config_version = self.game_config.get("metadata", {}).get("version")
        data_version = self.game_data.get("metadata", {}).get("version")

        if config_version and data_version:
            assert config_version == data_version, (
                f"Version mismatch:\n"
                f"  game_rules.json: {config_version}\n"
                f"  game_content.json: {data_version}\n"
                f"All config files should have matching versions."
            )

    def test_no_duplicate_keys_across_all_config_files(self):
        """
        Test that no keys are duplicated across ALL config files.

        This comprehensive test prevents the mistake of defining the same
        variable in multiple JSON files where only the last one loaded would count.

        Checks:
        - game_rules.json (all sections)
        - game_content.json (all sections)
        - user_settings.json defaults (from GameSettings.DEFAULTS)

        Exceptions:
        - 'metadata' sections (allowed in multiple files)
        - 'version' keys (allowed in metadata)
        - Nested structures (ai_behavior) intentionally duplicated
        """
        from rsp.core.config import GameSettings

        # Collect all keys from all files with their source
        all_keys = {}  # {key: [file1, file2, ...]}

        def collect_keys(data, file_name, section_path=""):
            """Recursively collect all keys from a nested dict."""
            if not isinstance(data, dict):
                return

            for key, value in data.items():
                # Skip metadata sections (intentionally in multiple files)
                if key == "metadata":
                    continue

                full_key = f"{section_path}.{key}" if section_path else key

                # Track which file this key appears in
                if full_key not in all_keys:
                    all_keys[full_key] = []
                all_keys[full_key].append(file_name)

                # Recurse into nested dicts (but track the path)
                if isinstance(value, dict):
                    collect_keys(value, file_name, full_key)

        # Collect keys from all config files
        collect_keys(self.game_config, "game_rules.json")
        collect_keys(self.game_data, "game_content.json")
        collect_keys(GameSettings.DEFAULTS, "user_settings.json")

        # Find duplicates (keys that appear in more than one file)
        duplicates = {}
        for key, sources in all_keys.items():
            if len(sources) > 1:
                # Exception: ai_behavior is intentionally in multiple files (nested structure)
                if key == "balance.ai_behavior":
                    continue

                # Exception: ascension exists in both game_rules.json (modifier values)
                # and user_settings.json (user progress/current level) - different purposes
                if key == "ascension":
                    continue

                # Get values from each source
                values = {}
                for source in sources:
                    if source == "game_rules.json":
                        values[source] = self._get_nested_value(self.game_config, key)
                    elif source == "game_content.json":
                        values[source] = self._get_nested_value(self.game_data, key)
                    elif source == "user_settings.json":
                        values[source] = self._get_nested_value(GameSettings.DEFAULTS, key)

                duplicates[key] = {"sources": sources, "values": values}

        assert len(duplicates) == 0, (
            f"Found {len(duplicates)} duplicate keys across config files:\n"
            f"{json.dumps(duplicates, indent=2, default=str)}\n\n"
            f"Each configuration value should exist in ONLY ONE file to maintain "
            f"single source of truth and prevent the bug where defining a variable "
            f"twice means only the last one loaded counts."
        )

    def _get_nested_value(self, data, key_path):
        """Get a value from nested dict using dot notation (e.g., 'balance.heat_reduction')."""
        keys = key_path.split(".")
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value


# ============================================================================
# TIER 4: VALUE VALIDATION
# ============================================================================


class TestConfigValueConsistency:
    """Verify config values are consistent and reasonable."""

    @pytest.fixture(scope="class")
    def config_data(self):
        """Load game_rules.json once for all tests."""
        with open("game_rules.json", encoding="utf-8") as f:
            return json.load(f)

    @pytest.fixture(scope="class")
    def game_data(self):
        """Load game_content.json once for all tests."""
        with open("game_content.json", encoding="utf-8") as f:
            return json.load(f)

    def test_cpu_restore_min_less_than_max(self, config_data):
        """Verify CPU restore min is less than max."""
        balance = config_data["balance"]
        assert (
            balance["cpu_restore_min"] < balance["cpu_restore_max"]
        ), "cpu_restore_min should be less than cpu_restore_max"

    def test_screen_dimensions_positive(self, config_data):
        """Verify screen dimensions are positive."""
        display = config_data["display"]
        assert display["screen_width"] > 0
        assert display["screen_height"] > 0
        assert display["map_width"] > 0
        assert display["map_height"] > 0

    def test_gameplay_values_positive(self, config_data):
        """Verify gameplay values are positive."""
        gameplay = config_data["gameplay"]
        assert gameplay["default_player_ram"] > 0
        assert gameplay["default_player_cpu"] > 0
        assert gameplay["max_heat"] > 0
        assert gameplay["max_trace_level"] > 0

    def test_balance_values_positive(self, config_data):
        """Verify balance values are positive."""
        balance = config_data["balance"]
        assert balance["heat_reduction_normal"] > 0
        assert balance["heat_reduction_boosted"] > 0
        assert balance["cooling_node_effect"] > 0
        assert balance["cpu_recovery_amount"] > 0

    def test_difficulty_multipliers_reasonable(self, game_data):
        """Verify difficulty multipliers are in reasonable range."""
        multipliers = game_data["difficulty_multipliers"]

        # Easy should be < 1.0, normal = 1.0, hard/nightmare > 1.0
        assert multipliers["easy"] < 1.0
        assert multipliers["normal"] == 1.0
        assert multipliers["hard"] > 1.0
        assert multipliers["nightmare"] > multipliers["hard"]


class TestConfigValueUsage:
    """Test that config values exist for features that need them."""

    def setup_method(self):
        """Load config files."""
        self.game_config = self._load_json("game_rules.json")
        self.game_data = self._load_json("game_content.json")

    def _load_json(self, filename):
        """Load a JSON file from project root."""
        path = Path(__file__).parent.parent.parent / filename
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def test_cpu_restore_values_exist(self):
        """Test that cpu_restore_min/max values exist (used by code hacks)."""
        config_balance = self.game_config.get("balance", {})
        data_balance = self.game_data.get("balance", {})

        # At least ONE file should have these values
        has_in_config = "cpu_restore_min" in config_balance and "cpu_restore_max" in config_balance
        has_in_data = "cpu_restore_min" in data_balance and "cpu_restore_max" in data_balance

        assert has_in_config or has_in_data, (
            "cpu_restore_min/max not found in any config file. "
            "These are required for restore_cpu code hack."
        )

    def test_heat_reduction_values_exist(self):
        """Test that heat reduction values exist for various game mechanics."""
        balance = self.game_config.get("balance", {})

        required_heat_values = [
            "heat_reduction_normal",
            "heat_reduction_boosted",
            "heat_reduction_instant",
        ]

        missing = [v for v in required_heat_values if v not in balance]

        assert (
            len(missing) == 0
        ), f"Missing required heat reduction values in game_rules.json balance: {missing}"

    def test_trace_management_values_exist(self):
        """Test that trace management values exist."""
        balance = self.game_config.get("balance", {})

        required_trace_values = [
            "trace_increase_interval",
            "trace_increase_amount",
            "trace_reduction_code_hack",
            "ghost_node_trace_reduction_percent",
        ]

        missing = [v for v in required_trace_values if v not in balance]

        assert (
            len(missing) == 0
        ), f"Missing required trace values in game_rules.json balance: {missing}"

    def test_enemy_ai_values_exist(self):
        """Test that enemy AI behavior values exist."""
        balance = self.game_config.get("balance", {})

        required_ai_values = [
            "enemy_memory_turns",
            "patrol_stuck_threshold",
            "max_movement_queue_size",
            "pathfinding_timeout_attempts",
        ]

        missing = [v for v in required_ai_values if v not in balance]

        assert (
            len(missing) == 0
        ), f"Missing required AI values in game_rules.json balance: {missing}"

    def test_vision_system_values_exist(self):
        """Test that vision system values exist."""
        balance = self.game_config.get("balance", {})

        required_vision_values = [
            "enhanced_vision_bonus",
            "blind_spot_vision_reduction_factor",
            "adjacent_distance_threshold",
        ]

        missing = [v for v in required_vision_values if v not in balance]

        assert (
            len(missing) == 0
        ), f"Missing required vision values in game_rules.json balance: {missing}"


# ============================================================================
# TIER 5: INTEGRATION TESTS (Most important - NO MOCKING)
# ============================================================================


class TestConfigRealObjectInstantiation:
    """
    CRITICAL SMOKE TESTS - Instantiate real objects with real config.

    These tests verify that real game objects can be created using real config files.
    NO MOCKING - this catches real integration issues.
    """

    def test_game_config_loads_successfully(self):
        """Verify GameConfig can load from real JSON file."""
        from rsp.core.config import GameConfig

        GameConfig._config_data = None
        GameConfig.load_from_json()

        assert GameConfig.SCREEN_WIDTH > 0
        assert GameConfig.SCREEN_HEIGHT > 0
        assert GameConfig.DEFAULT_PLAYER_RAM > 0
        assert GameConfig.DEFAULT_PLAYER_CPU > 0

    def test_game_balance_loads_successfully(self):
        """Verify GameBalance can load from real JSON file."""
        from rsp.core.config import GameBalance, GameConfig

        GameConfig._config_data = None
        GameConfig.load_from_json()

        GameBalance.load_from_json()

        assert GameBalance.HEAT_REDUCTION_NORMAL > 0
        assert GameBalance.CPU_RESTORE_MIN > 0
        assert GameBalance.CPU_RESTORE_MAX > GameBalance.CPU_RESTORE_MIN
        assert GameBalance.HEAT_REDUCTION_INSTANT > 0

    def test_room_generation_config_loads_successfully(self):
        """Verify RoomGenerationConfig can load from real JSON file."""
        from rsp.core.config import GameConfig, RoomGenerationConfig

        GameConfig._config_data = None
        GameConfig.load_from_json()

        RoomGenerationConfig.load_from_json()

        assert RoomGenerationConfig.MIN_ROOMS_BASE > 0
        assert RoomGenerationConfig.MAX_ROOMS > 0

    def test_data_loader_loads_game_data_successfully(self):
        """Verify DataLoader can load game_content.json."""
        from rsp.core.data import DataLoader

        DataLoader._game_data = None

        game_data = DataLoader.load_game_data()

        assert "enemy_types" in game_data
        assert "exploits" in game_data
        assert "network_configs" in game_data

    def test_data_loader_loads_story_fragments_successfully(self):
        """Verify DataLoader can load narrative_content.json."""
        from rsp.core.data import DataLoader

        DataLoader._story_fragments = None

        fragments = DataLoader.load_story_fragments()

        assert isinstance(fragments, list)
        assert len(fragments) > 0

    def test_player_creation_with_real_config(self):
        """Verify Player can be created with real config values."""
        from rsp.core.config import GameConfig
        from rsp.entities.base import Position
        from rsp.entities.player import Player

        GameConfig._config_data = None
        GameConfig.load_from_json()

        player = Player(10, 10)

        assert player is not None
        assert player.position == Position(10, 10)
        assert player.ram_total > 0
        assert player.cpu > 0

    def test_enemy_creation_with_real_config(self):
        """Verify Enemy can be created with real config data."""
        from rsp.entities.characters import Enemy
        from rsp.entities.base import Position

        enemy = Enemy(Position(15, 15), "scanner")

        assert enemy is not None
        assert enemy.position == Position(15, 15)
        assert enemy.type == "scanner"
        assert enemy.cpu > 0

    def test_code_hack_with_real_balance_values(self):
        """Verify CodeHack uses real balance values from JSON."""
        from rsp.core.config import GameBalance, GameConfig
        from rsp.combat.inventory import CodeHack
        from rsp.entities.player import Player

        GameConfig._config_data = None
        GameConfig.load_from_json()
        GameBalance.load_from_json()

        cpu_restore_min = GameBalance.CPU_RESTORE_MIN

        code_hack = CodeHack("red", "restore_cpu", "Red Code", "Restores CPU")

        player = Player(10, 10)
        player.cpu = 50

        class MockGame:
            class MockMessageLog:
                def add_message(self, *args, **kwargs):
                    pass

            def __init__(self):
                self.message_log = self.MockMessageLog()

        mock_game = MockGame()

        initial_cpu = player.cpu
        code_hack._apply_effect("restore_cpu", player, mock_game)

        assert player.cpu > initial_cpu
        assert player.cpu >= initial_cpu + cpu_restore_min or player.cpu == player.max_cpu


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
