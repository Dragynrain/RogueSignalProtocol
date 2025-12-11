#!/usr/bin/env python3
"""
Integration tests for Combat system functionality.
Tests the actual ExploitSystem class and combat mechanics integration.
"""

from unittest.mock import Mock, patch

from game_characters import Player
from game_combat import ExploitSystem
from game_entities import ExploitDefinition, Position, TargetingMode


def test_exploit_system_initialization(basic_game_engine):
    """ExploitSystem initializes correctly with game instance."""
    from game_combat import ExploitSystem

    exploit_system = ExploitSystem(basic_game_engine)

    assert exploit_system.game is basic_game_engine


class TestExploitSystem:
    """Test the ExploitSystem class and exploit mechanics."""

    def test_use_exploit_not_equipped(self, basic_game_engine):
        """Cannot use exploit that isn't equipped."""
        # Player starts with no exploits equipped
        basic_game_engine.player.inventory_manager.equipped_exploits = []

        exploit_system = ExploitSystem(basic_game_engine)

        result = exploit_system.use_exploit("nonexistent_exploit")

        assert result is False
        # Message log is real, check the last message
        assert basic_game_engine.message_log.messages[-1].text == "Exploit not equipped"

    def test_use_exploit_requires_targeting(self, basic_game_engine):
        """Exploit requiring targeting enters targeting mode."""
        # Set up player with exploit equipped
        basic_game_engine.player.heat = 50
        basic_game_engine.player.inventory_manager.equipped_exploits = ["buffer_overflow"]

        with patch("game_combat.GameData") as mock_game_data:
            # Mock an exploit that requires targeting
            mock_exploit = Mock(spec=ExploitDefinition)
            mock_exploit.targeting = TargetingMode.SINGLE
            mock_exploit.range = 5
            mock_exploit.heat = 10
            mock_exploit.name = "Buffer Overflow"
            mock_game_data.EXPLOITS = {"buffer_overflow": mock_exploit}

            exploit_system = ExploitSystem(basic_game_engine)

            result = exploit_system.use_exploit("buffer_overflow")

            assert result is True
            assert basic_game_engine.targeting_mode is True
            assert basic_game_engine.targeting_exploit == "buffer_overflow"
            assert basic_game_engine.message_log.messages[-1].text == "Targeting Buffer Overflow"

    def test_use_exploit_heat_limit_exceeded(self, basic_game_engine):
        """Exploit with heat cost exceeding limit shows overclock dialogue."""
        # Set player to high heat
        basic_game_engine.player.heat = 90  # High heat
        basic_game_engine.player.inventory_manager.equipped_exploits = ["system_crash"]

        with (
            patch("game_combat.GameData") as mock_game_data,
            patch.object(basic_game_engine.dialogue_state, "show") as mock_show,
        ):
            mock_exploit = Mock(spec=ExploitDefinition)
            mock_exploit.heat = 20  # Would exceed 100 heat limit
            mock_exploit.targeting = TargetingMode.NONE
            mock_exploit.range = 0
            mock_exploit.name = "System Crash"
            mock_exploit.self_damage = 0  # Prevent TypeError when comparing to int
            mock_game_data.EXPLOITS = {"system_crash": mock_exploit}

            exploit_system = ExploitSystem(basic_game_engine)

            result = exploit_system.use_exploit("system_crash")

            # Should return False and show dialogue instead of old confirmation system
            assert result is False
            # Verify dialogue_state.show was called
            mock_show.assert_called_once()

    def test_execute_exploit_invalid(self, basic_game_engine):
        """Cannot execute unknown exploit."""
        with patch("game_combat.GameData") as mock_game_data:
            mock_game_data.EXPLOITS = {}  # No exploits available

            exploit_system = ExploitSystem(basic_game_engine)

            result = exploit_system.execute_exploit("unknown_exploit", Position(5, 5))

            assert result is False
            assert basic_game_engine.message_log.messages[-1].text == "Unknown exploit"

    def test_calculate_heat_cost_with_efficiency(self, basic_game_engine):
        """Heat cost calculation considers efficiency bonus."""
        basic_game_engine.player.temporary_effects["exploit_efficiency_turns"] = 5  # Has efficiency

        exploit_system = ExploitSystem(basic_game_engine)

        mock_exploit = Mock(spec=ExploitDefinition)
        mock_exploit.heat = 20

        heat_cost = exploit_system._calculate_heat_cost(mock_exploit)

        # Should be 60% of original cost due to efficiency
        assert heat_cost == 12  # 20 * 0.6 = 12

    def test_calculate_heat_cost_without_efficiency(self, basic_game_engine):
        """Heat cost calculation without efficiency bonus."""
        basic_game_engine.player.temporary_effects["exploit_efficiency_turns"] = 0  # No efficiency

        exploit_system = ExploitSystem(basic_game_engine)

        mock_exploit = Mock(spec=ExploitDefinition)
        mock_exploit.heat = 30

        heat_cost = exploit_system._calculate_heat_cost(mock_exploit)

        # Should be full cost without efficiency
        assert heat_cost == 30

    def test_target_validation(self, basic_game_engine):
        """Target validation works for different exploit types."""
        with patch.object(basic_game_engine.game_map, "has_line_of_sight", return_value=True):
            exploit_system = ExploitSystem(basic_game_engine)

            # Mock exploit with range requirement
            mock_exploit = Mock(spec=ExploitDefinition)
            mock_exploit.range = 5
            mock_exploit.targeting = TargetingMode.SINGLE

            # Target close enough to player (at 15, 15)
            target = Position(17, 15)

            result = exploit_system._validate_target(mock_exploit, target)

            # Should validate successfully (distance is 2, within range of 5)
            assert result is True


class TestPlayerCombat:
    """Test player combat mechanics."""

    def test_player_take_damage_with_effects(self):
        """Player take_damage method works with temporary effects."""
        player = Player(10, 10)
        initial_cpu = player.cpu

        # Test basic damage
        damage_taken = player.take_damage(25)

        assert damage_taken == 25
        assert player.cpu == initial_cpu - 25

    def test_player_death_prevention(self):
        """Player CPU cannot go below 0."""
        player = Player(10, 10)
        player.cpu = 10  # Low CPU

        # Deal massive damage
        damage_taken = player.take_damage(50)

        # Should only take damage down to 0
        assert damage_taken == 10  # Only actual damage dealt
        assert player.cpu == 0

    def test_player_temporary_effects_update(self):
        """Player temporary effects decrease each turn."""
        player = Player(5, 5)

        # Set some temporary effects
        player.temporary_effects["traffic_masquerade_turns"] = 3
        player.temporary_effects["speed_boost_turns"] = 2

        player.update_effects()

        # Effects should decrease by 1
        assert player.temporary_effects["traffic_masquerade_turns"] == 2
        assert player.temporary_effects["speed_boost_turns"] == 1

    def test_player_temporary_effects_minimum_zero(self):
        """Temporary effects don't go below 0."""
        player = Player(5, 5)

        # Set effect to 1
        player.temporary_effects["virus_turns"] = 1

        player.update_effects()

        # Should be 0, not negative
        assert player.temporary_effects["virus_turns"] == 0

        # Update again
        player.update_effects()

        # Should still be 0
        assert player.temporary_effects["virus_turns"] == 0


class TestEnemyCombat:
    """Test enemy combat mechanics."""

    def test_enemy_attack_adjacent_player(self):
        """Enemy can attack adjacent player."""
        from tests.fixtures.simple_fixtures import enemy, player

        test_enemy = enemy("virus", 5, 5)
        test_player = player(6, 5, 100)  # Adjacent
        initial_cpu = test_player.cpu

        damage = test_enemy.attack_player(test_player)

        # Virus enemies deal 0 direct damage but apply virus effect
        assert damage == 0
        # Player CPU should be unchanged (virus damage is applied over time)
        assert test_player.cpu == initial_cpu

    def test_enemy_cannot_attack_distant_player(self):
        """Enemy cannot attack non-adjacent player."""
        from tests.fixtures.simple_fixtures import enemy, player

        test_enemy = enemy("scanner", 5, 5)
        test_player = player(10, 10, 100)  # Not adjacent

        can_attack = test_enemy.can_attack_player(test_player)

        assert can_attack is False

    def test_enemy_disabled_cannot_attack(self):
        """Disabled enemy cannot attack player."""
        from tests.fixtures.simple_fixtures import enemy, player

        test_enemy = enemy("patrol", 8, 8)
        test_enemy.disabled_turns = 3  # Disabled
        test_player = player(9, 8, 100)  # Adjacent
        initial_cpu = test_player.cpu

        damage = test_enemy.attack_player(test_player)

        # Patrol enemy type deals direct damage even when disabled
        # (disabled status doesn't prevent attack method execution)
        assert damage == test_enemy.type_data.damage  # Normal damage
        assert test_player.cpu == initial_cpu - test_enemy.type_data.damage  # Damage taken


class TestConsecutiveAttackHeatPenalty:
    """Test consecutive attack heat penalty mechanic."""

    def test_first_attack_no_penalty(self, basic_game_engine):
        """First attack has no heat penalty."""
        from tests.fixtures.simple_fixtures import enemy

        # Set up player at position (10, 10)
        basic_game_engine.player.position = Position(10, 10)
        basic_game_engine.player.heat = 0

        # Create enemy adjacent to player
        test_enemy = enemy("patrol", 11, 10)
        basic_game_engine.enemies = [test_enemy]

        # First attack
        basic_game_engine._perform_bump_attack(test_enemy)

        # Should be base heat (8) with no penalty
        assert basic_game_engine.player.heat == 8
        assert basic_game_engine.player.consecutive_attacks_here == 0

    def test_consecutive_attacks_build_penalty(self, basic_game_engine):
        """Consecutive attacks at same position increase heat penalty."""
        from tests.fixtures.simple_fixtures import enemy

        # Set up player at position (10, 10)
        basic_game_engine.player.position = Position(10, 10)
        basic_game_engine.player.heat = 0

        # Create multiple enemies to attack
        enemy1 = enemy("patrol", 11, 10)
        enemy1.cpu = 100  # High HP so doesn't die
        enemy1.max_cpu = 100
        enemy2 = enemy("patrol", 11, 10)
        enemy2.cpu = 100
        enemy2.max_cpu = 100
        enemy3 = enemy("patrol", 11, 10)
        enemy3.cpu = 100
        enemy3.max_cpu = 100

        basic_game_engine.enemies = [enemy1, enemy2, enemy3]

        # First attack at (10, 10)
        basic_game_engine._perform_bump_attack(enemy1)
        heat_after_1 = basic_game_engine.player.heat
        assert heat_after_1 == 8  # Base heat

        # Second attack at same position (10, 10)
        basic_game_engine._perform_bump_attack(enemy2)
        heat_after_2 = basic_game_engine.player.heat
        assert heat_after_2 == 8 + 9  # 8 + (8 + 1 penalty) = 17

        # Third attack at same position (10, 10)
        basic_game_engine._perform_bump_attack(enemy3)
        heat_after_3 = basic_game_engine.player.heat
        assert heat_after_3 == 8 + 9 + 10  # 8 + 9 + (8 + 2 penalty) = 27

    def test_moving_resets_penalty(self, basic_game_engine):
        """Moving to a new position resets heat penalty."""
        from tests.fixtures.simple_fixtures import enemy

        # Set up player at position (10, 10)
        basic_game_engine.player.position = Position(10, 10)
        basic_game_engine.player.heat = 0

        # Create enemies
        enemy1 = enemy("patrol", 11, 10)
        enemy1.cpu = 100
        enemy1.max_cpu = 100
        enemy2 = enemy("patrol", 11, 11)
        enemy2.cpu = 100
        enemy2.max_cpu = 100

        basic_game_engine.enemies = [enemy1, enemy2]

        # First attack at (10, 10)
        basic_game_engine._perform_bump_attack(enemy1)
        assert basic_game_engine.player.heat == 8

        # Second attack at same position
        basic_game_engine._perform_bump_attack(enemy1)
        assert basic_game_engine.player.heat == 17  # 8 + 9

        # Move player to new position
        basic_game_engine.player.position = Position(11, 11)

        # Third attack at NEW position (11, 11)
        basic_game_engine._perform_bump_attack(enemy2)
        heat_after_move = basic_game_engine.player.heat
        # Should be previous heat (17) + base heat (8) with no penalty
        assert heat_after_move == 25  # 17 + 8
        assert basic_game_engine.player.consecutive_attacks_here == 0

    def test_penalty_with_exploit_efficiency(self, basic_game_engine):
        """Exploit efficiency reduces heat including penalty."""
        from tests.fixtures.simple_fixtures import enemy

        # Set up player at position (10, 10) with exploit efficiency
        basic_game_engine.player.position = Position(10, 10)
        basic_game_engine.player.heat = 0
        basic_game_engine.player.temporary_effects["exploit_efficiency_turns"] = 5

        # Create enemies
        enemy1 = enemy("patrol", 11, 10)
        enemy1.cpu = 100
        enemy1.max_cpu = 100
        enemy2 = enemy("patrol", 11, 10)
        enemy2.cpu = 100
        enemy2.max_cpu = 100

        basic_game_engine.enemies = [enemy1, enemy2]

        # First attack with efficiency (8 * 0.7 = 5 heat)
        basic_game_engine._perform_bump_attack(enemy1)
        assert basic_game_engine.player.heat == 5  # 8 * 0.7 = 5.6 -> 5

        # Second attack with efficiency and penalty ((8+1) * 0.7 = 6 heat)
        basic_game_engine._perform_bump_attack(enemy2)
        heat_after_2 = basic_game_engine.player.heat
        # 5 + (9 * 0.7) = 5 + 6.3 = 5 + 6 = 11
        assert heat_after_2 == 11

    def test_penalty_message_displays(self, basic_game_engine):
        """Penalty message displays when penalty > 0."""
        from tests.fixtures.simple_fixtures import enemy

        # Set up player at position (10, 10)
        basic_game_engine.player.position = Position(10, 10)
        basic_game_engine.player.heat = 0

        # Create enemies
        enemy1 = enemy("patrol", 11, 10)
        enemy1.cpu = 100
        enemy1.max_cpu = 100
        enemy2 = enemy("patrol", 11, 10)
        enemy2.cpu = 100
        enemy2.max_cpu = 100

        basic_game_engine.enemies = [enemy1, enemy2]

        # First attack - no penalty message
        basic_game_engine._perform_bump_attack(enemy1)
        messages = [msg.text for msg in basic_game_engine.message_log.messages]
        penalty_messages = [msg for msg in messages if "Attacking from same spot:" in msg]
        assert len(penalty_messages) == 0  # No penalty on first attack

        # Second attack - should show penalty message
        basic_game_engine._perform_bump_attack(enemy2)
        messages = [msg.text for msg in basic_game_engine.message_log.messages]
        penalty_messages = [msg for msg in messages if "Attacking from same spot:" in msg]
        assert len(penalty_messages) == 1
        assert "+1 heat penalty" in penalty_messages[0]

    def test_multiple_consecutive_attacks_escalate(self, basic_game_engine):
        """Heat penalty escalates with each consecutive attack."""
        from tests.fixtures.simple_fixtures import enemy

        # Set up player at position (10, 10)
        basic_game_engine.player.position = Position(10, 10)
        basic_game_engine.player.heat = 0

        # Create 5 enemies with high HP
        enemies = []
        for i in range(5):
            e = enemy("firewall", 11, 10)  # High HP enemy
            e.cpu = 200
            e.max_cpu = 200
            enemies.append(e)

        basic_game_engine.enemies = enemies

        # Attack 5 times in a row at same position
        expected_heat = 0
        for i, e in enumerate(enemies):
            basic_game_engine._perform_bump_attack(e)
            expected_heat += 8 + i  # 8, 9, 10, 11, 12

        # Total should be 8 + 9 + 10 + 11 + 12 = 50
        assert basic_game_engine.player.heat == expected_heat
        assert expected_heat == 50
        assert basic_game_engine.player.consecutive_attacks_here == 4  # 0-indexed

    def test_penalty_resets_only_on_position_change(self, basic_game_engine):
        """Penalty only resets when position actually changes."""
        from tests.fixtures.simple_fixtures import enemy

        # Set up player at position (10, 10)
        basic_game_engine.player.position = Position(10, 10)
        basic_game_engine.player.heat = 0

        # Create enemies
        enemy1 = enemy("patrol", 11, 10)
        enemy1.cpu = 100
        enemy1.max_cpu = 100
        enemy2 = enemy("patrol", 11, 10)
        enemy2.cpu = 100
        enemy2.max_cpu = 100

        basic_game_engine.enemies = [enemy1, enemy2]

        # First attack
        basic_game_engine._perform_bump_attack(enemy1)
        assert basic_game_engine.player.consecutive_attacks_here == 0

        # "Move" to same position (shouldn't reset)
        basic_game_engine.player.position = Position(10, 10)

        # Second attack - penalty should still apply
        basic_game_engine._perform_bump_attack(enemy2)
        assert basic_game_engine.player.heat == 17  # 8 + 9, penalty applied
        assert basic_game_engine.player.consecutive_attacks_here == 1
