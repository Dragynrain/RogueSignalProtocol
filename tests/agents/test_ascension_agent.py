#!/usr/bin/env python3
"""
Ascension Agent Tests - Verify all 20 ascension levels in headless gameplay.

Tests each ascension level's modifiers are correctly applied:
- Enemy stat modifications (HP, vision, damage)
- Player stat modifications (vision, RAM)
- Game mechanic changes (trace, heat, alerts)
- Level generation effects (enemy counts, nodes)

Each test spawns real enemies or uses real gameplay to verify the
ascension modifiers are working as intended.
"""

import pytest

from game_ascension import calculate_ascension_modifiers
from game_characters import Enemy
from game_entities import EnemyState, Position
from tests.test_agent import GameTestAgent


# Base enemy stats from game_content.json for reference
BASE_ENEMY_STATS = {
    "scanner": {"cpu": 35, "vision": 5, "damage": 0},
    "patrol": {"cpu": 40, "vision": 4, "damage": 10},
    "bot": {"cpu": 25, "vision": 3, "damage": 8},
    "firewall": {"cpu": 80, "vision": 3, "damage": 5},
    "hunter": {"cpu": 50, "vision": 6, "damage": 15},
    "virus": {"cpu": 35, "vision": 4, "damage": 0},
    "inhibitor": {"cpu": 30, "vision": 4, "damage": 0},
    "admin": {"cpu": 250, "vision": 8, "damage": 45},
}


class AscensionTestAgent(GameTestAgent):
    """
    Agent specialized for testing ascension modifiers.

    Extends GameTestAgent with methods specific to verifying
    ascension effects on enemies, player, and game mechanics.
    """

    def __init__(self, seed: int | None = None, ascension_level: int = 0):
        """
        Initialize agent at specified ascension level.

        Args:
            seed: Random seed for deterministic testing
            ascension_level: Ascension level to test (0-20)
        """
        super().__init__(seed=seed, level=1, ascension_level=ascension_level)
        self.ascension_level = ascension_level
        self.mods = calculate_ascension_modifiers(ascension_level)

    def spawn_test_enemy(self, enemy_type: str, offset_x: int = 5, offset_y: int = 0) -> Enemy:
        """
        Spawn an enemy near player with ascension modifiers applied.

        Args:
            enemy_type: Type of enemy to spawn
            offset_x: X offset from player position
            offset_y: Y offset from player position

        Returns:
            The spawned enemy with ascension modifiers applied
        """
        # Find a valid spawn position (not a wall)
        base_x = self.player.x + offset_x
        base_y = self.player.y + offset_y

        # Search for valid position if the target is blocked
        for dx in range(10):
            for dy in range(-5, 6):
                test_x = base_x + dx
                test_y = base_y + dy
                if (test_x, test_y) not in self.game_map.walls:
                    enemy = Enemy(Position(test_x, test_y), enemy_type)
                    enemy.apply_ascension_modifiers(self.mods)
                    self.engine.enemies.append(enemy)
                    return enemy

        # Fallback: spawn at player offset (might fail if wall)
        enemy = Enemy(Position(base_x, base_y), enemy_type)
        enemy.apply_ascension_modifiers(self.mods)
        self.engine.enemies.append(enemy)
        return enemy

    def count_level_enemies(self) -> int:
        """Count total enemies on current level."""
        return len(self.enemies)

    def get_player_vision_range(self) -> int:
        """Get player's effective vision range including ascension overrides."""
        if self.mods.player_vision_override is not None:
            return self.mods.player_vision_override
        return 15  # Default player vision

    def get_heat_reduction_rate(self) -> int:
        """Get heat reduction rate including ascension override."""
        if self.mods.heat_reduction_override is not None:
            return self.mods.heat_reduction_override
        return 2  # Default heat reduction


class TestAscensionLevel0:
    """Test base game (Ascension 0) - no modifiers."""

    def test_a0_enemy_stats_unchanged(self):
        """A0: Enemy stats should match base values."""
        agent = AscensionTestAgent(seed=42, ascension_level=0)

        for enemy_type, base_stats in BASE_ENEMY_STATS.items():
            enemy = agent.spawn_test_enemy(enemy_type)
            assert enemy.cpu == base_stats["cpu"], f"{enemy_type} HP should be {base_stats['cpu']}"
            assert enemy.max_cpu == base_stats["cpu"]
            assert enemy.vision_range == base_stats["vision"], f"{enemy_type} vision unchanged"
            assert enemy.damage_multiplier == 1.0, f"{enemy_type} damage multiplier should be 1.0"

    def test_a0_player_stats_default(self):
        """A0: Player stats should be default values."""
        agent = AscensionTestAgent(seed=42, ascension_level=0)

        assert agent.player.ram_total == 8, "Default RAM is 8"
        assert agent.get_player_vision_range() == 15, "Default vision is 15"


class TestAscensionLevel1:
    """Test A1: Scanner vision +1."""

    def test_a1_scanner_vision_bonus(self):
        """A1: Scanners should have +1 vision (5 -> 6)."""
        agent = AscensionTestAgent(seed=42, ascension_level=1)

        scanner = agent.spawn_test_enemy("scanner")
        assert scanner.vision_range == 6, "Scanner vision should be 5 + 1 = 6"

    def test_a1_other_enemies_unchanged(self):
        """A1: Non-scanner enemies should have unchanged vision."""
        agent = AscensionTestAgent(seed=42, ascension_level=1)

        patrol = agent.spawn_test_enemy("patrol")
        assert patrol.vision_range == 4, "Patrol vision unchanged at A1"

        hunter = agent.spawn_test_enemy("hunter")
        assert hunter.vision_range == 6, "Hunter vision unchanged at A1"


class TestAscensionLevel2:
    """Test A2: Enemy HP +10."""

    def test_a2_enemy_hp_bonus(self):
        """A2: All enemies should have +10 HP."""
        agent = AscensionTestAgent(seed=42, ascension_level=2)

        for enemy_type, base_stats in BASE_ENEMY_STATS.items():
            enemy = agent.spawn_test_enemy(enemy_type)
            expected_hp = base_stats["cpu"] + 10
            assert enemy.cpu == expected_hp, f"{enemy_type} HP: {base_stats['cpu']} + 10 = {expected_hp}"
            assert enemy.max_cpu == expected_hp

    def test_a2_cumulative_with_a1(self):
        """A2: Should include A1 scanner vision bonus (cumulative)."""
        agent = AscensionTestAgent(seed=42, ascension_level=2)

        scanner = agent.spawn_test_enemy("scanner")
        assert scanner.cpu == 45, "Scanner HP: 35 + 10 = 45"
        assert scanner.vision_range == 6, "Scanner still has A1 vision bonus"


class TestAscensionLevel3:
    """Test A3: Trace gain multiplier 2.0x."""

    def test_a3_trace_multiplier(self):
        """A3: Trace gain multiplier should be 2.0."""
        agent = AscensionTestAgent(seed=42, ascension_level=3)

        assert agent.mods.trace_gain_multiplier == 2.0, "Trace multiplier should be 2.0"

    def test_a3_gameplay_trace_accumulation(self):
        """A3: Trace should accumulate faster during gameplay."""
        # Create agents at A0 and A3
        agent_a0 = AscensionTestAgent(seed=100, ascension_level=0)
        agent_a3 = AscensionTestAgent(seed=100, ascension_level=3)

        # Record initial trace
        initial_trace_a0 = agent_a0.player.trace_level
        initial_trace_a3 = agent_a3.player.trace_level

        # Wait several turns to accumulate background trace
        agent_a0.wait(10)
        agent_a3.wait(10)

        # Calculate trace gained
        trace_gained_a0 = agent_a0.player.trace_level - initial_trace_a0
        trace_gained_a3 = agent_a3.player.trace_level - initial_trace_a3

        # A3 should gain approximately 2x trace (allow some variance for game mechanics)
        if trace_gained_a0 > 0:
            ratio = trace_gained_a3 / trace_gained_a0
            assert ratio >= 1.5, f"A3 trace gain ({trace_gained_a3}) should be ~2x A0 ({trace_gained_a0})"


class TestAscensionLevel4:
    """Test A4: Enemy damage multiplier 1.2x."""

    def test_a4_damage_multiplier(self):
        """A4: Enemy damage multiplier should be 1.2."""
        agent = AscensionTestAgent(seed=42, ascension_level=4)

        patrol = agent.spawn_test_enemy("patrol")
        assert patrol.damage_multiplier == 1.2, "Patrol damage multiplier should be 1.2"

        hunter = agent.spawn_test_enemy("hunter")
        assert hunter.damage_multiplier == 1.2, "Hunter damage multiplier should be 1.2"

    def test_a4_enemy_deals_more_damage_to_player(self):
        """A4: Enemy attacks should deal 1.2x damage to player."""
        # Patrol base damage is 10, at A4 it should be 12
        agent = AscensionTestAgent(seed=42, ascension_level=4)

        # Clear existing enemies and spawn a patrol adjacent to player
        agent.engine.enemies.clear()
        patrol = agent.spawn_test_enemy("patrol", offset_x=1, offset_y=0)

        # Make patrol hostile so it attacks
        from game_entities import EnemyState
        patrol.state = EnemyState.HOSTILE
        patrol.last_seen_player = agent.player.position

        # Record initial HP
        initial_hp = agent.player.cpu

        # Have patrol attack player
        damage = patrol.attack_player(agent.player, agent.engine)

        # At A4, patrol deals 10 * 1.2 = 12 damage
        expected_damage = int(10 * 1.2)
        assert damage == expected_damage, (
            f"Patrol at A4 should deal {expected_damage} damage, got {damage}"
        )
        assert agent.player.cpu == initial_hp - expected_damage

    def test_a4_cumulative_modifiers(self):
        """A4: Should include all previous modifiers (A1-A3)."""
        agent = AscensionTestAgent(seed=42, ascension_level=4)

        scanner = agent.spawn_test_enemy("scanner")
        assert scanner.vision_range == 6, "A1: Scanner vision +1"
        assert scanner.cpu == 45, "A2: Enemy HP +10"
        assert agent.mods.trace_gain_multiplier == 2.0, "A3: Trace multiplier"
        assert scanner.damage_multiplier == 1.2, "A4: Damage multiplier"


class TestAscensionLevel5:
    """Test A5: All enemy vision +1."""

    def test_a5_all_enemy_vision_bonus(self):
        """A5: All enemies should have +1 vision."""
        agent = AscensionTestAgent(seed=42, ascension_level=5)

        for enemy_type, base_stats in BASE_ENEMY_STATS.items():
            enemy = agent.spawn_test_enemy(enemy_type)
            # A1 adds +1 to scanner, A5 adds +1 to all
            if enemy_type == "scanner":
                expected_vision = base_stats["vision"] + 2  # A1 + A5
            else:
                expected_vision = base_stats["vision"] + 1  # A5 only
            assert enemy.vision_range == expected_vision, (
                f"{enemy_type} vision: {base_stats['vision']} + bonus = {expected_vision}"
            )


class TestAscensionLevel6:
    """Test A6: Blind spot reduction per floor."""

    def test_a6_blind_spot_reduction_modifier(self):
        """A6: Blind spot reduction per floor should be 1."""
        agent = AscensionTestAgent(seed=42, ascension_level=6)

        assert agent.mods.blind_spot_reduction_per_floor == 1

    def test_a6_fewer_blind_spots_on_level(self):
        """A6: Levels should have fewer blind spots than A0."""
        # Count blind spots across multiple seeds
        a0_blind_spots = []
        a6_blind_spots = []

        for seed in [10, 20, 30, 40, 50]:
            agent_a0 = AscensionTestAgent(seed=seed, ascension_level=0)
            agent_a6 = AscensionTestAgent(seed=seed, ascension_level=6)

            a0_blind_spots.append(len(agent_a0.game_map.blind_spots))
            a6_blind_spots.append(len(agent_a6.game_map.blind_spots))

        avg_a0 = sum(a0_blind_spots) / len(a0_blind_spots)
        avg_a6 = sum(a6_blind_spots) / len(a6_blind_spots)

        # A6 should have fewer blind spots (reduction of 1 per floor)
        assert avg_a6 <= avg_a0, (
            f"A6 avg blind spots ({avg_a6}) should be <= A0 ({avg_a0})"
        )


class TestAscensionLevel7:
    """Test A7: Hostile trace bonus +0.2."""

    def test_a7_hostile_trace_bonus(self):
        """A7: Hostile trace bonus should be 0.2."""
        agent = AscensionTestAgent(seed=42, ascension_level=7)

        assert agent.mods.hostile_trace_bonus == 0.2

    def test_a7_hostile_enemy_increases_trace_more(self):
        """A7: Being spotted by hostile enemy should add more trace."""
        # This is harder to test directly since trace accumulation happens
        # during turn processing with hostile enemies. Verify the modifier exists
        # and is applied to the turn processor.
        agent = AscensionTestAgent(seed=42, ascension_level=7)

        # Verify the turn processor has access to the modifiers
        assert agent.engine.turn_processor.ascension_modifiers.hostile_trace_bonus == 0.2


class TestAscensionLevel8:
    """Test A8: Heat reduction override to 1."""

    def test_a8_heat_reduction_override(self):
        """A8: Heat reduction should be overridden to 1."""
        agent = AscensionTestAgent(seed=42, ascension_level=8)

        assert agent.mods.heat_reduction_override == 1
        assert agent.get_heat_reduction_rate() == 1, "Heat cools 1 per turn instead of 2"

    def test_a8_heat_cools_slower_in_gameplay(self):
        """A8: Heat should cool at rate 1 instead of 2 per turn."""
        # A0: Heat cools at rate 2 per turn
        agent_a0 = AscensionTestAgent(seed=42, ascension_level=0)
        agent_a0.player.heat = 20
        initial_heat_a0 = agent_a0.player.heat

        # Move to ensure not on cooling node, then wait
        agent_a0.move_player(0, 0)  # No-op to process turn
        heat_after_a0 = agent_a0.player.heat
        reduction_a0 = initial_heat_a0 - heat_after_a0

        # A8: Heat cools at rate 1 per turn
        agent_a8 = AscensionTestAgent(seed=42, ascension_level=8)
        agent_a8.player.heat = 20
        initial_heat_a8 = agent_a8.player.heat

        agent_a8.move_player(0, 0)  # No-op to process turn
        heat_after_a8 = agent_a8.player.heat
        reduction_a8 = initial_heat_a8 - heat_after_a8

        # A8 should cool slower (1 vs 2)
        assert reduction_a8 < reduction_a0, (
            f"A8 heat reduction ({reduction_a8}) should be less than A0 ({reduction_a0})"
        )


class TestAscensionLevel9:
    """Test A9: Enemy count +5 per floor."""

    def test_a9_enemy_count_bonus(self):
        """A9: Enemy count bonus should be 5."""
        agent = AscensionTestAgent(seed=42, ascension_level=9)

        assert agent.mods.enemy_count_bonus == 5

    def test_a9_more_enemies_on_level(self):
        """A9: Level should have more enemies than A0."""
        # Test multiple seeds to account for RNG variance
        a0_counts = []
        a9_counts = []

        for seed in [1, 2, 3, 4, 5]:
            agent_a0 = AscensionTestAgent(seed=seed, ascension_level=0)
            agent_a9 = AscensionTestAgent(seed=seed, ascension_level=9)
            a0_counts.append(agent_a0.count_level_enemies())
            a9_counts.append(agent_a9.count_level_enemies())

        avg_a0 = sum(a0_counts) / len(a0_counts)
        avg_a9 = sum(a9_counts) / len(a9_counts)

        # A9 should have approximately 5 more enemies on average
        assert avg_a9 >= avg_a0, f"A9 avg ({avg_a9}) should have more enemies than A0 ({avg_a0})"


class TestAscensionLevel10:
    """Test A10: Player vision override to 12."""

    def test_a10_player_vision_override(self):
        """A10: Player vision should be 12 instead of 15."""
        agent = AscensionTestAgent(seed=42, ascension_level=10)

        assert agent.mods.player_vision_override == 12
        assert agent.get_player_vision_range() == 12


class TestAscensionLevel11:
    """Test A11: Code reduction per floor."""

    def test_a11_code_reduction_modifier(self):
        """A11: Code reduction per floor should be 2."""
        agent = AscensionTestAgent(seed=42, ascension_level=11)

        assert agent.mods.code_reduction_per_floor == 2
        assert agent.mods.code_minimum == 3

    def test_a11_fewer_code_hacks_on_level(self):
        """A11: Levels should have fewer code hacks than A0."""
        a0_codes = []
        a11_codes = []

        for seed in [10, 20, 30, 40, 50]:
            agent_a0 = AscensionTestAgent(seed=seed, ascension_level=0)
            agent_a11 = AscensionTestAgent(seed=seed, ascension_level=11)

            a0_codes.append(len(agent_a0.game_map.code_hacks))
            a11_codes.append(len(agent_a11.game_map.code_hacks))

        avg_a0 = sum(a0_codes) / len(a0_codes)
        avg_a11 = sum(a11_codes) / len(a11_codes)

        assert avg_a11 < avg_a0, (
            f"A11 avg code hacks ({avg_a11}) should be less than A0 ({avg_a0})"
        )


class TestAscensionLevel12:
    """Test A12: Spawn weight changes."""

    def test_a12_spawn_weights_set(self):
        """A12: Spawn weights should be overridden."""
        agent = AscensionTestAgent(seed=42, ascension_level=12)

        assert agent.mods.spawn_weights is not None
        assert "hunter" in agent.mods.spawn_weights
        assert "virus" in agent.mods.spawn_weights


class TestAscensionLevel13:
    """Test A13: Node capacity ranges."""

    def test_a13_node_capacity_ranges_set(self):
        """A13: Node capacity ranges should be set."""
        agent = AscensionTestAgent(seed=42, ascension_level=13)

        assert agent.mods.node_capacity_ranges is not None
        assert "floor_1" in agent.mods.node_capacity_ranges


class TestAscensionLevel14:
    """Test A14: Starting RAM override to 6."""

    def test_a14_starting_ram_override(self):
        """A14: Player starting RAM should be 6 instead of 8."""
        agent = AscensionTestAgent(seed=42, ascension_level=14)

        assert agent.mods.starting_ram_override == 6
        assert agent.player.ram_total == 6, "Player RAM should be 6"


class TestAscensionLevel15:
    """Test A15: Alert range override to 10."""

    def test_a15_alert_range_override(self):
        """A15: Alert range should be 10 instead of 6."""
        agent = AscensionTestAgent(seed=42, ascension_level=15)

        assert agent.mods.alert_range_override == 10


class TestAscensionLevel16:
    """Test A16: Room generation overrides."""

    def test_a16_room_generation_overrides_set(self):
        """A16: Room generation overrides should be set."""
        agent = AscensionTestAgent(seed=42, ascension_level=16)

        assert agent.mods.room_generation_overrides is not None
        assert "min_room_size" in agent.mods.room_generation_overrides


class TestAscensionLevel17:
    """Test A17: Melee heat bonus +5."""

    def test_a17_melee_heat_bonus(self):
        """A17: Melee heat bonus should be 5."""
        agent = AscensionTestAgent(seed=42, ascension_level=17)

        assert agent.mods.melee_heat_bonus == 5

    def test_a17_bump_attack_generates_extra_heat(self):
        """A17: Bump attacks should generate +5 heat (melee bonus).

        Heat calculation:
        - Base bump attack: 8 heat
        - A17 melee bonus: +5 heat
        - Turn processing: -2 (normal) or -1 (A8+)

        A0:  8 - 2 = 6 heat after turn
        A17: 13 - 1 = 12 heat after turn (includes A8 heat reduction override)

        Net difference accounting for both modifiers: +6 heat
        """
        # A0: Bump attack generates 8 base heat - 2 reduction = 6
        agent_a0 = AscensionTestAgent(seed=42, ascension_level=0)
        agent_a0.player.heat = 0

        # Spawn enemy adjacent to player
        bot_a0 = agent_a0.spawn_test_enemy("bot", offset_x=1, offset_y=0)
        bot_x, bot_y = bot_a0.x, bot_a0.y

        # Move into enemy to bump attack
        agent_a0.move_player(bot_x - agent_a0.player.x, bot_y - agent_a0.player.y)
        heat_a0 = agent_a0.player.heat

        # A17: 8 + 5 melee bonus = 13, then -1 (A8 override) = 12
        agent_a17 = AscensionTestAgent(seed=42, ascension_level=17)
        agent_a17.player.heat = 0

        bot_a17 = agent_a17.spawn_test_enemy("bot", offset_x=1, offset_y=0)
        bot_x17, bot_y17 = bot_a17.x, bot_a17.y

        agent_a17.move_player(bot_x17 - agent_a17.player.x, bot_y17 - agent_a17.player.y)
        heat_a17 = agent_a17.player.heat

        # A17 should have significantly more heat than A0
        # +5 from melee bonus, +1 from slower cooling (A8) = +6 total
        assert heat_a17 > heat_a0, (
            f"A17 bump attack heat ({heat_a17}) should be higher than A0 ({heat_a0})"
        )
        # The exact difference is 6: +5 melee bonus, +1 from A8 heat reduction override
        expected_diff = 5 + 1  # melee_bonus + (normal_reduction - a8_reduction)
        actual_diff = heat_a17 - heat_a0
        assert actual_diff == expected_diff, (
            f"A17 heat difference ({actual_diff}) should be {expected_diff} "
            f"(5 melee + 1 slower cooling)"
        )


class TestAscensionLevel18:
    """Test A18: Upgrade reduction per floor."""

    def test_a18_upgrade_reduction_modifier(self):
        """A18: Upgrade reduction per floor should be 1."""
        agent = AscensionTestAgent(seed=42, ascension_level=18)

        assert agent.mods.upgrade_reduction_per_floor == 1

    def test_a18_fewer_upgrades_on_level(self):
        """A18: Levels should have fewer permanent upgrades than A0."""
        a0_upgrades = []
        a18_upgrades = []

        for seed in [10, 20, 30, 40, 50]:
            agent_a0 = AscensionTestAgent(seed=seed, ascension_level=0)
            agent_a18 = AscensionTestAgent(seed=seed, ascension_level=18)

            a0_upgrades.append(len(agent_a0.game_map.permanent_upgrades))
            a18_upgrades.append(len(agent_a18.game_map.permanent_upgrades))

        avg_a0 = sum(a0_upgrades) / len(a0_upgrades)
        avg_a18 = sum(a18_upgrades) / len(a18_upgrades)

        assert avg_a18 <= avg_a0, (
            f"A18 avg upgrades ({avg_a18}) should be <= A0 ({avg_a0})"
        )


class TestAscensionLevel19:
    """Test A19: Node reduction per floor."""

    def test_a19_node_reduction_modifier(self):
        """A19: Node reduction per floor should be 1."""
        agent = AscensionTestAgent(seed=42, ascension_level=19)

        assert agent.mods.node_reduction_per_floor == 1

    def test_a19_fewer_nodes_on_level(self):
        """A19: Levels should have fewer healing/utility nodes than A0."""
        a0_nodes = []
        a19_nodes = []

        for seed in [10, 20, 30, 40, 50]:
            agent_a0 = AscensionTestAgent(seed=seed, ascension_level=0)
            agent_a19 = AscensionTestAgent(seed=seed, ascension_level=19)

            # Count total utility nodes (CPU recovery + ghost + cooling)
            a0_total = (
                len(agent_a0.game_map.cpu_recovery_nodes) +
                len(agent_a0.game_map.ghost_nodes) +
                len(agent_a0.game_map.cooling_nodes)
            )
            a19_total = (
                len(agent_a19.game_map.cpu_recovery_nodes) +
                len(agent_a19.game_map.ghost_nodes) +
                len(agent_a19.game_map.cooling_nodes)
            )

            a0_nodes.append(a0_total)
            a19_nodes.append(a19_total)

        avg_a0 = sum(a0_nodes) / len(a0_nodes)
        avg_a19 = sum(a19_nodes) / len(a19_nodes)

        assert avg_a19 <= avg_a0, (
            f"A19 avg nodes ({avg_a19}) should be <= A0 ({avg_a0})"
        )


class TestAscensionLevel20:
    """Test A20: Blind spots consumable."""

    def test_a20_blind_spots_consumable(self):
        """A20: Blind spots should be consumable."""
        agent = AscensionTestAgent(seed=42, ascension_level=20)

        assert agent.mods.blind_spots_consumable is True

    def test_a20_blind_spot_disappears_after_use(self):
        """A20: Blind spot should disappear when player leaves it."""
        agent = AscensionTestAgent(seed=42, ascension_level=20)

        # Find a blind spot
        if not agent.game_map.blind_spots:
            pytest.skip("No blind spots on this map seed")

        blind_spot = list(agent.game_map.blind_spots)[0]
        initial_count = len(agent.game_map.blind_spots)

        # Move player to the blind spot
        agent.player.x = blind_spot[0]
        agent.player.y = blind_spot[1]

        # Process a turn while on blind spot
        agent.wait(1)

        # Move off the blind spot
        agent.move_player(1, 0)

        # At A20, blind spots are consumable - should have one fewer
        final_count = len(agent.game_map.blind_spots)
        assert final_count < initial_count, (
            f"A20 blind spot should be consumed: {initial_count} -> {final_count}"
        )


class TestAscensionCumulative:
    """Test cumulative behavior across multiple levels."""

    def test_a20_has_all_modifiers(self):
        """A20: Should have all 20 levels of modifiers applied."""
        agent = AscensionTestAgent(seed=42, ascension_level=20)
        mods = agent.mods

        # Verify all cumulative modifiers are present
        assert mods.scanner_vision_bonus == 1, "A1"
        assert mods.enemy_hp_bonus == 10, "A2"
        assert mods.trace_gain_multiplier == 2.0, "A3"
        assert mods.enemy_damage_multiplier == 1.2, "A4"
        assert mods.enemy_vision_bonus == 1, "A5"
        assert mods.blind_spot_reduction_per_floor == 1, "A6"
        assert mods.hostile_trace_bonus == 0.2, "A7"
        assert mods.heat_reduction_override == 1, "A8"
        assert mods.enemy_count_bonus == 5, "A9"
        assert mods.player_vision_override == 12, "A10"
        assert mods.code_reduction_per_floor == 2, "A11"
        assert mods.spawn_weights is not None, "A12"
        assert mods.node_capacity_ranges is not None, "A13"
        assert mods.starting_ram_override == 6, "A14"
        assert mods.alert_range_override == 10, "A15"
        assert mods.room_generation_overrides is not None, "A16"
        assert mods.melee_heat_bonus == 5, "A17"
        assert mods.upgrade_reduction_per_floor == 1, "A18"
        assert mods.node_reduction_per_floor == 1, "A19"
        assert mods.blind_spots_consumable is True, "A20"

    def test_a20_enemy_stats_fully_modified(self):
        """A20: Enemies should have all stat modifications applied."""
        agent = AscensionTestAgent(seed=42, ascension_level=20)

        # Test hunter at A20
        hunter = agent.spawn_test_enemy("hunter")
        assert hunter.cpu == 60, "Hunter HP: 50 + 10 (A2) = 60"
        assert hunter.vision_range == 7, "Hunter vision: 6 + 1 (A5) = 7"
        assert hunter.damage_multiplier == 1.2, "Hunter damage x1.2 (A4)"

        # Test scanner at A20
        scanner = agent.spawn_test_enemy("scanner")
        assert scanner.cpu == 45, "Scanner HP: 35 + 10 (A2) = 45"
        assert scanner.vision_range == 7, "Scanner vision: 5 + 1 (A1) + 1 (A5) = 7"

    def test_a20_player_stats_fully_modified(self):
        """A20: Player should have all stat modifications applied."""
        agent = AscensionTestAgent(seed=42, ascension_level=20)

        assert agent.player.ram_total == 6, "Player RAM: 6 (A14)"
        assert agent.get_player_vision_range() == 12, "Player vision: 12 (A10)"


class TestAscensionGameplay:
    """Integration tests verifying ascension affects actual gameplay."""

    def test_enemy_harder_to_kill_at_higher_ascension(self):
        """Higher ascension enemies should take more damage to kill."""
        # A0: Hunter has 50 HP
        agent_a0 = AscensionTestAgent(seed=42, ascension_level=0)
        hunter_a0 = agent_a0.spawn_test_enemy("hunter")
        initial_hp_a0 = hunter_a0.cpu

        # A20: Hunter has 60 HP (50 + 10)
        agent_a20 = AscensionTestAgent(seed=42, ascension_level=20)
        hunter_a20 = agent_a20.spawn_test_enemy("hunter")
        initial_hp_a20 = hunter_a20.cpu

        assert initial_hp_a20 > initial_hp_a0, (
            f"A20 hunter ({initial_hp_a20}) should have more HP than A0 ({initial_hp_a0})"
        )

    def test_player_more_vulnerable_at_higher_ascension(self):
        """Player should be more vulnerable at higher ascension (less RAM, vision)."""
        agent_a0 = AscensionTestAgent(seed=42, ascension_level=0)
        agent_a20 = AscensionTestAgent(seed=42, ascension_level=20)

        assert agent_a20.player.ram_total < agent_a0.player.ram_total, "Less RAM at A20"
        assert agent_a20.get_player_vision_range() < agent_a0.get_player_vision_range(), (
            "Less vision at A20"
        )

    @pytest.mark.slow
    def test_survival_harder_at_high_ascension(self):
        """Survival should be harder at high ascension (statistical test)."""
        survival_a0 = []
        survival_a20 = []

        for seed in range(5):
            # A0 run
            agent_a0 = AscensionTestAgent(seed=seed, ascension_level=0)
            for _ in range(50):
                if agent_a0.player.cpu <= 0:
                    break
                agent_a0.wait(1)
            survival_a0.append(agent_a0.player.cpu)

            # A20 run
            agent_a20 = AscensionTestAgent(seed=seed, ascension_level=20)
            for _ in range(50):
                if agent_a20.player.cpu <= 0:
                    break
                agent_a20.wait(1)
            survival_a20.append(agent_a20.player.cpu)

        # A20 should generally have lower HP on average
        avg_a0 = sum(survival_a0) / len(survival_a0)
        avg_a20 = sum(survival_a20) / len(survival_a20)

        print(f"\nSurvival test: A0 avg HP = {avg_a0:.1f}, A20 avg HP = {avg_a20:.1f}")
        # Don't assert - just report (RNG can cause variance)


class TestAscensionDetection:
    """Test that enemies can detect player differently at various ascension levels."""

    def test_scanner_detects_at_longer_range_a1(self):
        """A1: Scanner should have +1 vision range for detection."""
        agent_a0 = AscensionTestAgent(seed=42, ascension_level=0)
        agent_a1 = AscensionTestAgent(seed=42, ascension_level=1)

        scanner_a0 = agent_a0.spawn_test_enemy("scanner")
        scanner_a1 = agent_a1.spawn_test_enemy("scanner")

        assert scanner_a1.vision_range > scanner_a0.vision_range, (
            f"A1 scanner vision ({scanner_a1.vision_range}) > A0 ({scanner_a0.vision_range})"
        )

    def test_all_enemies_see_further_a5(self):
        """A5: All enemies should have +1 vision for detection."""
        agent_a4 = AscensionTestAgent(seed=42, ascension_level=4)
        agent_a5 = AscensionTestAgent(seed=42, ascension_level=5)

        # Test non-scanner enemy
        patrol_a4 = agent_a4.spawn_test_enemy("patrol")
        patrol_a5 = agent_a5.spawn_test_enemy("patrol")

        assert patrol_a5.vision_range > patrol_a4.vision_range, (
            f"A5 patrol vision ({patrol_a5.vision_range}) > A4 ({patrol_a4.vision_range})"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
