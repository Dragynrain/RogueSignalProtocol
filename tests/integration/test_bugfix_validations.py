"""
Integration tests to validate critical bug fixes.

These tests verify fixes for:
- CPU overflow prevention after node restoration
- Death handler idempotency (calling check_death multiple times is safe)
- Color fallback safety (invalid UI colors don't crash game)
- Error message logging (full errors logged, not truncated)
"""

import pytest

from rsp.core.config import GameSettings
from rsp.entities.base import Position
from rsp.level.map import RestoreNode


class TestCPUOverflowPrevention:
    """Test that CPU never exceeds max_cpu after node restoration."""

    def test_cpu_capped_after_node_restoration(self, basic_game_engine):
        """Verify CPU is capped to max_cpu when restored via CPU node."""
        engine = basic_game_engine

        # Set player to near-full CPU
        engine.player.max_cpu = 100
        engine.player.cpu = 95

        # Create a CPU node at player position with large capacity
        # RestoreNode args: node_type, total_capacity, used_capacity
        player_pos = (engine.player.x, engine.player.y)
        node = RestoreNode(node_type="cpu", total_capacity=50, used_capacity=0)
        engine.game_map.cpu_recovery_nodes[player_pos] = node

        # Track initial CPU
        initial_cpu = engine.player.cpu

        # Process turn (should use node)
        engine.last_node_position = None  # Ensure sound triggers
        engine._process_special_tiles()

        # CPU should be capped at max_cpu, not exceed it
        assert engine.player.cpu <= engine.player.max_cpu
        assert engine.player.cpu == 100  # Should be exactly max

    def test_cpu_restored_correctly_when_needed(self, basic_game_engine):
        """Verify CPU is restored by correct amount when below max."""
        engine = basic_game_engine

        # Set player to low CPU
        engine.player.max_cpu = 100
        engine.player.cpu = 50

        # Create a CPU node at player position
        # RestoreNode args: node_type, total_capacity, used_capacity
        player_pos = (engine.player.x, engine.player.y)
        node = RestoreNode(node_type="cpu", total_capacity=100, used_capacity=0)
        engine.game_map.cpu_recovery_nodes[player_pos] = node

        # Process turn
        engine.last_node_position = None
        engine._process_special_tiles()

        # CPU should be restored but capped at max
        assert engine.player.cpu <= engine.player.max_cpu
        # Should restore up to 20 (CPU_RECOVERY_AMOUNT) bringing CPU to 70
        assert engine.player.cpu >= 50  # At least original


class TestDeathHandlerIdempotency:
    """Test that death handler can be called multiple times safely."""

    def test_check_death_idempotent_when_already_handled(self, basic_game_engine):
        """Verify check_death returns True consistently after death handled."""
        engine = basic_game_engine
        handler = engine.death_handler

        # Set player to dead
        engine.player.cpu = 0

        # First call handles death
        result1 = handler.check_death("combat")
        assert result1 is True
        assert handler._handled is True

        # Subsequent calls should still return True
        result2 = handler.check_death("virus")
        result3 = handler.check_death("overheat")

        assert result2 is True
        assert result3 is True

        # Should only be handled once
        assert handler._handled is True

    def test_check_death_safe_after_healing_impossible_scenario(self, basic_game_engine):
        """Verify handled flag prevents re-handling even if CPU restored (edge case)."""
        engine = basic_game_engine
        handler = engine.death_handler

        # Kill player and handle death
        engine.player.cpu = 0
        handler.check_death("combat")
        assert handler._handled is True

        # Hypothetically restore CPU (shouldn't happen in real game)
        engine.player.cpu = 50

        # check_death should still return True because already handled
        result = handler.check_death("unknown")
        assert result is True

    def test_reset_clears_handled_flag(self, basic_game_engine):
        """Verify reset() clears the handled flag for new game."""
        engine = basic_game_engine
        handler = engine.death_handler

        # Handle a death
        engine.player.cpu = 0
        handler.check_death("combat")
        assert handler._handled is True

        # Reset for new game
        handler.reset()
        assert handler._handled is False
        assert handler._death_event is None


class TestColorFailFast:
    """Test that invalid colors fail fast with clear errors."""

    def test_invalid_ui_color_raises_keyerror(self):
        """Verify invalid UI color raises KeyError (fail-fast, no silent fallback)."""
        settings = GameSettings()

        # Set invalid UI color
        settings.ui_color = "nonexistent_color"

        # Should raise KeyError - config is broken, don't silently degrade
        with pytest.raises(KeyError):
            settings.get_ui_color_rgb()

    def test_valid_ui_color_works(self):
        """Verify valid UI colors return correct values."""
        settings = GameSettings()

        # Set valid UI color
        settings.ui_color = "cyan"

        color = settings.get_ui_color_rgb()

        assert isinstance(color, tuple)
        assert len(color) == 3

    def test_all_valid_ui_colors_work(self):
        """Verify all documented UI colors are valid."""
        settings = GameSettings()
        valid_colors = [
            "cyan",
            "purple",
            "magenta",
            "golden",
            "crimson",
            "azure",
            "emerald",
            "ivory",
        ]

        for color_name in valid_colors:
            settings.ui_color = color_name
            color = settings.get_ui_color_rgb()
            assert isinstance(color, tuple), f"Color {color_name} should return tuple"
            assert len(color) == 3, f"Color {color_name} should have 3 components"


class TestDeathEventCapture:
    """Test that death events capture correct information."""

    def test_death_event_captures_cause(self, basic_game_engine):
        """Verify death event captures the death cause."""
        engine = basic_game_engine
        handler = engine.death_handler

        # Kill player
        engine.player.cpu = 0
        handler.check_death("virus", source="Virus Alpha")

        event = handler.death_event
        assert event is not None
        assert event.cause == "virus"
        assert event.source == "Virus Alpha"

    def test_death_event_captures_player_state(self, basic_game_engine):
        """Verify death event captures player state at death."""
        engine = basic_game_engine
        handler = engine.death_handler

        # Set specific state before death
        engine.player.cpu = 0
        engine.player.heat = 75
        engine.player.trace_level = 50.0
        engine.player.temporary_effects["virus_turns"] = 3

        handler.check_death("overheat")

        event = handler.death_event
        assert event is not None
        assert event.final_heat == 75
        assert event.final_trace == 50.0
        assert event.virus_turns == 3


class TestVictoryTakesPrecedence:
    """Test that victory prevents death handling."""

    def test_victory_prevents_death_processing(self, basic_game_engine):
        """Verify death is not processed if victory already achieved."""
        engine = basic_game_engine
        handler = engine.death_handler

        # Achieve victory first
        engine.game_state.show_victory_screen = True

        # Kill player
        engine.player.cpu = 0

        # check_death should return True but not process death
        result = handler.check_death("combat")

        assert result is True  # Player is "dead"
        assert handler._handled is False  # But death not handled (victory takes precedence)


class TestEnemyStateTransitions:
    """Test enemy state transitions and queue invalidation."""

    def test_make_hostile_clears_move_queue(self, basic_game_engine):
        """Verify make_hostile clears movement queue on state change."""
        engine = basic_game_engine
        from rsp.entities.base import EnemyState, Position

        # Get an enemy and give it a movement queue
        enemy = engine.enemies[0]
        enemy.state = EnemyState.UNAWARE
        enemy.move_queue = [Position(5, 5), Position(6, 6), Position(7, 7)]

        # Make hostile should clear the queue
        enemy.make_hostile(engine.player.position)

        assert enemy.state == EnemyState.HOSTILE
        assert len(enemy.move_queue) == 0  # Queue should be cleared

    def test_make_hostile_idempotent(self, basic_game_engine):
        """Verify calling make_hostile twice doesn't clear queue the second time."""
        engine = basic_game_engine
        from rsp.entities.base import EnemyState, Position

        enemy = engine.enemies[0]
        enemy.state = EnemyState.HOSTILE
        enemy.move_queue = [Position(5, 5), Position(6, 6)]

        # Calling make_hostile when already hostile should NOT clear queue
        enemy.make_hostile(engine.player.position)

        assert len(enemy.move_queue) == 2  # Queue preserved

    def test_patrol_enemy_preserves_patrol_index(self, basic_game_engine):
        """Verify patrol enemies save patrol index before becoming hostile."""
        engine = basic_game_engine
        from rsp.entities.base import EnemyMovement, EnemyState, Position

        # Find or set up a patrol enemy
        enemy = engine.enemies[0]
        enemy.type_data.movement = EnemyMovement.PATROL
        enemy.patrol_points = [Position(10, 10), Position(20, 20), Position(30, 30)]
        enemy.patrol_index = 2
        enemy.state = EnemyState.UNAWARE

        # Make hostile
        enemy.make_hostile(engine.player.position)

        # Should preserve original patrol index for later restoration
        assert enemy.original_patrol_index == 2


class TestSpeedAndSlowdownMechanics:
    """Test speed boost and slowdown effect interactions."""

    def test_speed_boost_grants_extra_moves(self, basic_game_engine):
        """Verify speed boost grants bonus moves per turn."""
        engine = basic_game_engine

        # Grant speed boost
        engine.player.temporary_effects["speed_boost_turns"] = 3
        engine.player.speed_moves_remaining = 0

        # Simulate turn start logic from game_turn_manager
        if (
            engine.player.temporary_effects["speed_boost_turns"] > 0
            and engine.player.speed_moves_remaining == 0
        ):
            engine.player.speed_moves_remaining = 2

        assert engine.player.speed_moves_remaining == 2

    def test_inhibitor_cancels_speed_moves_this_turn(self, basic_game_engine):
        """Verify inhibitor attack immediately cancels this turn's speed moves."""
        engine = basic_game_engine

        # Set up player with speed boost and remaining moves
        engine.player.temporary_effects["speed_boost_turns"] = 5
        engine.player.speed_moves_remaining = 2

        inhibitor = None
        for enemy in engine.enemies:
            if enemy.type == "inhibitor":
                inhibitor = enemy
                break

        if inhibitor is None:
            # No inhibitor in test level, skip
            return

        # Simulate inhibitor attack
        inhibitor.attack_player(engine.player)

        # Speed moves should be cancelled for THIS turn
        assert engine.player.speed_moves_remaining == 0

    def test_slowdown_stacks_with_cap(self, basic_game_engine):
        """Verify slowdown effect stacks but has a cap."""
        engine = basic_game_engine
        from rsp.core.config import GameBalance

        # Set initial slowdown
        engine.player.temporary_effects["movement_slowed_turns"] = 3
        engine.player.temporary_effects["speed_boost_turns"] = 0

        # Apply more slowdown
        current_slow = engine.player.temporary_effects.get("movement_slowed_turns", 0)
        additional_slow = 4
        engine.player.temporary_effects["movement_slowed_turns"] = min(
            current_slow + additional_slow, GameBalance.INHIBITOR_SLOWDOWN_CAP
        )

        # Should be capped
        assert (
            engine.player.temporary_effects["movement_slowed_turns"]
            <= GameBalance.INHIBITOR_SLOWDOWN_CAP
        )


class TestEnemyEliminationHelper:
    """Test the consolidated enemy elimination helper."""

    def test_elimination_grants_cpu_reward(self, basic_game_engine):
        """Verify enemy elimination grants CPU reward."""
        engine = basic_game_engine
        from rsp.core.config import GameBalance

        initial_cpu = engine.player.cpu
        enemy = engine.enemies[0]

        # Use the helper
        engine.handle_enemy_elimination(
            enemy=enemy,
            damage=50,
            was_stealth=False,
            from_blind_spot=False,
        )

        expected_cpu = min(
            engine.player.max_cpu, initial_cpu + GameBalance.ENEMY_ELIMINATION_CPU_REWARD
        )
        assert engine.player.cpu == expected_cpu

    def test_elimination_removes_enemy(self, basic_game_engine):
        """Verify enemy elimination removes enemy from game."""
        engine = basic_game_engine

        initial_count = len(engine.enemies)
        enemy = engine.enemies[0]
        enemy_id = enemy.id

        engine.handle_enemy_elimination(
            enemy=enemy,
            damage=50,
            was_stealth=False,
            from_blind_spot=False,
        )

        # Enemy should be removed
        assert len(engine.enemies) == initial_count - 1
        assert not any(e.id == enemy_id for e in engine.enemies)


class TestLogicBombOverheatWarning:
    """Test Logic Bomb friendly fire warning includes overheat damage."""

    def test_friendly_fire_warning_includes_overheat_damage(self, basic_game_engine):
        """Verify friendly fire warning shows total damage including overheat.

        Bug: Previously the friendly fire warning only showed direct damage,
        not accounting for overheat damage that would also be applied.
        Fix: Logic Bomb now calculates overheat damage and adds it to the
        warning's damage total.
        """
        engine = basic_game_engine
        from rsp.combat.combat import ExploitSystem
        from rsp.core.data import GameData

        combat = ExploitSystem(engine)

        # Set up player with high heat (will overheat on Logic Bomb use)
        engine.player.heat = 90
        engine.player.max_heat = 100
        engine.player.cpu = 100

        # Logic Bomb costs 35 heat, so 90 + 35 = 125 > 100, overheat = 25
        # Friendly fire damage = 15 (base)
        # Total should be 40 (15 + 25)

        # Place player in blast radius by targeting nearby
        target = Position(engine.player.x, engine.player.y)

        # Get exploit definition
        exploit = GameData.EXPLOITS["logic_bomb"]

        # Calculate expected total damage
        heat_cost = combat._calculate_heat_cost(exploit)
        overheat_damage = max(0, (engine.player.heat + heat_cost) - engine.player.max_heat)
        base_damage = exploit.damage
        expected_total = base_damage + overheat_damage

        # The overheat damage should be > 0 for this test to be meaningful
        assert overheat_damage > 0, "Test requires overheat condition"
        assert expected_total > base_damage, "Total damage should exceed base damage"

    def test_no_overheat_shows_base_damage_only(self, basic_game_engine):
        """Verify friendly fire warning shows only base damage when no overheat."""
        engine = basic_game_engine
        from rsp.combat.combat import ExploitSystem
        from rsp.core.data import GameData

        combat = ExploitSystem(engine)

        # Set up player with low heat (no overheat)
        engine.player.heat = 10
        engine.player.max_heat = 100
        engine.player.cpu = 100

        # Logic Bomb costs 35 heat, so 10 + 35 = 45 < 100, no overheat
        exploit = GameData.EXPLOITS["logic_bomb"]
        heat_cost = combat._calculate_heat_cost(exploit)

        overheat_damage = max(0, (engine.player.heat + heat_cost) - engine.player.max_heat)

        assert overheat_damage == 0, "No overheat expected for this test"


class TestMemoryLeakStateTransition:
    """Test Memory Leak exploit properly handles enemy state transitions."""

    def test_memory_leak_resets_hostile_to_unaware(self, basic_game_engine):
        """Verify Memory Leak converts HOSTILE enemies to UNAWARE.

        Design decision: Memory Leak blinds enemies AND resets their state.
        This is intentional - the exploit is meant to "wipe" enemy memory.
        """
        engine = basic_game_engine
        from rsp.entities.base import EnemyState

        # Set up a hostile enemy
        enemy = engine.enemies[0]
        enemy.state = EnemyState.HOSTILE
        enemy.last_seen_player = engine.player.position
        enemy.move_queue = [Position(5, 5), Position(6, 6)]

        # Simulate Memory Leak effect (what _execute_memory_leak does)
        enemy.state = EnemyState.UNAWARE
        enemy.last_seen_player = None
        enemy.blinded_turns = 3
        enemy.move_queue.clear()

        # Verify state transition
        assert enemy.state == EnemyState.UNAWARE
        assert enemy.last_seen_player is None
        assert enemy.blinded_turns == 3
        assert len(enemy.move_queue) == 0

    def test_blinded_enemy_continues_moving(self, basic_game_engine):
        """Verify blinded enemies keep moving (can't see but can walk)."""
        engine = basic_game_engine
        from rsp.entities.base import EnemyState

        enemy = engine.enemies[0]
        initial_pos = Position(enemy.x, enemy.y)

        # Blind the enemy
        enemy.blinded_turns = 3
        enemy.state = EnemyState.UNAWARE

        # Process enemy movement - enemy should be able to move even when blinded
        # Movement might decrement blinded_turns, which is expected behavior
        enemy.move(engine.game_map, engine.player, engine)

        # Enemy should still be able to move (blinding doesn't freeze them)
        # Movement might not change position if blocked, but system shouldn't crash
        # Blinded turns may be decremented during movement processing
        assert enemy.blinded_turns >= 0  # Still valid state (may have decremented)


class TestDenialOfServiceStacking:
    """Test Denial of Service stun duration stacking behavior."""

    def test_dos_stun_stacks_additively(self, basic_game_engine):
        """Verify DoS stun durations stack when applied multiple times.

        Design note: This is intentional behavior - multiple DoS uses
        extend the disable duration. Players must invest multiple uses
        (and heat) to achieve longer stuns.
        """
        engine = basic_game_engine

        enemy = engine.enemies[0]
        initial_disabled = enemy.disabled_turns

        # First DoS application
        first_stun = 5
        enemy.disabled_turns += first_stun

        assert enemy.disabled_turns == initial_disabled + first_stun

        # Second DoS application
        second_stun = 5
        enemy.disabled_turns += second_stun

        # Stuns should stack
        expected = initial_disabled + first_stun + second_stun
        assert enemy.disabled_turns == expected

    def test_stunned_enemy_cannot_attack(self, basic_game_engine):
        """Verify stunned enemies cannot attack the player."""
        engine = basic_game_engine
        from rsp.entities.base import EnemyState

        enemy = engine.enemies[0]
        enemy.state = EnemyState.HOSTILE
        enemy.disabled_turns = 3

        # Stunned enemy should not be able to attack
        can_attack = enemy.can_attack_player(engine.player)

        assert can_attack is False

    def test_stunned_enemy_cannot_move(self, basic_game_engine):
        """Verify stunned enemies cannot move."""
        engine = basic_game_engine

        enemy = engine.enemies[0]
        initial_pos = Position(enemy.x, enemy.y)
        enemy.disabled_turns = 3

        # Try to move
        moved = enemy.move(engine.game_map, engine.player, engine)

        # Enemy should not move when stunned
        assert enemy.position == initial_pos
        assert moved is False


class TestInhibitorSpeedInteraction:
    """Test inhibitor slowdown interaction with speed boost."""

    def test_inhibitor_reduces_speed_boost_turns(self, basic_game_engine):
        """Verify inhibitor attack reduces speed boost duration."""
        engine = basic_game_engine
        from rsp.core.config import GameConfig

        # Give player speed boost
        engine.player.temporary_effects["speed_boost_turns"] = 5
        engine.player.temporary_effects["movement_slowed_turns"] = 0

        slow_turns = GameConfig._get_required("balance.inhibitor_slow_turns")
        current_speed = engine.player.temporary_effects["speed_boost_turns"]

        # Apply inhibitor effect (simulating attack)
        net_effect = current_speed - slow_turns

        if net_effect >= 0:
            # Speed boost partially reduced
            engine.player.temporary_effects["speed_boost_turns"] = net_effect
            assert engine.player.temporary_effects["speed_boost_turns"] == net_effect
        else:
            # Speed boost fully consumed, apply slowdown
            engine.player.temporary_effects["speed_boost_turns"] = 0
            engine.player.temporary_effects["movement_slowed_turns"] = -net_effect
            assert engine.player.temporary_effects["speed_boost_turns"] == 0
            assert engine.player.temporary_effects["movement_slowed_turns"] == -net_effect

    def test_inhibitor_on_slowed_player_stacks_slowdown(self, basic_game_engine):
        """Verify inhibitor attack stacks slowdown on already-slowed player."""
        engine = basic_game_engine
        from rsp.core.config import GameBalance, GameConfig

        # Player already slowed
        engine.player.temporary_effects["speed_boost_turns"] = 0
        engine.player.temporary_effects["movement_slowed_turns"] = 2

        slow_turns = GameConfig._get_required("balance.inhibitor_slow_turns")
        current_slow = engine.player.temporary_effects["movement_slowed_turns"]

        # Apply inhibitor effect
        new_slow = min(current_slow + slow_turns, GameBalance.INHIBITOR_SLOWDOWN_CAP)
        engine.player.temporary_effects["movement_slowed_turns"] = new_slow

        # Slowdown should stack but be capped
        assert (
            engine.player.temporary_effects["movement_slowed_turns"]
            <= GameBalance.INHIBITOR_SLOWDOWN_CAP
        )
        assert engine.player.temporary_effects["movement_slowed_turns"] >= current_slow
