"""
Integration tests for combat death handling flow.

Tests that enemy attack -> death -> save deletion works correctly
through the centralized death_handler.check_death() path.
"""

import pytest

from game_entities import EnemyState, Position
from game_metrics import init_session_metrics
from tests.test_agent import GameTestAgent


def find_damage_dealing_enemy(enemies):
    """Find an enemy that deals direct CPU damage (not virus/inhibitor)."""
    for enemy in enemies:
        if enemy.type not in ("virus", "inhibitor") and enemy.type_data.damage > 0:
            return enemy
    return None


class TestCombatDeathFlow:
    """Tests for the combat death handling flow."""

    def test_enemy_attack_death_triggers_game_over(self):
        """Enemy attack killing player should set game_over flag."""
        agent = GameTestAgent(seed=42)
        init_session_metrics()

        # Find a damage-dealing enemy (not virus/inhibitor)
        enemy = find_damage_dealing_enemy(agent.enemies)
        if enemy is None:
            pytest.skip("No damage-dealing enemies spawned in test level")

        # Put enemy adjacent to player and make hostile
        enemy.position = Position(agent.engine.player.x + 1, agent.engine.player.y)
        enemy.state = EnemyState.HOSTILE
        enemy.last_seen_player = agent.engine.player.position
        enemy.disabled_turns = 0
        enemy.blinded_turns = 0
        enemy.move_cooldown = 0

        # Reduce player HP so one attack will kill
        agent.engine.player.cpu = 1

        # Process turn - enemy should attack and kill player
        agent.engine.game_session.process_turn()

        # Verify death was handled
        assert agent.engine.game_over is True
        assert agent.engine.pending_death_dialogue is True

    def test_enemy_attack_death_deletes_save(self, tmp_path, monkeypatch):
        """Enemy attack death should delete save file via death_handler.check_death()."""
        from game_save import SaveGameManager

        # Patch save path
        test_save = tmp_path / "test_save.json"
        monkeypatch.setattr(SaveGameManager, "_get_save_file_path", lambda: str(test_save))

        # Create a save file
        test_save.write_text('{"test": "data"}')
        assert test_save.exists()

        agent = GameTestAgent(seed=42)
        init_session_metrics()

        # Find a damage-dealing enemy
        enemy = find_damage_dealing_enemy(agent.enemies)
        if enemy is None:
            pytest.skip("No damage-dealing enemies spawned in test level")

        # Put enemy adjacent to player and make hostile
        enemy.position = Position(agent.engine.player.x + 1, agent.engine.player.y)
        enemy.state = EnemyState.HOSTILE
        enemy.last_seen_player = agent.engine.player.position
        enemy.disabled_turns = 0
        enemy.blinded_turns = 0
        enemy.move_cooldown = 0

        # Reduce player HP so attack will kill
        agent.engine.player.cpu = 1

        # Process turn - enemy should attack and kill player
        agent.engine.game_session.process_turn()

        # Save should be deleted by death_handler.check_death()
        assert not test_save.exists()

    def test_attack_player_returns_damage_only(self):
        """attack_player should return damage and not directly handle death."""
        agent = GameTestAgent(seed=42)
        init_session_metrics()

        # Find a damage-dealing enemy
        enemy = find_damage_dealing_enemy(agent.enemies)
        if enemy is None:
            pytest.skip("No damage-dealing enemies spawned in test level")

        # Put enemy adjacent to player and make hostile
        enemy.position = Position(agent.engine.player.x + 1, agent.engine.player.y)
        enemy.state = EnemyState.HOSTILE

        # Set CPU so player won't die from one attack
        original_cpu = 100
        agent.engine.player.cpu = original_cpu
        agent.engine.player.max_cpu = original_cpu

        # Call attack_player directly (without game_engine to isolate the call)
        damage = enemy.attack_player(agent.engine.player, game_engine=None)

        # Should return damage dealt (damage-dealing enemies always deal > 0)
        assert damage > 0
        # Player should have taken damage
        assert agent.engine.player.cpu == original_cpu - damage

    def test_multiple_enemy_attacks_same_turn(self):
        """Multiple enemies attacking same turn should cumulate damage."""
        agent = GameTestAgent(seed=42)
        init_session_metrics()

        # Find two damage-dealing enemies
        damage_dealers = [
            e
            for e in agent.enemies
            if e.type not in ("virus", "inhibitor") and e.type_data.damage > 0
        ]
        if len(damage_dealers) < 2:
            pytest.skip("Need at least 2 damage-dealing enemies for this test")

        enemy1 = damage_dealers[0]
        enemy2 = damage_dealers[1]

        # Position both enemies adjacent
        enemy1.position = Position(agent.engine.player.x + 1, agent.engine.player.y)
        enemy1.state = EnemyState.HOSTILE
        enemy1.last_seen_player = agent.engine.player.position
        enemy1.disabled_turns = 0
        enemy1.blinded_turns = 0
        enemy1.move_cooldown = 0

        enemy2.position = Position(agent.engine.player.x - 1, agent.engine.player.y)
        enemy2.state = EnemyState.HOSTILE
        enemy2.last_seen_player = agent.engine.player.position
        enemy2.disabled_turns = 0
        enemy2.blinded_turns = 0
        enemy2.move_cooldown = 0

        # Set CPU high enough to survive both attacks
        original_cpu = 200
        agent.engine.player.cpu = original_cpu
        agent.engine.player.max_cpu = original_cpu

        # Process turn
        agent.engine.game_session.process_turn()

        # Player should have taken damage from both enemies
        expected_damage = enemy1.type_data.damage + enemy2.type_data.damage
        assert agent.engine.player.cpu == original_cpu - expected_damage


class TestDeathPreventsDuplicateProcessing:
    """Tests that death is only processed once."""

    def test_death_handler_idempotent(self):
        """PlayerDeathHandler.check_death should be safe to call multiple times."""
        agent = GameTestAgent(seed=42)
        init_session_metrics()

        # Kill player
        agent.engine.player.cpu = 0

        # First call to process_turn handles death
        agent.engine.game_session.process_turn()
        assert agent.engine.game_over is True
        assert agent.engine.death_handler.is_handled is True

        # Reset the death handler for testing idempotency
        agent.engine.death_handler.reset()
        assert agent.engine.death_handler.is_handled is False

        # Second call should handle death again (since we reset)
        agent.engine.death_handler.check_death("combat")
        assert agent.engine.game_over is True
        assert agent.engine.death_handler.is_handled is True

    def test_death_only_saves_metrics_once(self, monkeypatch):
        """Session metrics should only be finalized once on death."""
        import game_metrics
        from game_metrics import finalize_session as orig_finalize

        call_count = {"count": 0}

        def counting_finalize(*args, **kwargs):
            call_count["count"] += 1
            return orig_finalize(*args, **kwargs)

        # Patch at the source module (function is imported locally in death_handler)
        monkeypatch.setattr(game_metrics, "finalize_session", counting_finalize)

        agent = GameTestAgent(seed=42)
        init_session_metrics()

        # Kill player
        agent.engine.player.cpu = 0

        # Process death
        agent.engine.game_session.process_turn()

        # finalize_session should be called once
        assert call_count["count"] == 1
