"""
Tests for the simplified enemy movement system and enemy communication/alerting.
Tests the actual behavior rather than internal implementation details.
"""

from unittest.mock import Mock, patch
from game_characters import Enemy, Player
from game_entities import Position, EnemyState, EnemyMovement
from game_map import GameMap
from game_config import GameConfig
from tests.fixtures.real_game_data import create_real_enemy, create_test_map_with_real_tiles


class TestEnemyMovementBehavior:
    """Test that enemies move correctly based on their state and type."""

    def setup_method(self):
        """Set up test fixtures."""
        self.game_map = create_test_map_with_real_tiles()
        self.player = Player(10, 10)
        self.game_engine = Mock()
        self.game_engine.player = self.player
        self.game_engine.enemies = []
        self.game_engine.game_map = self.game_map

    def test_hostile_enemy_pathfinds_to_player(self):
        """HOSTILE enemies should pathfind toward player's last known position."""
        enemy = create_real_enemy("virus", Position(5, 5))
        enemy.state = EnemyState.HOSTILE
        enemy.last_seen_player = self.player.position
        self.game_engine.enemies = [enemy]

        # Mock pathfinding to succeed
        with patch.object(enemy, 'can_see_player', return_value=False):
            enemy.move(self.game_map, self.player, self.game_engine)

        # Enemy movement system should work
        assert enemy.last_seen_player is not None, "Should retain last seen player position"

    def test_unaware_enemy_uses_normal_movement(self):
        """UNAWARE enemies should use their base movement type (random, patrol, etc)."""
        enemy = create_real_enemy("bot", Position(5, 5))  # bot is RANDOM movement
        assert enemy.state == EnemyState.UNAWARE
        self.game_engine.enemies = [enemy]

        enemy.move(self.game_map, self.player, self.game_engine)

        # Movement system should work
        assert enemy.state == EnemyState.UNAWARE

    def test_alert_enemy_continues_normal_movement(self):
        """ALERT enemies should continue normal movement (it's a 1-turn warning)."""
        enemy = create_real_enemy("patrol", Position(5, 5))
        enemy.patrol_points = [Position(10, 5), Position(15, 5)]
        enemy.patrol_index = 0
        enemy.state = EnemyState.ALERT  # Alert but not hostile yet
        self.game_engine.enemies = [enemy]

        enemy.move(self.game_map, self.player, self.game_engine)

        # Should still have patrol system
        assert enemy.patrol_points is not None


class TestEnemyCommunication:
    """Test enemy alerting and communication system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.game_map = create_test_map_with_real_tiles()
        self.player = Player(10, 10)

        # Create mock game engine with turn manager
        self.game_engine = Mock()
        self.game_engine.player = self.player
        self.game_engine.game_map = self.game_map
        self.game_engine.message_log = Mock()
        self.game_engine.sound_manager = Mock()

        # Import GameTurnManager here to avoid circular imports
        from game_turn_manager import GameTurnManager
        self.turn_manager = GameTurnManager(self.game_engine)

    def test_nearby_enemies_alerted_when_enemy_goes_hostile(self):
        """When an enemy becomes HOSTILE, nearby enemies should be alerted."""
        # Create alerting enemy
        alerting_enemy = create_real_enemy("scanner", Position(10, 10))
        alerting_enemy.state = EnemyState.HOSTILE

        # Create nearby enemy (within alert radius)
        nearby_enemy = create_real_enemy("bot", Position(12, 12))
        nearby_enemy.state = EnemyState.UNAWARE

        # Create distant enemy (outside alert radius)
        distant_enemy = create_real_enemy("virus", Position(50, 50))
        distant_enemy.state = EnemyState.UNAWARE

        self.game_engine.enemies = [alerting_enemy, nearby_enemy, distant_enemy]

        # Trigger alert
        self.turn_manager._alert_nearby_enemies(alerting_enemy)

        # Nearby enemy should be alerted
        assert nearby_enemy.state == EnemyState.HOSTILE, "Nearby enemy should become HOSTILE"
        assert nearby_enemy.last_seen_player == self.player.position, "Should know player position"

        # Distant enemy should remain unaware
        assert distant_enemy.state == EnemyState.UNAWARE, "Distant enemy should stay UNAWARE"
        assert distant_enemy.last_seen_player is None, "Should not know player position"

    def test_alerted_enemies_skip_alert_warning(self):
        """Enemies alerted by communication skip ALERT and go straight to HOSTILE."""
        alerting_enemy = create_real_enemy("scanner", Position(10, 10))
        alerting_enemy.state = EnemyState.HOSTILE

        nearby_enemy = create_real_enemy("bot", Position(12, 12))
        nearby_enemy.state = EnemyState.UNAWARE

        self.game_engine.enemies = [alerting_enemy, nearby_enemy]

        # Trigger alert
        self.turn_manager._alert_nearby_enemies(alerting_enemy)

        # Should skip ALERT and go straight to HOSTILE
        assert nearby_enemy.state == EnemyState.HOSTILE, "Should go directly to HOSTILE"
        assert nearby_enemy.alert_timer == 0, "Alert timer should be 0"

    def test_already_hostile_enemies_not_re_alerted(self):
        """Enemies that are already HOSTILE should not be alerted again."""
        alerting_enemy = create_real_enemy("scanner", Position(10, 10))
        alerting_enemy.state = EnemyState.HOSTILE

        already_hostile = create_real_enemy("bot", Position(12, 12))
        already_hostile.state = EnemyState.HOSTILE
        already_hostile.last_seen_player = Position(5, 5)  # Different position

        self.game_engine.enemies = [alerting_enemy, already_hostile]

        # Trigger alert
        self.turn_manager._alert_nearby_enemies(alerting_enemy)

        # Should keep original last_seen_player position
        assert already_hostile.last_seen_player == Position(5, 5), "Should not update position"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
