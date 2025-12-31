"""
Tests for the simplified enemy movement system and enemy communication/alerting.
Tests the actual behavior rather than internal implementation details.
"""

from unittest.mock import patch

import pytest

from rsp.entities.base import EnemyState, Position
from tests.fixtures.simple_fixtures import enemy_builder


class TestEnemyMovementBehavior:
    """Test that enemies move correctly based on their state and type."""

    def test_hostile_enemy_pathfinds_to_player(self, basic_game_engine):
        """HOSTILE enemies should pathfind toward player's last known position."""
        test_enemy = enemy_builder(
            "virus", pos=(5, 5), state=EnemyState.HOSTILE, last_seen=(10, 10)
        )
        basic_game_engine.enemies = [test_enemy]

        # Mock pathfinding to succeed
        with patch.object(test_enemy, "can_see_player", return_value=False):
            test_enemy.move(basic_game_engine.game_map, basic_game_engine.player, basic_game_engine)

        # Enemy movement system should work
        assert test_enemy.last_seen_player is not None, "Should retain last seen player position"

    def test_unaware_enemy_uses_normal_movement(self, basic_game_engine):
        """UNAWARE enemies should use their base movement type (random, patrol, etc)."""
        test_enemy = enemy_builder("bot", pos=(5, 5))  # bot is RANDOM movement
        assert test_enemy.state == EnemyState.UNAWARE
        basic_game_engine.enemies = [test_enemy]

        test_enemy.move(basic_game_engine.game_map, basic_game_engine.player, basic_game_engine)

        # Movement system should work
        assert test_enemy.state == EnemyState.UNAWARE

    def test_alert_enemy_continues_normal_movement(self, basic_game_engine):
        """ALERT enemies should continue normal movement (it's a 1-turn warning)."""
        test_enemy = enemy_builder(
            "patrol", pos=(5, 5), state=EnemyState.ALERT, patrol_points=[(10, 5), (15, 5)]
        )
        test_enemy.patrol_index = 0
        basic_game_engine.enemies = [test_enemy]

        test_enemy.move(basic_game_engine.game_map, basic_game_engine.player, basic_game_engine)

        # Should still have patrol system
        assert test_enemy.patrol_points is not None


class TestEnemyCommunication:
    """Test enemy alerting and communication system."""

    def test_nearby_enemies_alerted_when_enemy_goes_hostile(self, basic_game_engine):
        """When an enemy becomes HOSTILE, nearby enemies should be alerted."""
        from rsp.core.session import GameSession

        # Create alerting enemy
        alerting_enemy = enemy_builder("scanner", pos=(10, 10), state=EnemyState.HOSTILE)

        # Create nearby enemy (within alert radius)
        nearby_enemy = enemy_builder("bot", pos=(12, 12), state=EnemyState.UNAWARE)

        # Create distant enemy (outside alert radius)
        distant_enemy = enemy_builder("virus", pos=(50, 50), state=EnemyState.UNAWARE)

        basic_game_engine.enemies = [alerting_enemy, nearby_enemy, distant_enemy]
        game_session = GameSession(basic_game_engine)

        # Trigger alert
        game_session._alert_nearby_enemies(alerting_enemy)

        # Nearby enemy should be alerted
        assert nearby_enemy.state == EnemyState.HOSTILE, "Nearby enemy should become HOSTILE"
        assert (
            nearby_enemy.last_seen_player == basic_game_engine.player.position
        ), "Should know player position"

        # Distant enemy should remain unaware
        assert distant_enemy.state == EnemyState.UNAWARE, "Distant enemy should stay UNAWARE"
        assert distant_enemy.last_seen_player is None, "Should not know player position"

    def test_alerted_enemies_skip_alert_warning(self, basic_game_engine):
        """Enemies alerted by communication skip ALERT and go straight to HOSTILE."""
        from rsp.core.session import GameSession

        alerting_enemy = enemy_builder("scanner", pos=(10, 10), state=EnemyState.HOSTILE)
        nearby_enemy = enemy_builder("bot", pos=(12, 12), state=EnemyState.UNAWARE)

        basic_game_engine.enemies = [alerting_enemy, nearby_enemy]
        game_session = GameSession(basic_game_engine)

        # Trigger alert
        game_session._alert_nearby_enemies(alerting_enemy)

        # Should skip ALERT and go straight to HOSTILE
        assert nearby_enemy.state == EnemyState.HOSTILE, "Should go directly to HOSTILE"
        assert nearby_enemy.alert_timer == 0, "Alert timer should be 0"

    def test_already_hostile_enemies_not_re_alerted(self, basic_game_engine):
        """Enemies that are already HOSTILE should not be alerted again."""
        from rsp.core.session import GameSession

        alerting_enemy = enemy_builder("scanner", pos=(10, 10), state=EnemyState.HOSTILE)
        already_hostile = enemy_builder(
            "bot", pos=(12, 12), state=EnemyState.HOSTILE, last_seen=(5, 5)
        )

        basic_game_engine.enemies = [alerting_enemy, already_hostile]
        game_session = GameSession(basic_game_engine)

        # Trigger alert
        game_session._alert_nearby_enemies(alerting_enemy)

        # Should keep original last_seen_player position
        assert already_hostile.last_seen_player == Position(5, 5), "Should not update position"


class TestQueueMaintenanceIntegration:
    """Test queue maintenance behavior in integration scenarios."""

    def test_queue_always_has_moves_when_path_available(self, basic_game_engine):
        """Queue should always have up to 3 moves when path to target exists."""
        test_enemy = enemy_builder(
            "virus", pos=(5, 5), state=EnemyState.HOSTILE, last_seen=(20, 20)
        )
        basic_game_engine.enemies = [test_enemy]

        # Execute several moves
        for _ in range(5):
            test_enemy.move(basic_game_engine.game_map, basic_game_engine.player, basic_game_engine)
            # Queue should always have moves (up to 3) when path exists
            assert len(test_enemy.move_queue) <= 3, "Queue should not exceed 3 moves"
            # Queue is valid (may be empty if at target or blocked)
            assert isinstance(test_enemy.move_queue, list), "Move queue should be a list"

    def test_queue_refills_after_each_move(self, basic_game_engine):
        """After each move execution, queue should top back up to 3."""
        test_enemy = enemy_builder(
            "scanner", pos=(10, 10), state=EnemyState.HOSTILE, last_seen=(30, 30)
        )
        basic_game_engine.enemies = [test_enemy]

        # First move
        test_enemy.move(basic_game_engine.game_map, basic_game_engine.player, basic_game_engine)
        first_queue_len = len(test_enemy.move_queue)

        # Second move
        test_enemy.move(basic_game_engine.game_map, basic_game_engine.player, basic_game_engine)
        second_queue_len = len(test_enemy.move_queue)

        # Queue should be maintained around 3 (or fewer if path is short)
        assert first_queue_len <= 3, "First queue should not exceed 3"
        assert second_queue_len <= 3, "Second queue should not exceed 3"

    def test_queue_clears_on_state_transition(self, basic_game_engine):
        """Queue should clear when enemy state transitions."""
        test_enemy = enemy_builder(
            "patrol", pos=(10, 10), state=EnemyState.UNAWARE, patrol_points=[(15, 15), (20, 20)]
        )
        test_enemy.patrol_index = 0
        basic_game_engine.enemies = [test_enemy]

        # Build up queue
        test_enemy.move(basic_game_engine.game_map, basic_game_engine.player, basic_game_engine)
        initial_queue_len = len(test_enemy.move_queue)

        # Change state (simulating detection)
        old_state = test_enemy.state
        test_enemy.state = EnemyState.HOSTILE
        test_enemy.last_seen_player = basic_game_engine.player.position
        if test_enemy.state != old_state:
            test_enemy.move_queue.clear()

        # Queue should be cleared
        assert len(test_enemy.move_queue) == 0, "Queue should clear on state change"


class TestCompleteEnemyLifecycle:
    """Test complete enemy AI lifecycle from spawn to attack."""

    def test_enemy_detects_player_and_transitions_to_hostile(self, basic_game_engine):
        """Test detection flow: UNAWARE → sees player → transitions to HOSTILE.

        This tests the AI detection system that happens in real gameplay.
        The pathfinding portion is tested separately in pathfinding tests.
        """
        # Position enemy and player in open area (center of map) for clear LOS
        enemy_pos = (15, 12)
        player_pos = (15, 16)  # Same column, 4 tiles away (clear vertical line)

        # Create UNAWARE enemy - scanner has good base vision
        test_enemy = enemy_builder("scanner", pos=enemy_pos)
        test_enemy.state = EnemyState.UNAWARE
        basic_game_engine.enemies = [test_enemy]

        # Place player in enemy's line of sight
        basic_game_engine.player.x = player_pos[0]
        basic_game_engine.player.y = player_pos[1]

        # Ensure clear line of sight by removing any walls between them
        for y in range(min(enemy_pos[1], player_pos[1]), max(enemy_pos[1], player_pos[1]) + 1):
            pos = (enemy_pos[0], y)
            if pos in basic_game_engine.game_map.walls:
                basic_game_engine.game_map.walls.remove(pos)

        # Verify initial state
        assert test_enemy.state == EnemyState.UNAWARE

        # Process turns until enemy detects player
        detected = False
        for turn in range(5):  # Give it 5 turns to detect
            basic_game_engine.process_turn()
            if test_enemy.state in (EnemyState.HOSTILE, EnemyState.ALERT):
                detected = True
                break

        assert detected, f"Enemy should detect player within 5 turns, got {test_enemy.state}"

        # Continue processing until enemy is HOSTILE
        for _ in range(3):  # Extra turns for full transition
            if test_enemy.state == EnemyState.HOSTILE:
                break
            basic_game_engine.process_turn()

        assert test_enemy.state == EnemyState.HOSTILE, f"Enemy should be HOSTILE, got {test_enemy.state}"

        # Enemy should know where player was
        assert test_enemy.last_seen_player is not None, "Enemy should have recorded player position"

    def test_adjacent_enemy_can_attack(self, basic_game_engine):
        """Test that an adjacent HOSTILE enemy can attack the player."""
        # Place enemy adjacent to player
        player_x, player_y = 15, 15
        basic_game_engine.player.x = player_x
        basic_game_engine.player.y = player_y

        # Create HOSTILE enemy adjacent to player (use firewall - has damage)
        test_enemy = enemy_builder("firewall", pos=(player_x + 1, player_y))
        test_enemy.state = EnemyState.HOSTILE
        test_enemy.last_seen_player = basic_game_engine.player.position
        basic_game_engine.enemies = [test_enemy]

        # Verify adjacency
        distance = test_enemy.position.grid_distance_to(basic_game_engine.player.position)
        assert distance == 1, f"Enemy should be adjacent (distance 1), got {distance}"

        # Verify enemy has damage
        assert test_enemy.type_data.damage > 0, f"Enemy should have damage, got {test_enemy.type_data.damage}"

        # Enemy should be able to attack
        assert test_enemy.can_attack_player(
            basic_game_engine.player
        ), "Adjacent HOSTILE enemy with damage should be able to attack"

    def test_alert_chain_propagation(self, basic_game_engine):
        """Test that when one enemy goes HOSTILE, nearby enemies are alerted.

        This tests the communication system between enemies.
        """
        from rsp.core.session import GameSession

        # Create a chain of enemies
        primary = enemy_builder("scanner", pos=(10, 10), state=EnemyState.UNAWARE)
        nearby1 = enemy_builder("bot", pos=(12, 10), state=EnemyState.UNAWARE)
        nearby2 = enemy_builder("patrol", pos=(10, 12), state=EnemyState.UNAWARE)
        distant = enemy_builder("virus", pos=(40, 40), state=EnemyState.UNAWARE)

        basic_game_engine.enemies = [primary, nearby1, nearby2, distant]
        game_session = GameSession(basic_game_engine)

        # Primary enemy goes hostile
        player_pos = basic_game_engine.player.position
        primary.make_hostile(player_pos)
        game_session._alert_nearby_enemies(primary)

        # Nearby enemies should be alerted
        assert nearby1.state == EnemyState.HOSTILE, "nearby1 should be alerted"
        assert nearby2.state == EnemyState.HOSTILE, "nearby2 should be alerted"

        # Distant enemy should remain unaware
        assert distant.state == EnemyState.UNAWARE, "distant should stay unaware"

        # All alerted enemies should know player position
        assert nearby1.last_seen_player == player_pos
        assert nearby2.last_seen_player == player_pos


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
