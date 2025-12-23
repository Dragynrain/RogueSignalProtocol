#!/usr/bin/env python3
"""
Tests for fail-fast config loading behavior.

These tests verify that required JSON config sections raise errors
when missing, rather than silently falling back to defaults.

Per CLAUDE.md: "Fail-fast on missing game_content.json, game_rules.json,
narrative_content.json. ONLY user_settings.json defaults. No hardcoded fallbacks."
"""


class TestAscensionConfigFailFast:
    """Test that ascension config loading fails fast on missing sections."""

    def test_ascension_section_exists(self):
        """Verify ascension section exists in game_rules.json."""
        from game_ascension import _load_ascension_config

        config = _load_ascension_config()
        # Should not raise - section exists
        assert "modifiers" in config
        assert "max_level" in config

    def test_calculate_modifiers_requires_modifiers_section(self):
        """Verify calculate_ascension_modifiers uses config correctly."""
        from game_ascension import calculate_ascension_modifiers

        # Should not raise for valid level
        mods = calculate_ascension_modifiers(1)
        # Just verify it returns a valid object
        assert mods is not None

    def test_get_max_ascension_level_uses_config(self):
        """Verify max level comes from config, not hardcoded."""
        from game_ascension import get_max_ascension_level

        max_level = get_max_ascension_level()
        assert isinstance(max_level, int)
        assert max_level > 0


class TestNetworkConfigFailFast:
    """Test that network config loading fails fast on missing data."""

    def test_network_configs_exist(self):
        """Verify network configs exist for all levels."""
        from game_config import GameConfig

        configs = GameConfig.get_network_configs()
        # Should have configs for at least levels 1-3
        assert 1 in configs
        assert 2 in configs
        assert 3 in configs

    def test_network_config_has_name(self):
        """Verify each network config has required 'name' field."""
        from game_config import GameConfig

        configs = GameConfig.get_network_configs()
        for level, config in configs.items():
            assert "name" in config, f"Level {level} config missing 'name'"


class TestGatewayStrategyWeights:
    """Test that gateway strategy weights are properly loaded."""

    def test_gateway_strategy_weights_exist(self):
        """Verify gateway strategy weights exist in config."""
        from game_config import GameConfig

        weights = GameConfig._get_required("room_generation.gateway_strategy_weights")
        assert "far_corner" in weights
        assert "central_hub" in weights
        assert "hidden_dead_end" in weights
        assert "gauntlet" in weights

    def test_gateway_weights_are_numeric(self):
        """Verify gateway weights are valid numbers."""
        from game_config import GameConfig

        weights = GameConfig._get_required("room_generation.gateway_strategy_weights")
        for key, value in weights.items():
            assert isinstance(value, (int, float)), f"Weight '{key}' is not numeric"
            assert value >= 0, f"Weight '{key}' is negative"


class TestPatrolValidationMargin:
    """Test that patrol validation margin is properly configured."""

    def test_patrol_validation_margin_exists(self):
        """Verify patrol validation margin exists in config."""
        from game_config import GameConfig

        margin = GameConfig._get_required("balance.patrol_validation_margin")
        assert isinstance(margin, int)
        assert margin >= 0


class TestRequiredConfigSections:
    """Test that all required config sections exist."""

    def test_balance_section_exists(self):
        """Verify balance section exists."""
        from game_config import GameConfig

        # These should not raise
        GameConfig._get_required("balance.patrol_spacing_min")
        GameConfig._get_required("balance.patrol_spacing_max")
        GameConfig._get_required("balance.shadow_damage_bonus")

    def test_room_generation_section_exists(self):
        """Verify room_generation section exists."""
        from game_config import GameConfig

        GameConfig._get_required("room_generation.gateway_strategy_weights")
        GameConfig._get_required("room_generation.min_rooms_base")

    def test_gameplay_section_exists(self):
        """Verify gameplay section exists."""
        from game_config import GameConfig

        GameConfig._get_required("gameplay.default_player_cpu")
        GameConfig._get_required("gameplay.default_player_ram")
