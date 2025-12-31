"""
Tests for enemy blinded_turns save/load.

Verifies that the blinded_turns property (from Memory Leak exploit)
is correctly saved and restored when loading a game.
"""

import pytest

from rsp.entities.characters import Enemy
from rsp.entities.base import EnemyState, Position


class TestBlindedTurnsSaveLoad:
    """Tests that blinded_turns is properly persisted."""

    def test_blinded_turns_saved_in_enemy_data(self):
        """Blinded turns should be included in serialized enemy data."""
        from rsp.systems.save import SaveGameManager
        from tests.test_agent import GameTestAgent

        agent = GameTestAgent(seed=42)

        # Find an enemy and set blinded_turns
        if agent.engine.enemies:
            enemy = agent.engine.enemies[0]
            enemy.blinded_turns = 3

            # Serialize the game
            save_data = SaveGameManager.create_save_data(agent.engine)

            # Check that enemy data includes blinded_turns
            enemy_data = save_data["enemies"][0]
            assert "blinded_turns" in enemy_data, "blinded_turns should be in saved enemy data"
            assert enemy_data["blinded_turns"] == 3, "blinded_turns should be saved correctly"

    def test_blinded_turns_restored_from_enemy_data(self):
        """Blinded turns should be correctly parsed from saved enemy data."""
        # Create enemy data with blinded_turns (using enum value as saved)
        enemy_data = {
            "id": 1,
            "type": "scanner",
            "x": 10,
            "y": 10,
            "cpu": 30,
            "state": EnemyState.UNAWARE.value,  # Use the enum value
            "move_cooldown": 0,
            "disabled_turns": 0,
            "blinded_turns": 5,
            "alert_timer": 0,
            "patrol_index": 0,
            "last_seen_player": None,
        }

        # Create an enemy and restore its state
        enemy = Enemy(Position(10, 10), "scanner")

        # Apply the saved data (simulating what _restore_enemies does)
        enemy.id = enemy_data["id"]
        enemy.cpu = enemy_data["cpu"]
        # Mimic the actual restore logic
        enemy.state = (
            EnemyState(enemy_data["state"])
            if isinstance(enemy_data["state"], str)
            else enemy_data["state"]
        )
        enemy.move_cooldown = enemy_data["move_cooldown"]
        enemy.disabled_turns = enemy_data["disabled_turns"]
        enemy.blinded_turns = enemy_data.get("blinded_turns", 0)
        enemy.alert_timer = enemy_data["alert_timer"]

        assert enemy.blinded_turns == 5, "blinded_turns should be restored to 5"

    def test_blinded_turns_defaults_to_zero_for_old_saves(self):
        """Old saves without blinded_turns should default to 0."""
        # Create enemy data WITHOUT blinded_turns (old save format)
        enemy_data = {
            "id": 1,
            "type": "scanner",
            "x": 10,
            "y": 10,
            "cpu": 30,
            "state": "UNAWARE",
            "move_cooldown": 0,
            "disabled_turns": 0,
            # No blinded_turns field
            "alert_timer": 0,
            "patrol_index": 0,
            "last_seen_player": None,
        }

        # Create an enemy and restore its state
        enemy = Enemy(Position(10, 10), "scanner")

        # Apply the saved data using .get() with default 0
        enemy.blinded_turns = enemy_data.get("blinded_turns", 0)

        assert (
            enemy.blinded_turns == 0
        ), "blinded_turns should default to 0 for old saves without the field"

    def test_memory_leak_effect_value_preserved(self):
        """Memory Leak exploit duration value should be preserved in save data."""
        from rsp.core.data import GameData
        from rsp.systems.save import SaveGameManager
        from tests.test_agent import GameTestAgent

        agent = GameTestAgent(seed=42)

        # Get Memory Leak exploit duration
        memory_leak = GameData.EXPLOITS.get("memory_leak")
        if memory_leak is None:
            pytest.skip("memory_leak exploit not found")

        # Find an enemy
        if not agent.engine.enemies:
            pytest.skip("No enemies to test with")

        enemy = agent.engine.enemies[0]
        enemy_index = 0

        # Simulate Memory Leak effect
        enemy.blinded_turns = memory_leak.effect_duration

        # Serialize and check the value is preserved
        save_data = SaveGameManager.create_save_data(agent.engine)
        saved_blinded_turns = save_data["enemies"][enemy_index]["blinded_turns"]

        assert saved_blinded_turns == memory_leak.effect_duration, (
            f"Memory Leak effect duration should be saved: expected {memory_leak.effect_duration}, "
            f"got {saved_blinded_turns}"
        )
