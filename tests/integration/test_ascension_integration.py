"""
Integration tests for Ascension System - Phase 2 Game Integration.

Tests verify that ascension modifiers are correctly applied to:
- Enemy stats during spawn
- Level generation (enemy counts, codes, nodes)
- Turn processing (heat, trace, alert range)
"""

import pytest
from unittest.mock import Mock

from game_ascension import AscensionModifiers, calculate_ascension_modifiers
from game_characters import Enemy
from game_config import GameSettings
from game_engine import GameEngine
from game_entities import Position


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_sound_manager():
    """Create a mock sound manager for testing."""
    return Mock()


@pytest.fixture
def game_settings():
    """Create game settings for testing."""
    return GameSettings()


def create_game_at_ascension(level: int, sound_manager=None, settings=None) -> GameEngine:
    """
    Create a GameEngine at the specified ascension level.

    Args:
        level: Ascension level (0-20)
        sound_manager: Optional mock sound manager
        settings: Optional game settings

    Returns:
        GameEngine configured at the specified ascension level
    """
    if sound_manager is None:
        sound_manager = Mock()
    if settings is None:
        settings = GameSettings()

    return GameEngine(
        sound_manager=sound_manager,
        settings=settings,
        headless=True,
        ascension_level=level,
    )


# =============================================================================
# Phase 2.1: GameEngine Integration Tests
# =============================================================================


class TestGameEngineAscensionIntegration:
    """Test GameEngine properly stores and uses ascension level."""

    def test_game_engine_stores_ascension_level(self, mock_sound_manager, game_settings):
        """GameEngine should store the ascension level it was created with."""
        engine = create_game_at_ascension(7, mock_sound_manager, game_settings)
        assert engine.ascension_level == 7

    def test_game_engine_calculates_modifiers(self, mock_sound_manager, game_settings):
        """GameEngine should calculate AscensionModifiers on creation."""
        engine = create_game_at_ascension(5, mock_sound_manager, game_settings)

        assert hasattr(engine, "ascension_modifiers")
        assert isinstance(engine.ascension_modifiers, AscensionModifiers)
        # A5 should have A1-A5 modifiers
        assert engine.ascension_modifiers.scanner_vision_bonus == 1  # A1
        assert engine.ascension_modifiers.enemy_hp_bonus == 10  # A2
        assert engine.ascension_modifiers.enemy_vision_bonus == 1  # A5


# =============================================================================
# Phase 2.2: Enemy Modifier Application Tests
# =============================================================================


class TestEnemyAscensionModifierApplication:
    """Test that enemies get ascension modifiers applied during spawn/creation."""

    def test_enemy_hp_bonus_applied_during_level_gen(self, mock_sound_manager, game_settings):
        """Enemies spawned during level generation should have HP bonus applied."""
        engine = create_game_at_ascension(2, mock_sound_manager, game_settings)

        # Find a scanner enemy (base CPU is 35)
        scanner = None
        for enemy in engine.enemies:
            if enemy.type == "scanner":
                scanner = enemy
                break

        if scanner is not None:
            # A2 adds +10 CPU to all enemies
            # Scanner base CPU is 35, so with A2 it should be 45
            assert scanner.cpu == scanner.type_data.cpu + 10
            assert scanner.max_cpu == scanner.type_data.cpu + 10

    def test_scanner_vision_bonus_applied(self, mock_sound_manager, game_settings):
        """Scanners at A1+ should have +1 vision."""
        engine = create_game_at_ascension(1, mock_sound_manager, game_settings)

        # Find a scanner enemy
        scanner = None
        for enemy in engine.enemies:
            if enemy.type == "scanner":
                scanner = enemy
                break

        if scanner is not None:
            # A1 adds +1 vision to scanners only
            base_vision = scanner.type_data.vision
            assert scanner.vision_range == base_vision + 1

    def test_all_enemy_vision_bonus_at_a5(self, mock_sound_manager, game_settings):
        """All enemies at A5+ should have +1 vision."""
        engine = create_game_at_ascension(5, mock_sound_manager, game_settings)

        # Find non-scanner enemies
        for enemy in engine.enemies:
            if enemy.type != "scanner":
                base_vision = enemy.type_data.vision
                # A5 adds +1 vision to all enemies
                assert enemy.vision_range == base_vision + 1
                break

    def test_scanner_gets_both_vision_bonuses_at_a5(self, mock_sound_manager, game_settings):
        """Scanners at A5+ should have +2 vision total (A1 + A5)."""
        engine = create_game_at_ascension(5, mock_sound_manager, game_settings)

        # Find a scanner
        scanner = None
        for enemy in engine.enemies:
            if enemy.type == "scanner":
                scanner = enemy
                break

        if scanner is not None:
            base_vision = scanner.type_data.vision
            # A1: +1 for scanners, A5: +1 for all enemies
            assert scanner.vision_range == base_vision + 2

    def test_enemy_damage_multiplier_stored(self, mock_sound_manager, game_settings):
        """Enemies at A4+ should have damage multiplier stored."""
        engine = create_game_at_ascension(4, mock_sound_manager, game_settings)

        if engine.enemies:
            enemy = engine.enemies[0]
            # A4 sets damage multiplier to 1.2
            assert enemy.damage_multiplier == 1.2


# =============================================================================
# Phase 2.3: Level Generation Modifier Tests
# =============================================================================


class TestLevelGenerationModifiers:
    """Test that level generation respects ascension modifiers."""

    def test_enemy_count_bonus_applied_at_a9(self, mock_sound_manager, game_settings):
        """A9+ should add +5 enemies per floor."""
        # Create engine at A9
        engine_a9 = create_game_at_ascension(9, mock_sound_manager, game_settings)
        enemy_count_a9 = len(engine_a9.enemies)

        # Create engine at A0 for comparison
        engine_a0 = create_game_at_ascension(0, mock_sound_manager, game_settings)
        enemy_count_a0 = len(engine_a0.enemies)

        # A9 should have approximately +5 enemies
        # Allow some variance due to placement constraints
        assert enemy_count_a9 >= enemy_count_a0 + 3  # At least +3 to account for variance

    def test_spawn_weights_modified_at_a12(self, mock_sound_manager, game_settings):
        """A12 should use modified spawn weights for more dangerous enemies."""
        # This test verifies the spawn weights config is being used
        engine = create_game_at_ascension(12, mock_sound_manager, game_settings)

        # At A12, spawn weights favor more dangerous enemies
        # Check that modifiers are properly configured
        assert engine.ascension_modifiers.spawn_weights is not None
        assert engine.ascension_modifiers.spawn_weights["hunter"] == 4  # Up from 2
        assert engine.ascension_modifiers.spawn_weights["virus"] == 3  # Up from 1


# =============================================================================
# Phase 2.4: Turn Processing Modifier Tests
# =============================================================================


class TestTurnProcessingModifiers:
    """Test that turn processing uses ascension modifiers."""

    def test_heat_reduction_override_at_a8(self, mock_sound_manager, game_settings):
        """A8+ should reduce heat cooling rate from 2 to 1."""
        engine = create_game_at_ascension(8, mock_sound_manager, game_settings)

        # Verify modifier is set
        assert engine.ascension_modifiers.heat_reduction_override == 1

    def test_trace_gain_multiplier_at_a3(self, mock_sound_manager, game_settings):
        """A3+ should double background trace gain."""
        engine = create_game_at_ascension(3, mock_sound_manager, game_settings)

        # Verify modifier is set
        assert engine.ascension_modifiers.trace_gain_multiplier == 2.0

    def test_alert_range_override_at_a15(self, mock_sound_manager, game_settings):
        """A15+ should increase alert range to 10."""
        engine = create_game_at_ascension(15, mock_sound_manager, game_settings)

        # Verify modifier is set
        assert engine.ascension_modifiers.alert_range_override == 10

    def test_melee_heat_bonus_at_a17(self, mock_sound_manager, game_settings):
        """A17+ should add +5 heat per melee attack."""
        engine = create_game_at_ascension(17, mock_sound_manager, game_settings)

        # Verify modifier is set
        assert engine.ascension_modifiers.melee_heat_bonus == 5


# =============================================================================
# Modifier Application Tests (Actual Gameplay Impact)
# =============================================================================


class TestModifierGameplayImpact:
    """Test that modifiers actually affect gameplay, not just config."""

    def test_manually_created_enemy_with_modifiers(self):
        """Verify Enemy.apply_ascension_modifiers works correctly."""
        enemy = Enemy(Position(5, 5), "scanner")
        original_cpu = enemy.cpu
        original_vision = enemy.type_data.vision

        mods = AscensionModifiers(
            enemy_hp_bonus=10,
            scanner_vision_bonus=1,
            enemy_vision_bonus=1,
            enemy_damage_multiplier=1.2,
        )
        enemy.apply_ascension_modifiers(mods)

        # Check HP bonus
        assert enemy.cpu == original_cpu + 10
        assert enemy.max_cpu == original_cpu + 10

        # Check vision bonus (scanner gets both bonuses)
        assert enemy.vision_range == original_vision + 2

        # Check damage multiplier
        assert enemy.damage_multiplier == 1.2

    def test_patrol_enemy_vision_bonus(self):
        """Verify patrol enemies get vision bonus but not scanner bonus."""
        enemy = Enemy(Position(5, 5), "patrol")
        original_vision = enemy.type_data.vision

        mods = AscensionModifiers(
            scanner_vision_bonus=1,  # Should NOT apply
            enemy_vision_bonus=1,  # Should apply
        )
        enemy.apply_ascension_modifiers(mods)

        # Patrol only gets the general enemy vision bonus
        assert enemy.vision_range == original_vision + 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
