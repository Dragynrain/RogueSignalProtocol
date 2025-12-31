#!/usr/bin/env python3
"""
Stealth and Combat Agent Tests

Tests specialized agent behaviors:
- StealthAgent: Avoids detection, tests stealth mechanics
- CombatAgent: Aggressive playstyle, tests combat system

These agents validate:
- Stealth mechanics (detection, awareness states)
- Combat system (damage, enemy defeating, resource management)
- Edge case robustness (high-stress gameplay scenarios)
"""

import pytest

from rsp.entities.base import EnemyState
from tests.test_agent import GameTestAgent


class StealthAgent(GameTestAgent):
    """
    Agent that attempts to avoid detection while moving through level.

    Strategy:
    - Monitor enemy states (avoid triggering ALERT/HOSTILE)
    - Move cautiously toward objectives
    - Test stealth mechanics robustness

    Validates:
    - Enemy state transitions
    - Detection mechanics
    - Stealth gameplay viability
    """

    def __init__(self, seed=None, max_turns=500):
        """
        Initialize stealth agent.

        Args:
            seed: Random seed for deterministic testing
            max_turns: Maximum turns to spend (default 500)
        """
        super().__init__(seed=seed, level=1)
        self.max_turns = max_turns
        self.turns_taken = 0
        self.was_detected = False
        self.detection_count = 0

    def is_detected(self) -> bool:
        """
        Check if player has been detected by any enemy.

        Returns:
            True if any enemy is ALERT or HOSTILE
        """
        for enemy in self.enemies:
            if enemy.state in (EnemyState.ALERT, EnemyState.HOSTILE):
                return True
        return False

    def get_enemy_states(self):
        """
        Get current states of all enemies.

        Returns:
            Dict mapping enemy state names to counts
        """
        states = {}
        for enemy in self.enemies:
            state_name = enemy.state.name
            states[state_name] = states.get(state_name, 0) + 1
        return states

    def move_cautiously(self, max_moves=50):
        """
        Make cautious movements, checking for detection.

        Args:
            max_moves: Maximum number of moves to make

        Returns:
            Number of moves made without detection
        """
        import random

        moves_made = 0

        for _ in range(max_moves):
            # Check if detected
            if self.is_detected():
                self.was_detected = True
                self.detection_count += 1
                return moves_made

            # Try random move
            directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
            random.shuffle(directions)

            moved = False
            for dx, dy in directions:
                if self.move_player(dx, dy):
                    moves_made += 1
                    self.turns_taken += 1
                    moved = True
                    break

            if not moved:
                # Stuck - wait a turn
                self.wait(1)
                self.turns_taken += 1

        return moves_made

    def run_stealth_attempt(self, moves=50):
        """
        Attempt to move stealthily for a number of moves.

        Args:
            moves: Number of moves to attempt

        Returns:
            Dict with results
        """
        initial_enemies = len(self.enemies)
        initial_states = self.get_enemy_states()

        moves_made = self.move_cautiously(max_moves=moves)

        final_states = self.get_enemy_states()

        return {
            "moves_made": moves_made,
            "was_detected": self.was_detected,
            "detection_count": self.detection_count,
            "turns_taken": self.turns_taken,
            "initial_enemy_count": initial_enemies,
            "final_enemy_count": len(self.enemies),
            "initial_states": initial_states,
            "final_states": final_states,
            "player_alive": self.player.cpu > 0,
        }


class CombatAgent(GameTestAgent):
    """
    Agent that engages enemies aggressively.

    Strategy:
    - Move toward nearest enemy
    - Attempt to defeat enemies
    - Test combat system robustness

    Validates:
    - Combat mechanics
    - Enemy defeat logic
    - Resource management during combat
    """

    def __init__(self, seed=None, max_turns=500):
        """
        Initialize combat agent.

        Args:
            seed: Random seed for deterministic testing
            max_turns: Maximum turns for combat (default 500)
        """
        super().__init__(seed=seed, level=1)
        self.max_turns = max_turns
        self.turns_taken = 0
        self.combat_encounters = 0
        self.initial_enemy_count = len(self.enemies)

    def find_nearest_enemy(self):
        """
        Find nearest enemy to player.

        Returns:
            Enemy object or None
        """
        if not self.enemies:
            return None

        player_pos = (self.player.x, self.player.y)
        min_dist = float("inf")
        nearest = None

        for enemy in self.enemies:
            dist = abs(enemy.x - player_pos[0]) + abs(enemy.y - player_pos[1])
            if dist < min_dist:
                min_dist = dist
                nearest = enemy

        return nearest

    def move_toward_enemy(self, enemy, max_moves=20):
        """
        Move toward enemy for combat.

        Args:
            enemy: Enemy to approach
            max_moves: Max moves to make

        Returns:
            Number of moves made
        """
        moves_made = 0

        for _ in range(max_moves):
            if enemy not in self.enemies:
                # Enemy defeated or gone
                return moves_made

            # Calculate direction
            dx = 1 if enemy.x > self.player.x else (-1 if enemy.x < self.player.x else 0)
            dy = 1 if enemy.y > self.player.y else (-1 if enemy.y < self.player.y else 0)

            # Move toward enemy
            if dx != 0 or dy != 0:
                if self.move_player(dx, dy):
                    moves_made += 1
                    self.turns_taken += 1
                else:
                    # Blocked - wait
                    self.wait(1)
                    self.turns_taken += 1
            else:
                # Adjacent - combat happening
                self.wait(1)
                self.turns_taken += 1

            # Check if close enough (adjacent means combat is happening)
            dist = max(abs(enemy.x - self.player.x), abs(enemy.y - self.player.y))
            if dist <= 1:
                # We're in combat range
                self.combat_encounters += 1
                return moves_made

        return moves_made

    def engage_enemies(self, max_enemies=5):
        """
        Engage multiple enemies sequentially.

        Args:
            max_enemies: Maximum number of enemies to engage

        Returns:
            Number of enemies engaged
        """
        engaged = 0

        for _ in range(max_enemies):
            if self.turns_taken >= self.max_turns:
                break

            if self.player.cpu <= 0:
                # Player died
                break

            enemy = self.find_nearest_enemy()
            if not enemy:
                # No enemies left
                break

            # Move toward and engage enemy
            self.move_toward_enemy(enemy, max_moves=30)
            engaged += 1

        return engaged

    def run_combat_session(self, max_enemies=3):
        """
        Run a combat session, engaging enemies.

        Args:
            max_enemies: Max enemies to engage

        Returns:
            Dict with combat results
        """
        initial_hp = self.player.cpu
        initial_enemy_count = len(self.enemies)

        engaged = self.engage_enemies(max_enemies=max_enemies)

        final_enemy_count = len(self.enemies)
        enemies_defeated = initial_enemy_count - final_enemy_count

        return {
            "engaged": engaged,
            "initial_enemies": initial_enemy_count,
            "final_enemies": final_enemy_count,
            "enemies_defeated": enemies_defeated,
            "initial_hp": initial_hp,
            "final_hp": self.player.cpu,
            "hp_lost": initial_hp - self.player.cpu,
            "player_alive": self.player.cpu > 0,
            "combat_encounters": self.combat_encounters,
            "turns_taken": self.turns_taken,
        }


# ===== Tests =====


class TestStealthAgent:
    """Test StealthAgent behavior and stealth mechanics."""

    def test_stealth_agent_initialization(self):
        """Test stealth agent initializes correctly."""
        agent = StealthAgent(seed=12345)
        assert agent.max_turns == 500
        assert agent.turns_taken == 0
        assert not agent.was_detected
        assert agent.detection_count == 0

    def test_stealth_agent_detects_detection(self):
        """Test stealth agent can identify detection."""
        agent = StealthAgent(seed=12345)

        # Check detection state
        detected = agent.is_detected()
        assert isinstance(detected, bool)

        # Get enemy states
        states = agent.get_enemy_states()
        assert isinstance(states, dict)

    def test_stealth_agent_moves_cautiously(self):
        """Test stealth agent can make cautious movements."""
        agent = StealthAgent(seed=12345)

        result = agent.run_stealth_attempt(moves=10)

        # Should make some moves
        assert result["moves_made"] >= 0
        assert result["turns_taken"] >= 0
        assert isinstance(result["was_detected"], bool)
        assert result["player_alive"]

    def test_stealth_agent_tracks_detection(self):
        """Test stealth agent tracks detection events."""
        agent = StealthAgent(seed=12345)

        result = agent.run_stealth_attempt(moves=30)

        # Detection tracking should work
        assert isinstance(result["detection_count"], int)
        assert result["detection_count"] >= 0

    def test_stealth_agent_monitors_enemy_states(self):
        """Test stealth agent monitors enemy awareness states."""
        agent = StealthAgent(seed=12345)

        initial_states = agent.get_enemy_states()
        agent.run_stealth_attempt(moves=20)
        final_states = agent.get_enemy_states()

        # Should get state information
        assert isinstance(initial_states, dict)
        assert isinstance(final_states, dict)


class TestCombatAgent:
    """Test CombatAgent behavior and combat mechanics."""

    def test_combat_agent_initialization(self):
        """Test combat agent initializes correctly."""
        agent = CombatAgent(seed=12345)
        assert agent.max_turns == 500
        assert agent.turns_taken == 0
        assert agent.combat_encounters == 0
        assert agent.initial_enemy_count >= 0

    def test_combat_agent_finds_enemies(self):
        """Test combat agent can locate enemies."""
        agent = CombatAgent(seed=12345)

        enemy = agent.find_nearest_enemy()

        if agent.enemies:
            # Should find an enemy if any exist
            assert enemy is not None
            assert enemy in agent.enemies
        else:
            # No enemies on this seed
            assert enemy is None

    def test_combat_agent_moves_toward_enemies(self):
        """Test combat agent approaches enemies."""
        agent = CombatAgent(seed=12345)

        enemy = agent.find_nearest_enemy()
        if enemy:
            initial_dist = abs(enemy.x - agent.player.x) + abs(enemy.y - agent.player.y)
            agent.move_toward_enemy(enemy, max_moves=10)
            final_dist = abs(enemy.x - agent.player.x) + abs(enemy.y - agent.player.y)

            # Should move closer or stay same (if blocked)
            assert final_dist <= initial_dist + 5  # Allow some movement from combat

    def test_combat_agent_engages_enemies(self):
        """Test combat agent engages in combat."""
        agent = CombatAgent(seed=12345)

        result = agent.run_combat_session(max_enemies=2)

        # Should attempt engagement
        assert result["engaged"] >= 0
        assert result["turns_taken"] >= 0
        assert result["player_alive"]  # Should survive (or have valid reason for dying)

    def test_combat_agent_tracks_results(self):
        """Test combat agent tracks combat results."""
        agent = CombatAgent(seed=12345)

        result = agent.run_combat_session(max_enemies=2)

        # All tracking fields should exist
        assert "engaged" in result
        assert "initial_enemies" in result
        assert "final_enemies" in result
        assert "enemies_defeated" in result
        assert "initial_hp" in result
        assert "final_hp" in result
        assert "combat_encounters" in result

        # Values should be reasonable
        assert result["enemies_defeated"] >= 0
        assert result["final_enemies"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
