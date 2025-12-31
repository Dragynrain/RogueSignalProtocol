#!/usr/bin/env python3
"""
Unit tests for game_combat.py - ExploitSystem core logic.

Tests cover:
- Heat cost calculation with exploit efficiency
- Target validation (range, bounds)
- Damage calculation with shadow bonus
- Exploit handler dispatch

Does NOT test:
- Full exploit execution (integration tests)
- Turn processing and message log (integration tests)
- Sound effects and UI (integration tests)
"""

from unittest.mock import Mock, patch

import pytest

from rsp.combat.combat import ExploitSystem
from rsp.entities.base import ExploitDefinition, Position


class TestExploitSystemInitialization:
    """Test ExploitSystem initialization."""

    def test_exploit_system_stores_game_reference(self):
        """ExploitSystem should store reference to game engine."""
        mock_game = Mock()

        exploit_system = ExploitSystem(mock_game)

        assert exploit_system.game is mock_game

    def test_exploit_system_has_exploit_handlers(self):
        """ExploitSystem should initialize exploit handler dispatch table."""
        mock_game = Mock()

        exploit_system = ExploitSystem(mock_game)

        assert isinstance(exploit_system.exploit_handlers, dict)
        assert len(exploit_system.exploit_handlers) > 0

    def test_exploit_system_registers_all_major_exploits(self):
        """ExploitSystem should have handlers for all major exploits."""
        mock_game = Mock()
        exploit_system = ExploitSystem(mock_game)

        # Check major exploits are registered
        expected_exploits = [
            "system_hop",
            "traffic_masquerade",
            "decoy_swarm",
            "code_injection",
            "buffer_overflow",
            "system_crash",
            "logic_bomb",
            "threat_scan",
            "log_wiper",
            "antivirus",
            "denial_of_service",
            "memory_leak",
            "network_scan",
        ]

        for exploit in expected_exploits:
            assert exploit in exploit_system.exploit_handlers


class TestCalculateHeatCost:
    """Test heat cost calculation with exploit efficiency."""

    def test_heat_cost_normal(self):
        """Heat cost should be base cost without exploit efficiency."""
        mock_game = Mock()
        mock_game.player.temporary_effects = {"exploit_efficiency_turns": 0}
        exploit_system = ExploitSystem(mock_game)

        exploit = ExploitDefinition(
            name="Test",
            ram=5,
            heat=20,
            range=3,
            category="test",
            damage=10,
            targeting="single",
            description="Test",
        )

        heat_cost = exploit_system._calculate_heat_cost(exploit)

        assert heat_cost == 20  # No reduction

    def test_heat_cost_with_exploit_efficiency(self):
        """Heat cost should be 60% of base with exploit efficiency active."""
        mock_game = Mock()
        mock_game.player.temporary_effects = {"exploit_efficiency_turns": 3}
        exploit_system = ExploitSystem(mock_game)

        exploit = ExploitDefinition(
            name="Test",
            ram=5,
            heat=20,
            range=3,
            category="test",
            damage=10,
            targeting="single",
            description="Test",
        )

        heat_cost = exploit_system._calculate_heat_cost(exploit)

        assert heat_cost == 12  # 20 * 0.6 = 12

    def test_heat_cost_rounds_down(self):
        """Heat cost should be rounded down (integer division)."""
        mock_game = Mock()
        mock_game.player.temporary_effects = {"exploit_efficiency_turns": 5}
        exploit_system = ExploitSystem(mock_game)

        # Heat cost 25 * 0.6 = 15.0 (rounds to 15)
        exploit = ExploitDefinition(
            name="Test",
            ram=5,
            heat=25,
            range=3,
            category="test",
            damage=10,
            targeting="single",
            description="Test",
        )

        heat_cost = exploit_system._calculate_heat_cost(exploit)

        assert heat_cost == 15  # int(25 * 0.6) = 15

    def test_heat_cost_zero_exploit(self):
        """Heat cost should be 0 for exploits with no heat cost."""
        mock_game = Mock()
        mock_game.player.temporary_effects = {"exploit_efficiency_turns": 0}
        exploit_system = ExploitSystem(mock_game)

        exploit = ExploitDefinition(
            name="Free",
            ram=5,
            heat=0,
            range=3,
            category="test",
            damage=10,
            targeting="single",
            description="Test",
        )

        heat_cost = exploit_system._calculate_heat_cost(exploit)

        assert heat_cost == 0


class TestValidateTarget:
    """Test exploit target validation."""

    def test_validate_target_within_range(self):
        """Target within range should be valid."""
        mock_game = Mock()
        mock_game.player.position = Position(10, 10)
        mock_game.message_log = Mock()
        exploit_system = ExploitSystem(mock_game)

        exploit = ExploitDefinition(
            name="Test",
            ram=5,
            heat=10,
            range=5,
            category="test",
            damage=10,
            targeting="single",
            description="Test",
        )
        target = Position(12, 12)  # Grid distance = 2

        is_valid = exploit_system._validate_target(exploit, target)

        assert is_valid is True

    def test_validate_target_out_of_range(self):
        """Target outside exploit range should be invalid."""
        mock_game = Mock()
        mock_game.player.position = Position(10, 10)
        mock_game.message_log = Mock()
        exploit_system = ExploitSystem(mock_game)

        exploit = ExploitDefinition(
            name="Test",
            ram=5,
            heat=10,
            range=2,
            category="test",
            damage=10,
            targeting="single",
            description="Test",
        )
        target = Position(15, 15)  # Grid distance = 5 (too far)

        is_valid = exploit_system._validate_target(exploit, target)

        assert is_valid is False

    def test_validate_target_at_exact_range(self):
        """Target at exact maximum range should be valid."""
        mock_game = Mock()
        mock_game.player.position = Position(10, 10)
        mock_game.message_log = Mock()
        exploit_system = ExploitSystem(mock_game)

        exploit = ExploitDefinition(
            name="Test",
            ram=5,
            heat=10,
            range=3,
            category="test",
            damage=10,
            targeting="single",
            description="Test",
        )
        target = Position(13, 13)  # Grid distance = 3 (exact)

        is_valid = exploit_system._validate_target(exploit, target)

        assert is_valid is True

    def test_validate_target_uses_grid_distance(self):
        """Target validation should use grid distance (diagonals = 1)."""
        mock_game = Mock()
        mock_game.player.position = Position(10, 10)
        mock_game.message_log = Mock()
        exploit_system = ExploitSystem(mock_game)

        exploit = ExploitDefinition(
            name="Test",
            ram=5,
            heat=10,
            range=1,
            category="test",
            damage=10,
            targeting="single",
            description="Test",
        )

        # All 8 adjacent tiles should be valid (diagonal = 1 grid distance)
        adjacent_targets = [
            Position(9, 9),  # Top-left diagonal
            Position(10, 9),  # Top
            Position(11, 9),  # Top-right diagonal
            Position(9, 10),  # Left
            Position(11, 10),  # Right
            Position(9, 11),  # Bottom-left diagonal
            Position(10, 11),  # Bottom
            Position(11, 11),  # Bottom-right diagonal
        ]

        for target in adjacent_targets:
            is_valid = exploit_system._validate_target(exploit, target)
            assert is_valid is True, f"Target {target} should be valid (diagonal = 1)"

    def test_validate_target_out_of_map_bounds(self):
        """Target outside map bounds should be invalid."""
        mock_game = Mock()
        mock_game.player.position = Position(10, 10)
        mock_game.message_log = Mock()
        exploit_system = ExploitSystem(mock_game)

        exploit = ExploitDefinition(
            name="Test",
            ram=5,
            heat=10,
            range=100,  # Large range
            category="test",
            damage=10,
            targeting="single",
            description="Test",
        )

        # Target outside map bounds (negative coordinates)
        target = Position(-1, -1)

        is_valid = exploit_system._validate_target(exploit, target)

        assert is_valid is False


class TestCalculateExploitDamage:
    """Test exploit damage calculation with shadow bonus."""

    def test_calculate_damage_normal(self):
        """Damage should be base damage without shadow bonus."""
        mock_game = Mock()
        mock_game.game_map = Mock()
        mock_game.game_map.is_blind_spot.return_value = False
        mock_game.player = Mock()
        mock_game.player.position = Position(10, 10)
        mock_game.player.is_invisible.return_value = False
        exploit_system = ExploitSystem(mock_game)

        base_damage = 20
        damage = exploit_system._calculate_exploit_damage(base_damage)

        assert damage == 20  # No bonus

    def test_calculate_damage_with_shadow_bonus(self):
        """Damage should be +10 when in blind spot."""
        mock_game = Mock()
        mock_game.game_map = Mock()
        mock_game.game_map.is_blind_spot.return_value = True  # In shadow
        mock_game.player = Mock()
        mock_game.player.position = Position(10, 10)
        mock_game.player.is_invisible.return_value = False
        exploit_system = ExploitSystem(mock_game)

        base_damage = 20
        damage = exploit_system._calculate_exploit_damage(base_damage)

        assert damage == 30  # +10 shadow bonus

    def test_calculate_damage_with_invisibility_bonus(self):
        """Damage should be +10 when invisible."""
        mock_game = Mock()
        mock_game.game_map = Mock()
        mock_game.game_map.is_blind_spot.return_value = False
        mock_game.player = Mock()
        mock_game.player.position = Position(10, 10)
        mock_game.player.is_invisible.return_value = True  # Invisible
        exploit_system = ExploitSystem(mock_game)

        base_damage = 20
        damage = exploit_system._calculate_exploit_damage(base_damage)

        assert damage == 30  # +10 invisibility bonus

    def test_calculate_damage_shadow_and_invisibility_dont_stack(self):
        """Shadow and invisibility bonuses should not stack."""
        mock_game = Mock()
        mock_game.game_map = Mock()
        mock_game.game_map.is_blind_spot.return_value = True
        mock_game.player = Mock()
        mock_game.player.position = Position(10, 10)
        mock_game.player.is_invisible.return_value = True
        exploit_system = ExploitSystem(mock_game)

        base_damage = 20
        damage = exploit_system._calculate_exploit_damage(base_damage)

        assert damage == 30  # Only +10, not +20

    def test_calculate_damage_zero_damage_exploit(self):
        """Zero-damage exploits should not get shadow bonus."""
        mock_game = Mock()
        mock_game.game_map = Mock()
        mock_game.game_map.is_blind_spot.return_value = True
        mock_game.player = Mock()
        mock_game.player.position = Position(10, 10)
        mock_game.player.is_invisible.return_value = True
        exploit_system = ExploitSystem(mock_game)

        base_damage = 0
        damage = exploit_system._calculate_exploit_damage(base_damage)

        assert damage == 0  # No bonus for 0 damage


class TestExploitHandlerDispatch:
    """Test exploit handler dispatch system."""

    def test_execute_specific_exploit_dispatches_correctly(self):
        """_execute_specific_exploit should dispatch to correct handler."""
        mock_game = Mock()
        exploit_system = ExploitSystem(mock_game)

        # Mock a handler
        mock_handler = Mock(return_value=True)
        exploit_system.exploit_handlers["test_exploit"] = mock_handler

        exploit = ExploitDefinition(
            name="Test",
            ram=5,
            heat=10,
            range=3,
            category="test",
            damage=10,
            targeting="single",
            description="Test",
        )
        target = Position(10, 10)

        result = exploit_system._execute_specific_exploit("test_exploit", exploit, target)

        assert result is True
        mock_handler.assert_called_once_with(exploit, target)

    def test_execute_specific_exploit_unknown_exploit(self):
        """_execute_specific_exploit should return False for unknown exploits."""
        mock_game = Mock()
        exploit_system = ExploitSystem(mock_game)

        exploit = ExploitDefinition(
            name="Unknown",
            ram=5,
            heat=10,
            range=3,
            category="test",
            damage=10,
            targeting="single",
            description="Test",
        )
        target = Position(10, 10)

        result = exploit_system._execute_specific_exploit("nonexistent_exploit", exploit, target)

        assert result is False


class TestSpecificExploitMethods:
    """Test individual exploit execution methods."""

    def test_execute_traffic_masquerade(self):
        """Traffic Masquerade should set invisibility effect."""
        mock_game = Mock()
        mock_game.player.temporary_effects = {"traffic_masquerade_turns": 0}
        mock_game.message_log = Mock()
        mock_game.sound_manager = Mock()
        exploit_system = ExploitSystem(mock_game)

        # Mock the exploit data

        mock_exploit = Mock()
        mock_exploit.effect_duration = 5

        with patch("rsp.combat.combat.GameData.EXPLOITS", {"traffic_masquerade": mock_exploit}):
            result = exploit_system._execute_traffic_masquerade()

        assert result is True
        assert mock_game.player.temporary_effects["traffic_masquerade_turns"] == 5

    def test_execute_system_hop_to_valid_blind_spot(self):
        """System Hop should move player to blind spot."""
        mock_game = Mock()
        mock_game.player.position = Position(10, 10)
        mock_game.game_map = Mock()
        mock_game.game_map.is_blind_spot.return_value = True
        mock_game.game_map.is_valid_position.return_value = True
        mock_game._get_enemy_at.return_value = None
        mock_game.message_log = Mock()
        mock_game.sound_manager = Mock()
        exploit_system = ExploitSystem(mock_game)

        target = Position(15, 15)
        result = exploit_system._execute_system_hop(target)

        assert result is True
        assert mock_game.player.position.x == 15
        assert mock_game.player.position.y == 15

    def test_execute_system_hop_to_non_blind_spot_fails(self):
        """System Hop should fail if target is not a blind spot."""
        mock_game = Mock()
        mock_game.player.position = Position(10, 10)
        mock_game.game_map = Mock()
        mock_game.game_map.is_blind_spot.return_value = False  # Not a blind spot
        mock_game.game_map.is_valid_position.return_value = True
        mock_game.message_log = Mock()
        exploit_system = ExploitSystem(mock_game)

        target = Position(15, 15)
        result = exploit_system._execute_system_hop(target)

        assert result is False
        # Player position should not change
        assert mock_game.player.position.x == 10
        assert mock_game.player.position.y == 10

    def test_execute_system_hop_to_occupied_position_fails(self):
        """System Hop should fail if enemy is at target position."""
        mock_game = Mock()
        mock_game.player.position = Position(10, 10)
        mock_game.game_map = Mock()
        mock_game.game_map.is_blind_spot.return_value = True
        mock_game.game_map.is_valid_position.return_value = True
        mock_game._get_enemy_at.return_value = Mock()  # Enemy present
        mock_game.message_log = Mock()
        exploit_system = ExploitSystem(mock_game)

        target = Position(15, 15)
        result = exploit_system._execute_system_hop(target)

        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
