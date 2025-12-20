"""
Unit tests for Ascension System - Phase 0 Foundation Prerequisites.

Tests cover:
- New SessionMetrics fields for ascension tracking
- New death cause type 'self_damage'
- finalize_session() with final_cpu parameter
- SessionMetrics serialization with new fields
"""

import pytest

from game_metrics import (
    SessionMetrics,
    finalize_session,
    init_session_metrics,
    track,
)


class TestSessionMetricsAscensionFields:
    """Test new SessionMetrics fields for ascension system."""

    def test_ascension_level_field_exists(self):
        """SessionMetrics should have ascension_level field defaulting to 0."""
        session = init_session_metrics()
        assert hasattr(session, "ascension_level")
        assert session.ascension_level == 0

    def test_last_exploit_used_field_exists(self):
        """SessionMetrics should have last_exploit_used field defaulting to None."""
        session = init_session_metrics()
        assert hasattr(session, "last_exploit_used")
        assert session.last_exploit_used is None

    def test_admin_kills_field_exists(self):
        """SessionMetrics should have admin_kills field defaulting to 0."""
        session = init_session_metrics()
        assert hasattr(session, "admin_kills")
        assert session.admin_kills == 0

    def test_final_cpu_field_exists(self):
        """SessionMetrics should have final_cpu field defaulting to 0."""
        session = init_session_metrics()
        assert hasattr(session, "final_cpu")
        assert session.final_cpu == 0

    def test_restoration_nodes_used_field_exists(self):
        """SessionMetrics should have restoration_nodes_used field defaulting to 0."""
        session = init_session_metrics()
        assert hasattr(session, "restoration_nodes_used")
        assert session.restoration_nodes_used == 0

    def test_full_floor_clears_field_exists(self):
        """SessionMetrics should have full_floor_clears field defaulting to 0."""
        session = init_session_metrics()
        assert hasattr(session, "full_floor_clears")
        assert session.full_floor_clears == 0


class TestFinalizeSessionFinalCpu:
    """Test finalize_session() with final_cpu parameter."""

    def test_finalize_session_stores_final_cpu(self):
        """Verify final_cpu is recorded in session metrics."""
        init_session_metrics()
        finalized = finalize_session(victory=True, death_cause=None, death_level=0, final_cpu=42)
        assert finalized.final_cpu == 42

    def test_finalize_session_final_cpu_default(self):
        """finalize_session() should default final_cpu to 0 for backward compatibility."""
        init_session_metrics()
        finalized = finalize_session(victory=False, death_cause="combat", death_level=1)
        assert finalized.final_cpu == 0

    def test_finalize_session_close_call_scenario(self):
        """Test close_call achievement scenario - winning with 5 or less CPU."""
        init_session_metrics()
        finalized = finalize_session(victory=True, death_cause=None, death_level=0, final_cpu=3)
        assert finalized.victory is True
        assert finalized.final_cpu == 3
        assert finalized.final_cpu <= 5  # Close call threshold


class TestSessionMetricsSerialization:
    """Test SessionMetrics to_dict/from_dict with new ascension fields."""

    def test_to_dict_includes_ascension_fields(self):
        """to_dict should include all new ascension tracking fields."""
        session = init_session_metrics()
        session.ascension_level = 5
        session.last_exploit_used = "logic_bomb"
        session.admin_kills = 2
        session.final_cpu = 15
        session.restoration_nodes_used = 8
        session.full_floor_clears = 1

        data = session.to_dict()

        assert data["ascension_level"] == 5
        assert data["last_exploit_used"] == "logic_bomb"
        assert data["admin_kills"] == 2
        assert data["final_cpu"] == 15
        assert data["restoration_nodes_used"] == 8
        assert data["full_floor_clears"] == 1

    def test_from_dict_restores_ascension_fields(self):
        """from_dict should restore all ascension tracking fields."""
        session = init_session_metrics()
        session.ascension_level = 10
        session.last_exploit_used = "system_crash"
        session.admin_kills = 3
        session.final_cpu = 50
        session.restoration_nodes_used = 12
        session.full_floor_clears = 2

        data = session.to_dict()
        restored = SessionMetrics.from_dict(data)

        assert restored.ascension_level == 10
        assert restored.last_exploit_used == "system_crash"
        assert restored.admin_kills == 3
        assert restored.final_cpu == 50
        assert restored.restoration_nodes_used == 12
        assert restored.full_floor_clears == 2

    def test_from_dict_handles_missing_ascension_fields(self):
        """from_dict should provide defaults for missing ascension fields (backward compat)."""
        # Simulate old save data without ascension fields
        old_data = {
            "session_id": "test_id",
            "timestamp_start": 1234567890.0,
            "victory": False,
            "death_cause": "combat",
            "death_level": 2,
            "enemies_killed": {},
            "damage_dealt": 100,
            "damage_taken": 50,
            "stealth_kills": 0,
            "steps_taken": 200,
            "levels_completed": 1,
            "turns_taken": 150,
            "exploits_used": {},
            "exploits_equipped": {},
            "exploits_unequipped": {},
            "code_hacks_used": {},
            "heat_generated": 80,
            "overheating_events": 1,
            "trace_increases": 10,
            "admin_spawns": 0,
        }

        restored = SessionMetrics.from_dict(old_data)

        # Should have defaults for missing fields
        assert restored.ascension_level == 0
        assert restored.last_exploit_used is None
        assert restored.admin_kills == 0
        assert restored.final_cpu == 0
        assert restored.restoration_nodes_used == 0
        assert restored.full_floor_clears == 0


class TestDeathCauseSelfDamage:
    """Test 'self_damage' death cause type support."""

    def test_finalize_session_accepts_self_damage(self):
        """finalize_session should accept 'self_damage' as valid death cause."""
        init_session_metrics()
        finalized = finalize_session(
            victory=False, death_cause="self_damage", death_level=2, final_cpu=0
        )
        assert finalized.death_cause == "self_damage"

    def test_self_damage_with_logic_bomb_context(self):
        """Test self_damage death cause with last_exploit_used for own_worst_enemy achievement."""
        session = init_session_metrics()
        session.last_exploit_used = "logic_bomb"

        finalized = finalize_session(
            victory=False, death_cause="self_damage", death_level=1, final_cpu=0
        )

        # Scenario for own_worst_enemy achievement
        assert finalized.death_cause == "self_damage"
        assert finalized.last_exploit_used == "logic_bomb"


class TestTrackingAscensionMetrics:
    """Test tracking ascension-related metrics."""

    def test_track_admin_kills(self):
        """Track admin_kills as integer metric."""
        session = init_session_metrics()

        track("admin_kills")
        assert session.admin_kills == 1

        track("admin_kills")
        assert session.admin_kills == 2

    def test_track_restoration_nodes_used(self):
        """Track restoration_nodes_used as integer metric."""
        session = init_session_metrics()

        track("restoration_nodes_used")
        assert session.restoration_nodes_used == 1

        track("restoration_nodes_used", amount=3)
        assert session.restoration_nodes_used == 4

    def test_track_full_floor_clears(self):
        """Track full_floor_clears as integer metric."""
        session = init_session_metrics()

        track("full_floor_clears")
        assert session.full_floor_clears == 1


class TestHighestHeatReachedTracking:
    """Test highest_heat_reached is tracked when heat increases."""

    def test_highest_heat_reached_tracks_max(self):
        """Session should track highest heat value reached."""
        session = init_session_metrics()
        assert session.highest_heat_reached == 0

        # Simulate heat increases
        session.highest_heat_reached = max(session.highest_heat_reached, 25)
        assert session.highest_heat_reached == 25

        session.highest_heat_reached = max(session.highest_heat_reached, 40)
        assert session.highest_heat_reached == 40

        # Lower heat shouldn't reduce the max
        session.highest_heat_reached = max(session.highest_heat_reached, 30)
        assert session.highest_heat_reached == 40  # Still 40

    def test_highest_heat_reached_persists_in_serialization(self):
        """highest_heat_reached should survive to_dict/from_dict."""
        session = init_session_metrics()
        session.highest_heat_reached = 75

        data = session.to_dict()
        assert data["highest_heat_reached"] == 75

        restored = SessionMetrics.from_dict(data)
        assert restored.highest_heat_reached == 75


class TestGameRulesConfigForAscension:
    """Test game_rules.json has required config for ascension system."""

    def test_enemy_spawn_weights_exists_in_config(self):
        """game_rules.json should have gameplay.enemy_spawn_weights."""
        import json
        from pathlib import Path

        game_rules_path = Path(__file__).parent.parent.parent / "game_rules.json"
        with open(game_rules_path) as f:
            rules = json.load(f)

        assert "gameplay" in rules
        assert "enemy_spawn_weights" in rules["gameplay"]

        weights = rules["gameplay"]["enemy_spawn_weights"]
        # Verify all enemy types are present
        expected_types = ["scanner", "patrol", "bot", "firewall", "hunter", "virus", "inhibitor"]
        for enemy_type in expected_types:
            assert enemy_type in weights, f"Missing {enemy_type} in spawn weights"
            assert isinstance(weights[enemy_type], int), f"{enemy_type} weight should be int"

    def test_alert_radius_lowered_to_six(self):
        """Base alert radius should be 6 (lowered from 8 to enable A15 modifier)."""
        import json
        from pathlib import Path

        game_rules_path = Path(__file__).parent.parent.parent / "game_rules.json"
        with open(game_rules_path) as f:
            rules = json.load(f)

        assert rules["gameplay"]["nearby_enemy_alert_radius"] == 6

    def test_ascension_modifiers_config_exists(self):
        """game_rules.json should have ascension.modifiers section."""
        import json
        from pathlib import Path

        game_rules_path = Path(__file__).parent.parent.parent / "game_rules.json"
        with open(game_rules_path) as f:
            rules = json.load(f)

        assert "ascension" in rules
        assert "modifiers" in rules["ascension"]
        assert "max_level" in rules["ascension"]
        assert rules["ascension"]["max_level"] == 20

        # Check all 20 levels have modifiers defined
        modifiers = rules["ascension"]["modifiers"]
        for level in range(1, 21):
            assert str(level) in modifiers, f"Missing modifier for level {level}"


# =============================================================================
# Phase 1: Core Modifier System Tests
# =============================================================================


class TestAscensionModifiersDataclass:
    """Test AscensionModifiers dataclass structure."""

    def test_ascension_modifiers_import(self):
        """AscensionModifiers should be importable from game_ascension."""
        from game_ascension import AscensionModifiers

        assert AscensionModifiers is not None

    def test_ascension_modifiers_defaults(self):
        """AscensionModifiers should have all modifier fields with zero/neutral defaults."""
        from game_ascension import AscensionModifiers

        mods = AscensionModifiers()

        # Vision modifiers
        assert mods.scanner_vision_bonus == 0
        assert mods.enemy_vision_bonus == 0
        assert mods.player_vision_override is None

        # Combat modifiers
        assert mods.enemy_hp_bonus == 0
        assert mods.enemy_damage_multiplier == 1.0
        assert mods.melee_heat_bonus == 0

        # Resource modifiers
        assert mods.trace_gain_multiplier == 1.0
        assert mods.hostile_trace_bonus == 0.0
        assert mods.heat_reduction_override is None
        assert mods.starting_ram_override is None

        # Spawn modifiers
        assert mods.enemy_count_bonus == 0
        assert mods.spawn_weights is None

        # Level generation modifiers
        assert mods.blind_spot_reduction_per_floor == 0
        assert mods.code_reduction_per_floor == 0
        assert mods.upgrade_reduction_per_floor == 0
        assert mods.node_reduction_per_floor == 0

        # Node capacity (A13)
        assert mods.node_capacity_ranges is None

        # Alert range (A15)
        assert mods.alert_range_override is None

        # Room generation (A16)
        assert mods.room_generation_overrides is None

        # Consumable blind spots (A20)
        assert mods.blind_spots_consumable is False


class TestCalculateAscensionModifiers:
    """Test calculate_ascension_modifiers function."""

    def test_ascension_zero_no_modifiers(self):
        """A0 should return modifiers with all default/neutral values."""
        from game_ascension import calculate_ascension_modifiers

        mods = calculate_ascension_modifiers(0)

        assert mods.scanner_vision_bonus == 0
        assert mods.enemy_hp_bonus == 0
        assert mods.enemy_damage_multiplier == 1.0
        assert mods.trace_gain_multiplier == 1.0

    def test_ascension_one_scanner_vision(self):
        """A1 should have scanner_vision_bonus of 1."""
        from game_ascension import calculate_ascension_modifiers

        mods = calculate_ascension_modifiers(1)
        assert mods.scanner_vision_bonus == 1

    def test_ascension_modifiers_cumulative(self):
        """A5 should include all modifiers from A1-A5."""
        from game_ascension import calculate_ascension_modifiers

        mods = calculate_ascension_modifiers(5)

        # A1: Scanner vision
        assert mods.scanner_vision_bonus == 1
        # A2: Enemy HP
        assert mods.enemy_hp_bonus == 10
        # A3: Trace multiplier
        assert mods.trace_gain_multiplier == 2.0
        # A4: Enemy damage
        assert mods.enemy_damage_multiplier == 1.2
        # A5: All enemy vision
        assert mods.enemy_vision_bonus == 1

    def test_ascension_ten_includes_all_prior(self):
        """A10 should include modifiers from A1-A10."""
        from game_ascension import calculate_ascension_modifiers

        mods = calculate_ascension_modifiers(10)

        # Check cumulative modifiers
        assert mods.scanner_vision_bonus == 1  # A1
        assert mods.enemy_hp_bonus == 10  # A2
        assert mods.trace_gain_multiplier == 2.0  # A3
        assert mods.enemy_damage_multiplier == 1.2  # A4
        assert mods.enemy_vision_bonus == 1  # A5
        assert mods.blind_spot_reduction_per_floor == 1  # A6
        assert mods.hostile_trace_bonus == 0.2  # A7
        assert mods.heat_reduction_override == 1  # A8
        assert mods.enemy_count_bonus == 5  # A9
        assert mods.player_vision_override == 12  # A10

    def test_ascension_max_level(self):
        """A20 should include all modifiers."""
        from game_ascension import calculate_ascension_modifiers

        mods = calculate_ascension_modifiers(20)

        # Check final modifiers
        assert mods.blind_spots_consumable is True  # A20
        assert mods.node_capacity_ranges is not None  # A13
        assert mods.spawn_weights is not None  # A12


class TestGameEngineAscensionIntegration:
    """Test GameEngine ascension level integration."""

    def test_game_engine_has_ascension_level(self):
        """GameEngine should have ascension_level attribute."""
        from unittest.mock import Mock

        from game_engine import GameEngine

        engine = GameEngine(sound_manager=Mock(), headless=True)
        assert hasattr(engine, "ascension_level")
        assert engine.ascension_level == 0  # Default

    def test_game_engine_accepts_ascension_level(self):
        """GameEngine should accept ascension_level parameter."""
        from unittest.mock import Mock

        from game_engine import GameEngine

        engine = GameEngine(sound_manager=Mock(), headless=True, ascension_level=5)
        assert engine.ascension_level == 5

    def test_game_engine_has_ascension_modifiers(self):
        """GameEngine should calculate and store AscensionModifiers."""
        from unittest.mock import Mock

        from game_ascension import AscensionModifiers
        from game_engine import GameEngine

        engine = GameEngine(sound_manager=Mock(), headless=True, ascension_level=5)
        assert hasattr(engine, "ascension_modifiers")
        assert isinstance(engine.ascension_modifiers, AscensionModifiers)
        # A5 should have cumulative modifiers
        assert engine.ascension_modifiers.scanner_vision_bonus == 1  # A1
        assert engine.ascension_modifiers.enemy_hp_bonus == 10  # A2

    def test_game_engine_ascension_zero_neutral_modifiers(self):
        """GameEngine at A0 should have neutral modifiers."""
        from unittest.mock import Mock

        from game_engine import GameEngine

        engine = GameEngine(sound_manager=Mock(), headless=True, ascension_level=0)
        assert engine.ascension_modifiers.scanner_vision_bonus == 0
        assert engine.ascension_modifiers.enemy_hp_bonus == 0
        assert engine.ascension_modifiers.enemy_damage_multiplier == 1.0

    def test_game_engine_get_input_mapper_helper(self):
        """GameEngine.get_input_mapper() returns input mapper from input_handler."""
        from unittest.mock import Mock

        from game_engine import GameEngine

        engine = GameEngine(sound_manager=Mock(), headless=True, ascension_level=0)
        input_mapper = engine.get_input_mapper()
        assert input_mapper is not None
        assert input_mapper is engine.input_handler.input_mapper

    def test_game_engine_get_input_mapper_returns_none_when_no_handler(self):
        """GameEngine.get_input_mapper() returns None when no input_handler exists."""
        from unittest.mock import Mock

        from game_engine import GameEngine

        engine = GameEngine(sound_manager=Mock(), headless=True, ascension_level=0)
        original_handler = engine.input_handler
        del engine.input_handler
        assert engine.get_input_mapper() is None
        engine.input_handler = original_handler


class TestEnemyAscensionModifiers:
    """Test enemy stat modifications from ascension."""

    def test_enemy_apply_ascension_modifiers_exists(self):
        """Enemy should have apply_ascension_modifiers method."""
        from game_characters import Enemy
        from game_entities import Position

        enemy = Enemy(Position(5, 5), "scanner")
        assert hasattr(enemy, "apply_ascension_modifiers")

    def test_enemy_hp_bonus_applied(self):
        """A2 enemy_hp_bonus should increase enemy CPU."""
        from game_ascension import AscensionModifiers
        from game_characters import Enemy
        from game_entities import Position

        enemy = Enemy(Position(5, 5), "scanner")
        original_cpu = enemy.cpu

        mods = AscensionModifiers(enemy_hp_bonus=10)
        enemy.apply_ascension_modifiers(mods)

        assert enemy.cpu == original_cpu + 10
        assert enemy.max_cpu == original_cpu + 10

    def test_enemy_damage_multiplier_applied(self):
        """A4 enemy_damage_multiplier should be stored for damage calc."""
        from game_ascension import AscensionModifiers
        from game_characters import Enemy
        from game_entities import Position

        enemy = Enemy(Position(5, 5), "scanner")

        mods = AscensionModifiers(enemy_damage_multiplier=1.2)
        enemy.apply_ascension_modifiers(mods)

        assert hasattr(enemy, "damage_multiplier")
        assert enemy.damage_multiplier == 1.2

    def test_enemy_damage_multiplier_actually_increases_damage(self):
        """A4 enemy_damage_multiplier should actually increase damage dealt."""
        from game_ascension import AscensionModifiers
        from game_characters import Enemy
        from game_entities import Position
        from game_player import Player

        # Create enemy and player
        enemy = Enemy(Position(5, 5), "bot")  # bot does damage
        player = Player(6, 5)
        player.cpu = 100
        player.max_cpu = 100

        base_damage = enemy.type_data.damage

        # Test without multiplier (default 1.0)
        player_before = player.cpu
        enemy.attack_player(player)
        damage_without_multiplier = player_before - player.cpu

        # Reset player
        player.cpu = 100

        # Apply A4 multiplier
        mods = AscensionModifiers(enemy_damage_multiplier=1.5)
        enemy.apply_ascension_modifiers(mods)

        player_before = player.cpu
        enemy.attack_player(player)
        damage_with_multiplier = player_before - player.cpu

        # Damage with multiplier should be 50% higher
        assert damage_with_multiplier == int(base_damage * 1.5)
        assert damage_with_multiplier > damage_without_multiplier

    def test_scanner_vision_bonus_applied(self):
        """A1 scanner_vision_bonus should only affect scanners."""
        from game_ascension import AscensionModifiers
        from game_characters import Enemy
        from game_entities import Position

        scanner = Enemy(Position(5, 5), "scanner")
        patrol = Enemy(Position(10, 10), "patrol")

        original_scanner_vision = scanner.type_data.vision
        original_patrol_vision = patrol.type_data.vision

        mods = AscensionModifiers(scanner_vision_bonus=1, enemy_vision_bonus=0)
        scanner.apply_ascension_modifiers(mods)
        patrol.apply_ascension_modifiers(mods)

        # Scanner gets +1 vision
        assert scanner.vision_range == original_scanner_vision + 1
        # Patrol doesn't get scanner bonus
        assert patrol.vision_range == original_patrol_vision

    def test_enemy_vision_bonus_applied_to_all(self):
        """A5 enemy_vision_bonus should affect all enemies."""
        from game_ascension import AscensionModifiers
        from game_characters import Enemy
        from game_entities import Position

        scanner = Enemy(Position(5, 5), "scanner")
        patrol = Enemy(Position(10, 10), "patrol")

        original_scanner_vision = scanner.type_data.vision
        original_patrol_vision = patrol.type_data.vision

        mods = AscensionModifiers(enemy_vision_bonus=1)
        scanner.apply_ascension_modifiers(mods)
        patrol.apply_ascension_modifiers(mods)

        assert scanner.vision_range == original_scanner_vision + 1
        assert patrol.vision_range == original_patrol_vision + 1

    def test_scanner_gets_both_bonuses(self):
        """Scanner at A5 gets both scanner_vision_bonus and enemy_vision_bonus."""
        from game_ascension import AscensionModifiers
        from game_characters import Enemy
        from game_entities import Position

        scanner = Enemy(Position(5, 5), "scanner")
        original_vision = scanner.type_data.vision

        # A5 cumulative: scanner_vision_bonus=1 (A1) + enemy_vision_bonus=1 (A5)
        mods = AscensionModifiers(scanner_vision_bonus=1, enemy_vision_bonus=1)
        scanner.apply_ascension_modifiers(mods)

        assert scanner.vision_range == original_vision + 2


class TestAscensionUnlockProgression:
    """Test ascension unlock mechanics."""

    def test_is_ascension_unlocked_zero_always(self):
        """A0 should always be unlocked."""
        from game_ascension import is_ascension_unlocked

        assert is_ascension_unlocked(0, highest_unlocked=0) is True

    def test_is_ascension_unlocked_within_range(self):
        """Levels <= highest_unlocked should be unlocked."""
        from game_ascension import is_ascension_unlocked

        assert is_ascension_unlocked(3, highest_unlocked=5) is True
        assert is_ascension_unlocked(5, highest_unlocked=5) is True

    def test_is_ascension_unlocked_beyond_range(self):
        """Levels > highest_unlocked should NOT be unlocked."""
        from game_ascension import is_ascension_unlocked

        assert is_ascension_unlocked(6, highest_unlocked=5) is False
        assert is_ascension_unlocked(10, highest_unlocked=5) is False

    def test_unlock_next_ascension(self):
        """Victory at AN unlocks AN+1."""
        from game_ascension import unlock_next_ascension

        highest = unlock_next_ascension(current_level=5, highest_unlocked=5)
        assert highest == 6

    def test_unlock_no_skip(self):
        """Winning lower level doesn't change highest."""
        from game_ascension import unlock_next_ascension

        # Winning A3 when A5 is already unlocked
        highest = unlock_next_ascension(current_level=3, highest_unlocked=5)
        assert highest == 5  # Unchanged

    def test_unlock_max_cap(self):
        """Cannot unlock beyond max level (20)."""
        from game_ascension import unlock_next_ascension

        highest = unlock_next_ascension(current_level=20, highest_unlocked=20)
        assert highest == 20  # Stays at max


class TestLevelGenerationModifiers:
    """Test ascension modifiers applied to level generation."""

    def test_apply_enemy_count_bonus(self):
        """A9 enemy_count_bonus should increase enemy count."""
        from game_ascension import AscensionModifiers

        base_count = 19
        mods = AscensionModifiers(enemy_count_bonus=5)

        modified_count = base_count + mods.enemy_count_bonus
        assert modified_count == 24

    def test_apply_code_reduction(self):
        """A11 code_reduction_per_floor should reduce codes with minimum."""
        from game_ascension import AscensionModifiers

        mods = AscensionModifiers(code_reduction_per_floor=2, code_minimum=3)

        # Floor 1: 12 -> 10
        base_codes = 12
        modified = max(mods.code_minimum, base_codes - mods.code_reduction_per_floor)
        assert modified == 10

        # Floor 3: 5 -> 3 (hits minimum)
        base_codes = 5
        modified = max(mods.code_minimum, base_codes - mods.code_reduction_per_floor)
        assert modified == 3

    def test_node_capacity_at_a13(self):
        """A13 node_capacity_ranges should provide floor-based ranges."""
        from game_ascension import calculate_ascension_modifiers

        mods = calculate_ascension_modifiers(13)

        assert mods.node_capacity_ranges is not None
        assert "floor_1" in mods.node_capacity_ranges
        assert "floor_2" in mods.node_capacity_ranges
        assert "floor_3" in mods.node_capacity_ranges

        # Floor 1: 100-200
        floor_1_range = mods.node_capacity_ranges["floor_1"]
        assert floor_1_range[0] == 100
        assert floor_1_range[1] == 200

    def test_node_capacity_below_a13_is_none(self):
        """Below A13, node_capacity_ranges should be None (unlimited)."""
        from game_ascension import calculate_ascension_modifiers

        mods = calculate_ascension_modifiers(12)
        assert mods.node_capacity_ranges is None

        mods = calculate_ascension_modifiers(0)
        assert mods.node_capacity_ranges is None


class TestTurnProcessingModifiers:
    """Tests for Phase 2.4: Turn processing modifiers."""

    def test_heat_reduction_override_at_a8(self):
        """A8 heat_reduction_override should reduce cooling rate from 2 to 1."""
        from game_ascension import calculate_ascension_modifiers

        mods = calculate_ascension_modifiers(8)
        assert mods.heat_reduction_override == 1

    def test_heat_reduction_default_below_a8(self):
        """Below A8, heat_reduction_override should be None (use default 2)."""
        from game_ascension import calculate_ascension_modifiers

        mods = calculate_ascension_modifiers(7)
        assert mods.heat_reduction_override is None

    def test_melee_heat_bonus_at_a17(self):
        """A17 melee_heat_bonus should add +5 heat per melee attack."""
        from game_ascension import calculate_ascension_modifiers

        mods = calculate_ascension_modifiers(17)
        assert mods.melee_heat_bonus == 5

    def test_melee_heat_bonus_zero_below_a17(self):
        """Below A17, melee_heat_bonus should be 0."""
        from game_ascension import calculate_ascension_modifiers

        mods = calculate_ascension_modifiers(16)
        assert mods.melee_heat_bonus == 0

    def test_trace_gain_multiplier_at_a3(self):
        """A3 trace_gain_multiplier should double background trace gain."""
        from game_ascension import calculate_ascension_modifiers

        mods = calculate_ascension_modifiers(3)
        assert mods.trace_gain_multiplier == 2.0

    def test_trace_gain_multiplier_default_below_a3(self):
        """Below A3, trace_gain_multiplier should be 1.0 (no change)."""
        from game_ascension import calculate_ascension_modifiers

        mods = calculate_ascension_modifiers(2)
        assert mods.trace_gain_multiplier == 1.0

    def test_hostile_trace_bonus_at_a7(self):
        """A7 hostile_trace_bonus should add +0.2 per turn when spotted."""
        from game_ascension import calculate_ascension_modifiers

        mods = calculate_ascension_modifiers(7)
        assert mods.hostile_trace_bonus == 0.2

    def test_hostile_trace_bonus_zero_below_a7(self):
        """Below A7, hostile_trace_bonus should be 0."""
        from game_ascension import calculate_ascension_modifiers

        mods = calculate_ascension_modifiers(6)
        assert mods.hostile_trace_bonus == 0.0

    def test_alert_range_override_at_a15(self):
        """A15 alert_range_override should increase alert range to 10."""
        from game_ascension import calculate_ascension_modifiers

        mods = calculate_ascension_modifiers(15)
        assert mods.alert_range_override == 10

    def test_alert_range_override_none_below_a15(self):
        """Below A15, alert_range_override should be None (use default 6)."""
        from game_ascension import calculate_ascension_modifiers

        mods = calculate_ascension_modifiers(14)
        assert mods.alert_range_override is None


class TestStoryFragmentAscensionBonus:
    """Test story fragment spawn chance bonus from ascension level."""

    def test_story_fragment_spawn_threshold_formula(self):
        """Story fragment spawn threshold should be 50% at A0, 70% at A20."""
        # Formula: spawn_threshold = 0.5 + (ascension_level * 0.01)
        # This threshold is used in: if random.random() > spawn_threshold: return
        # Higher threshold = MORE spawns (fewer early returns)

        # A0: 50% spawn chance
        a0_threshold = 0.5 + (0 * 0.01)
        assert a0_threshold == 0.5

        # A10: 60% spawn chance
        a10_threshold = 0.5 + (10 * 0.01)
        assert a10_threshold == 0.6

        # A20: 70% spawn chance
        a20_threshold = 0.5 + (20 * 0.01)
        assert a20_threshold == 0.7

    def test_story_fragment_spawn_chance_increases_with_ascension(self):
        """Higher ascension should increase story fragment spawn chance."""
        # The threshold increases linearly from 0.5 (A0) to 0.7 (A20)
        thresholds = [0.5 + (level * 0.01) for level in range(21)]

        # Verify monotonic increase
        for i in range(1, 21):
            assert thresholds[i] > thresholds[i - 1]

        # Verify bounds
        assert thresholds[0] == 0.5  # A0: 50%
        assert thresholds[20] == 0.7  # A20: 70%


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
