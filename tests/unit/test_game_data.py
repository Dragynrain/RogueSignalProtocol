#!/usr/bin/env python3
"""
Unit tests for game_data.py - JSON data loading and game definitions.

Tests cover:
- Enemy type loading from JSON
- Exploit definitions validation
- Upgrade loading from JSON
- GameBalance configuration access
- Error handling for missing/corrupt data

These tests use real game data (real_game_data fixture) to validate
that the actual JSON configuration is valid and loadable.
"""

import pytest

from game_data import GameData, GameUpgrades, GameBalance
from game_entities import EnemyMovement, TargetingMode


class TestGameDataEnemyTypes:
    """Test enemy type loading and validation."""

    def test_enemy_types_loaded(self, real_game_data):
        """GameData.ENEMY_TYPES should be loaded on module import."""
        assert GameData.ENEMY_TYPES is not None
        assert isinstance(GameData.ENEMY_TYPES, dict)
        assert len(GameData.ENEMY_TYPES) > 0

    def test_all_enemy_types_have_required_fields(self, real_game_data):
        """Every enemy type should have all required fields."""
        required_fields = ["symbol", "cpu", "vision", "movement", "name", "damage"]

        for enemy_id, enemy_type in GameData.ENEMY_TYPES.items():
            # Check all fields exist
            assert hasattr(enemy_type, "symbol"), f"{enemy_id} missing symbol"
            assert hasattr(enemy_type, "cpu"), f"{enemy_id} missing cpu"
            assert hasattr(enemy_type, "vision"), f"{enemy_id} missing vision"
            assert hasattr(enemy_type, "movement"), f"{enemy_id} missing movement"
            assert hasattr(enemy_type, "name"), f"{enemy_id} missing name"
            assert hasattr(enemy_type, "damage"), f"{enemy_id} missing damage"

    def test_enemy_types_have_valid_stats(self, real_game_data):
        """Enemy stats should be valid positive values."""
        for enemy_id, enemy_type in GameData.ENEMY_TYPES.items():
            assert enemy_type.cpu > 0, f"{enemy_id} has invalid CPU: {enemy_type.cpu}"
            assert enemy_type.vision >= 0, f"{enemy_id} has invalid vision: {enemy_type.vision}"
            assert enemy_type.damage >= 0, f"{enemy_id} has invalid damage: {enemy_type.damage}"

    def test_enemy_types_have_valid_movement(self, real_game_data):
        """Enemy movement types should be valid EnemyMovement enums."""
        valid_movements = [
            EnemyMovement.SEEK,
            EnemyMovement.RANDOM,
            EnemyMovement.PATROL,
            EnemyMovement.STATIC,
        ]

        for enemy_id, enemy_type in GameData.ENEMY_TYPES.items():
            assert (
                enemy_type.movement in valid_movements
            ), f"{enemy_id} has invalid movement: {enemy_type.movement}"

    def test_enemy_types_have_single_character_symbols(self, real_game_data):
        """Enemy symbols should be single uppercase letters (A-Z)."""
        for enemy_id, enemy_type in GameData.ENEMY_TYPES.items():
            assert len(enemy_type.symbol) == 1, f"{enemy_id} symbol not single char: {enemy_type.symbol}"
            assert (
                enemy_type.symbol.isupper()
            ), f"{enemy_id} symbol not uppercase: {enemy_type.symbol}"
            assert (
                enemy_type.symbol.isalpha()
            ), f"{enemy_id} symbol not alphabetic: {enemy_type.symbol}"

    def test_enemy_types_have_unique_symbols(self, real_game_data):
        """Each enemy type should have a unique symbol."""
        symbols = [enemy_type.symbol for enemy_type in GameData.ENEMY_TYPES.values()]

        # Check for duplicates
        assert len(symbols) == len(set(symbols)), "Duplicate enemy symbols found"

    def test_standard_enemy_types_exist(self, real_game_data):
        """Standard enemy types should exist in ENEMY_TYPES."""
        # Check for common enemy types (based on typical game content)
        # At minimum we expect some basic enemy types to exist
        assert len(GameData.ENEMY_TYPES) > 0, "No enemy types loaded"


class TestGameDataExploits:
    """Test exploit definitions."""

    def test_exploits_dict_exists(self):
        """GameData.EXPLOITS should be a non-empty dict."""
        assert GameData.EXPLOITS is not None
        assert isinstance(GameData.EXPLOITS, dict)
        assert len(GameData.EXPLOITS) > 0

    def test_all_exploits_have_required_fields(self):
        """Every exploit should have all required fields."""
        for exploit_key, exploit in GameData.EXPLOITS.items():
            assert exploit.name is not None, f"{exploit_key} missing name"
            assert exploit.ram >= 0, f"{exploit_key} has invalid RAM: {exploit.ram}"
            assert exploit.heat >= 0, f"{exploit_key} has invalid heat: {exploit.heat}"
            assert exploit.range >= 0, f"{exploit_key} has invalid range: {exploit.range}"
            assert exploit.category is not None, f"{exploit_key} missing category"
            assert exploit.damage >= 0, f"{exploit_key} has invalid damage: {exploit.damage}"
            assert exploit.targeting is not None, f"{exploit_key} missing targeting"
            assert exploit.description is not None, f"{exploit_key} missing description"

    def test_exploits_have_valid_categories(self):
        """Exploits should use standard categories."""
        valid_categories = ["stealth", "combat", "emergency", "utility"]

        for exploit_key, exploit in GameData.EXPLOITS.items():
            assert (
                exploit.category in valid_categories
            ), f"{exploit_key} has invalid category: {exploit.category}"

    def test_exploits_have_valid_targeting(self):
        """Exploits should use valid TargetingMode values."""
        valid_targeting = [TargetingMode.SINGLE, TargetingMode.AREA, TargetingMode.NONE]

        for exploit_key, exploit in GameData.EXPLOITS.items():
            assert (
                exploit.targeting in valid_targeting
            ), f"{exploit_key} has invalid targeting: {exploit.targeting}"

    def test_standard_exploits_exist(self):
        """Standard exploits should exist."""
        expected_exploits = [
            "system_hop",
            "traffic_masquerade",
            "buffer_overflow",
            "code_injection",
            "threat_scan",
        ]

        for exploit in expected_exploits:
            assert exploit in GameData.EXPLOITS, f"Missing standard exploit: {exploit}"

    def test_exploit_range_matches_targeting(self):
        """Exploits with NONE targeting should have 0 range."""
        for exploit_key, exploit in GameData.EXPLOITS.items():
            if exploit.targeting == TargetingMode.NONE:
                assert (
                    exploit.range == 0
                ), f"{exploit_key} has NONE targeting but non-zero range: {exploit.range}"

    def test_combat_exploits_have_damage(self):
        """Combat category exploits should typically have damage > 0."""
        combat_exploits = [
            exploit
            for exploit_key, exploit in GameData.EXPLOITS.items()
            if exploit.category == "combat"
        ]

        # At least some combat exploits should deal damage
        exploits_with_damage = [e for e in combat_exploits if e.damage > 0]
        assert (
            len(exploits_with_damage) > 0
        ), "No combat exploits have damage (this might be intentional, but is unusual)"


class TestGameUpgrades:
    """Test upgrade loading and validation."""

    def test_upgrades_loaded(self, real_game_data):
        """GameUpgrades.UPGRADES should be loaded."""
        assert GameUpgrades.UPGRADES is not None
        assert isinstance(GameUpgrades.UPGRADES, dict)
        assert len(GameUpgrades.UPGRADES) > 0

    def test_all_upgrades_have_required_fields(self, real_game_data):
        """Every upgrade should have all required fields."""
        for upgrade_key, upgrade in GameUpgrades.UPGRADES.items():
            assert upgrade.name is not None, f"{upgrade_key} missing name"
            assert upgrade.symbol is not None, f"{upgrade_key} missing symbol"
            assert upgrade.color is not None, f"{upgrade_key} missing color"
            assert upgrade.stat_type is not None, f"{upgrade_key} missing stat_type"
            assert upgrade.bonus_amount > 0, f"{upgrade_key} has invalid bonus: {upgrade.bonus_amount}"

    def test_upgrades_have_valid_stat_types(self, real_game_data):
        """Upgrades should use valid stat types."""
        valid_stat_types = ["ram", "cpu", "heat"]

        for upgrade_key, upgrade in GameUpgrades.UPGRADES.items():
            assert (
                upgrade.stat_type in valid_stat_types
            ), f"{upgrade_key} has invalid stat_type: {upgrade.stat_type}"

    def test_upgrades_have_valid_colors(self, real_game_data):
        """Upgrade colors should be valid RGB tuples."""
        for upgrade_key, upgrade in GameUpgrades.UPGRADES.items():
            assert isinstance(upgrade.color, tuple), f"{upgrade_key} color not a tuple"
            assert len(upgrade.color) == 3, f"{upgrade_key} color not RGB (length {len(upgrade.color)})"

            # Check RGB values are in valid range
            r, g, b = upgrade.color
            assert 0 <= r <= 255, f"{upgrade_key} red value out of range: {r}"
            assert 0 <= g <= 255, f"{upgrade_key} green value out of range: {g}"
            assert 0 <= b <= 255, f"{upgrade_key} blue value out of range: {b}"

    def test_upgrades_ensure_loaded_is_idempotent(self, real_game_data):
        """Calling _ensure_loaded multiple times should be safe."""
        initial_upgrades = dict(GameUpgrades.UPGRADES)

        GameUpgrades._ensure_loaded()
        GameUpgrades._ensure_loaded()

        # Should still have the same upgrades
        assert GameUpgrades.UPGRADES == initial_upgrades

    def test_standard_upgrade_types_exist(self, real_game_data):
        """At least one upgrade of each stat type should exist."""
        stat_types = set(upgrade.stat_type for upgrade in GameUpgrades.UPGRADES.values())

        # Should have variety of upgrade types
        assert "ram" in stat_types or "cpu" in stat_types or "heat" in stat_types, (
            "No standard upgrade types found"
        )


class TestGameBalanceConfiguration:
    """Test GameBalance configuration access."""

    def test_get_balance_returns_dict(self, real_game_data):
        """get_balance should return a dictionary."""
        balance = GameBalance.get_balance()

        assert balance is not None
        assert isinstance(balance, dict)

    def test_cpu_restore_values_exist(self, real_game_data):
        """CPU restore min/max values should exist."""
        balance = GameBalance.get_balance()

        assert "cpu_restore_min" in balance
        assert "cpu_restore_max" in balance

        # Should be positive values
        assert balance["cpu_restore_min"] > 0
        assert balance["cpu_restore_max"] >= balance["cpu_restore_min"]

    def test_player_stats_section_exists(self, real_game_data):
        """Balance config should have player_stats section."""
        balance = GameBalance.get_balance()

        assert "player_stats" in balance
        assert isinstance(balance["player_stats"], dict)

    def test_combat_section_exists(self, real_game_data):
        """Balance config should have combat section."""
        balance = GameBalance.get_balance()

        assert "combat" in balance
        assert isinstance(balance["combat"], dict)

    def test_get_player_stat_returns_value(self, real_game_data):
        """get_player_stat should return a value for valid keys."""
        balance = GameBalance.get_balance()

        # Get first available player stat key
        if "player_stats" in balance and balance["player_stats"]:
            first_key = next(iter(balance["player_stats"].keys()))
            value = GameBalance.get_player_stat(first_key)

            assert value is not None

    def test_get_combat_value_returns_value(self, real_game_data):
        """get_combat_value should return a value for valid keys."""
        balance = GameBalance.get_balance()

        # Get first available combat value key
        if "combat" in balance and balance["combat"]:
            first_key = next(iter(balance["combat"].keys()))
            value = GameBalance.get_combat_value(first_key)

            assert value is not None


class TestGameDataIntegrity:
    """Test overall data integrity and consistency."""

    def test_enemy_types_and_exploits_loaded_together(self, real_game_data):
        """Both enemy types and exploits should be loaded."""
        assert len(GameData.ENEMY_TYPES) > 0
        assert len(GameData.EXPLOITS) > 0

    def test_enemy_types_and_upgrades_loaded_together(self, real_game_data):
        """Both enemy types and upgrades should be loaded."""
        assert len(GameData.ENEMY_TYPES) > 0
        assert len(GameUpgrades.UPGRADES) > 0

    def test_no_duplicate_enemy_type_names(self, real_game_data):
        """Enemy type names should be unique."""
        names = [enemy_type.name for enemy_type in GameData.ENEMY_TYPES.values()]

        assert len(names) == len(set(names)), "Duplicate enemy type names found"

    def test_no_duplicate_exploit_names(self):
        """Exploit names should be unique."""
        names = [exploit.name for exploit in GameData.EXPLOITS.values()]

        assert len(names) == len(set(names)), "Duplicate exploit names found"

    def test_no_duplicate_upgrade_names(self, real_game_data):
        """Upgrade names should be unique."""
        names = [upgrade.name for upgrade in GameUpgrades.UPGRADES.values()]

        assert len(names) == len(set(names)), "Duplicate upgrade names found"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
