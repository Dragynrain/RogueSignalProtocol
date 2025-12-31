#!/usr/bin/env python3
"""
Integration tests for Enemy State Save/Load (Deep Dive Fixes).

Tests roundtrip save/load for enemy fields that were previously missing:
- original_patrol_index: For hostile enemies returning to patrol
- original_movement_type: For virus mimic behavior
- max_cpu: For proper HP display across ascension levels
"""


from rsp.entities.base import EnemyMovement, EnemyState, Position
from rsp.entities.characters import Enemy


class TestEnemyPatrolStateRoundtrip:
    """Test original_patrol_index is saved and restored."""

    def test_original_patrol_index_serialized(self):
        """Verify original_patrol_index is included in serialized data."""
        from rsp.systems.save import SaveGameManager

        enemy = Enemy(Position(5, 5), "scanner")
        enemy.patrol_points = [Position(1, 1), Position(3, 3), Position(5, 5)]
        enemy.patrol_index = 2
        enemy.original_patrol_index = 0  # Was at patrol point 0 when became hostile

        serialized = SaveGameManager._serialize_enemies([enemy])

        assert len(serialized) == 1
        assert "original_patrol_index" in serialized[0]
        assert serialized[0]["original_patrol_index"] == 0

    def test_original_patrol_index_restored(self, basic_game_engine):
        """Verify original_patrol_index is restored from save data."""
        from rsp.systems.persistence import GameStatePersistence

        enemy_data = {
            "id": "test_enemy",
            "type": "scanner",
            "x": 5,
            "y": 5,
            "cpu": 20,
            "max_cpu": 25,
            "state": EnemyState.HOSTILE.value,
            "move_cooldown": 0,
            "disabled_turns": 0,
            "blinded_turns": 0,
            "alert_timer": 0,
            "patrol_index": 2,
            "original_patrol_index": 0,
            "patrol_points": [{"x": 1, "y": 1}, {"x": 3, "y": 3}, {"x": 5, "y": 5}],
            "last_seen_player": {"x": 10, "y": 10},
        }

        persistence = GameStatePersistence(basic_game_engine)
        persistence._restore_enemies([enemy_data])

        assert len(basic_game_engine.enemies) == 1
        restored = basic_game_engine.enemies[0]
        assert restored.original_patrol_index == 0
        assert restored.patrol_index == 2

    def test_original_patrol_index_defaults_to_zero(self, basic_game_engine):
        """Old saves without original_patrol_index should default to 0."""
        from rsp.systems.persistence import GameStatePersistence

        # Simulate old save format without original_patrol_index
        enemy_data = {
            "id": "test_enemy",
            "type": "scanner",
            "x": 5,
            "y": 5,
            "cpu": 20,
            "state": EnemyState.UNAWARE.value,
            "move_cooldown": 0,
            "disabled_turns": 0,
            "alert_timer": 0,
            "patrol_index": 1,
        }

        persistence = GameStatePersistence(basic_game_engine)
        persistence._restore_enemies([enemy_data])

        assert len(basic_game_engine.enemies) == 1
        restored = basic_game_engine.enemies[0]
        assert restored.original_patrol_index == 0  # Default value


class TestVirusMovementTypeRoundtrip:
    """Test original_movement_type is saved and restored for virus enemies."""

    def test_original_movement_type_serialized(self):
        """Verify original_movement_type is included in serialized data."""
        from rsp.systems.save import SaveGameManager

        enemy = Enemy(Position(5, 5), "virus")
        enemy.original_movement_type = EnemyMovement.PATROL

        serialized = SaveGameManager._serialize_enemies([enemy])

        assert len(serialized) == 1
        assert "original_movement_type" in serialized[0]
        assert serialized[0]["original_movement_type"] == EnemyMovement.PATROL.value

    def test_original_movement_type_not_serialized_when_none(self):
        """Verify original_movement_type is omitted when None."""
        from rsp.systems.save import SaveGameManager

        enemy = Enemy(Position(5, 5), "scanner")
        # Default is None for non-virus enemies
        assert enemy.original_movement_type is None

        serialized = SaveGameManager._serialize_enemies([enemy])

        assert "original_movement_type" not in serialized[0]

    def test_original_movement_type_restored(self, basic_game_engine):
        """Verify original_movement_type is restored from save data."""
        from rsp.systems.persistence import GameStatePersistence

        enemy_data = {
            "id": "virus_enemy",
            "type": "virus",
            "x": 7,
            "y": 7,
            "cpu": 15,
            "max_cpu": 20,
            "state": EnemyState.HOSTILE.value,
            "move_cooldown": 0,
            "disabled_turns": 0,
            "blinded_turns": 0,
            "alert_timer": 0,
            "patrol_index": 0,
            "original_patrol_index": 0,
            "original_movement_type": EnemyMovement.STATIC.value,
            "last_seen_player": {"x": 10, "y": 10},
        }

        persistence = GameStatePersistence(basic_game_engine)
        persistence._restore_enemies([enemy_data])

        assert len(basic_game_engine.enemies) == 1
        restored = basic_game_engine.enemies[0]
        assert restored.original_movement_type == EnemyMovement.STATIC


class TestEnemyMaxCpuRoundtrip:
    """Test max_cpu is saved and restored correctly."""

    def test_max_cpu_serialized(self):
        """Verify max_cpu is included in serialized data."""
        from rsp.systems.save import SaveGameManager

        enemy = Enemy(Position(5, 5), "scanner")
        enemy.cpu = 20
        enemy.max_cpu = 30

        serialized = SaveGameManager._serialize_enemies([enemy])

        assert len(serialized) == 1
        assert "max_cpu" in serialized[0]
        assert serialized[0]["max_cpu"] == 30
        assert serialized[0]["cpu"] == 20

    def test_max_cpu_restored_exactly(self, basic_game_engine):
        """Verify max_cpu is restored to exact saved value."""
        from rsp.systems.persistence import GameStatePersistence

        enemy_data = {
            "id": "damaged_enemy",
            "type": "scanner",
            "x": 5,
            "y": 5,
            "cpu": 15,
            "max_cpu": 35,  # Could be from higher ascension level
            "state": EnemyState.UNAWARE.value,
            "move_cooldown": 0,
            "disabled_turns": 0,
            "blinded_turns": 0,
            "alert_timer": 0,
            "patrol_index": 0,
        }

        persistence = GameStatePersistence(basic_game_engine)
        persistence._restore_enemies([enemy_data])

        assert len(basic_game_engine.enemies) == 1
        restored = basic_game_engine.enemies[0]
        # Both cpu and max_cpu should match saved values exactly
        assert restored.cpu == 15
        assert restored.max_cpu == 35

    def test_max_cpu_defaults_to_type_max_for_old_saves(self, basic_game_engine):
        """Old saves without max_cpu should use enemy type default."""
        from rsp.systems.persistence import GameStatePersistence

        # Simulate old save format without max_cpu
        enemy_data = {
            "id": "old_enemy",
            "type": "scanner",
            "x": 5,
            "y": 5,
            "cpu": 20,
            # max_cpu not present
            "state": EnemyState.UNAWARE.value,
            "move_cooldown": 0,
            "disabled_turns": 0,
            "alert_timer": 0,
            "patrol_index": 0,
        }

        persistence = GameStatePersistence(basic_game_engine)
        persistence._restore_enemies([enemy_data])

        restored = basic_game_engine.enemies[0]
        # Should use the enemy's default max_cpu (set on creation)
        # The exact value depends on GameData.ENEMY_TYPES["scanner"]["cpu"]
        assert restored.cpu == 20
        assert restored.max_cpu > 0  # Should have some value


class TestEnemyStateFullRoundtrip:
    """Test complete enemy state survives save/load cycle."""

    def test_hostile_patrol_enemy_roundtrip(self, basic_game_engine):
        """Test patrol enemy that became hostile roundtrips correctly."""
        from rsp.systems.persistence import GameStatePersistence
        from rsp.systems.save import SaveGameManager

        # Create an enemy that was patrolling and became hostile
        enemy = Enemy(Position(5, 5), "scanner")
        enemy.patrol_points = [Position(1, 1), Position(3, 3), Position(5, 5)]
        enemy.patrol_index = 2
        enemy.original_patrol_index = 0
        enemy.state = EnemyState.HOSTILE
        enemy.cpu = 20
        enemy.max_cpu = 30
        enemy.last_seen_player = Position(10, 10)
        enemy.move_queue = [Position(6, 6), Position(7, 7)]

        # Serialize
        serialized = SaveGameManager._serialize_enemies([enemy])

        # Verify all fields present
        assert serialized[0]["original_patrol_index"] == 0
        assert serialized[0]["patrol_index"] == 2
        assert serialized[0]["max_cpu"] == 30
        assert serialized[0]["state"] == "hostile"
        assert len(serialized[0]["move_queue"]) == 2

        # Restore to a fresh engine
        persistence = GameStatePersistence(basic_game_engine)
        persistence._restore_enemies(serialized)

        restored = basic_game_engine.enemies[0]
        assert restored.original_patrol_index == 0
        assert restored.patrol_index == 2
        assert restored.cpu == 20
        assert restored.max_cpu == 30
        assert restored.state == EnemyState.HOSTILE
        assert len(restored.move_queue) == 2

    def test_virus_mimic_enemy_roundtrip(self, basic_game_engine):
        """Test virus enemy with mimic behavior roundtrips correctly."""
        from rsp.systems.persistence import GameStatePersistence
        from rsp.systems.save import SaveGameManager

        # Create a virus that was mimicking a static enemy
        enemy = Enemy(Position(7, 7), "virus")
        enemy.original_movement_type = EnemyMovement.STATIC
        enemy.state = EnemyState.HOSTILE
        enemy.cpu = 10
        enemy.max_cpu = 15

        # Serialize
        serialized = SaveGameManager._serialize_enemies([enemy])

        assert serialized[0]["original_movement_type"] == "static"

        # Restore
        persistence = GameStatePersistence(basic_game_engine)
        persistence._restore_enemies(serialized)

        restored = basic_game_engine.enemies[0]
        assert restored.original_movement_type == EnemyMovement.STATIC
        assert restored.type == "virus"
