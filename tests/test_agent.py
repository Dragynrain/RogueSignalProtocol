#!/usr/bin/env python3
"""
Game Test Agent Framework

Provides headless game simulation for automated testing.
Allows programmatic control of game state and actions without rendering.
"""

import random
from typing import List, Tuple, Optional, Dict, Any
from game_engine import GameEngine
from game_entities import Position
from game_characters import Enemy
from game_config import GameConfig


class GameTestAgent:
    """
    Base class for automated game testing agents.

    Provides headless game simulation with direct state access and
    programmatic action execution. Useful for integration testing,
    regression testing, and gameplay validation.

    Example:
        agent = GameTestAgent(seed=12345)
        agent.move_player(1, 0)  # Move right
        assert agent.player.x == 6
        agent.attack_at(agent.player.x + 1, agent.player.y)
    """

    def __init__(self, seed: Optional[int] = None, level: int = 1):
        """
        Initialize a headless game instance for testing.

        Args:
            seed: Random seed for deterministic testing (optional)
            level: Starting level (default 1)
        """
        if seed is not None:
            random.seed(seed)

        # Create headless engine (no rendering, no audio)
        self.engine = GameEngine(headless=True, load_save=False)

        # Dismiss intro dialogue for clean test state
        if self.engine.dialogue_state.is_active():
            self.engine.dialogue_state.close()

        # Set level if different from default
        if level != 1:
            self.engine.level = level

    @property
    def player(self):
        """Direct access to player object."""
        return self.engine.player

    @property
    def game_map(self):
        """Direct access to game map."""
        return self.engine.game_map

    @property
    def enemies(self) -> List[Enemy]:
        """Get list of all active enemies."""
        return self.engine.enemies

    @property
    def message_log(self):
        """Access to game message log."""
        return self.engine.message_log

    @property
    def turn(self) -> int:
        """Current turn number."""
        return self.engine.turn

    def get_state(self) -> Dict[str, Any]:
        """
        Get comprehensive game state snapshot.

        Returns:
            Dictionary with player stats, positions, enemies, and visibility
        """
        return {
            'player_hp': self.player.cpu,
            'player_max_hp': self.player.max_cpu,
            'player_heat': self.player.heat,
            'player_pos': (self.player.x, self.player.y),
            'player_trace': self.player.trace_level,
            'enemies': [
                {
                    'type': e.type,
                    'pos': (e.x, e.y),
                    'hp': e.cpu,
                    'state': e.state.name
                }
                for e in self.enemies
            ],
            'visible_tiles': len(self.engine.visible_tiles),
            'turn': self.turn,
            'level': self.engine.level,
            'game_over': self.engine.game_over
        }

    def move_player(self, dx: int, dy: int) -> bool:
        """
        Move player by delta coordinates.

        Args:
            dx: Change in x (-1, 0, or 1)
            dy: Change in y (-1, 0, or 1)

        Returns:
            True if move was successful (including bump attacks), False if blocked by wall
        """
        from game_entities import Position

        old_pos = (self.player.x, self.player.y)

        # Check if there's an enemy at target position (before move)
        target_x = self.player.x + dx
        target_y = self.player.y + dy
        target_pos = Position(target_x, target_y)
        had_enemy = self._get_enemy_at(target_pos) is not None

        # Perform move (or bump attack if enemy present)
        self.engine.move_player(dx, dy)

        new_pos = (self.player.x, self.player.y)

        # Success if position changed (moved) OR we attacked an enemy (stayed but attacked)
        return old_pos != new_pos or had_enemy

    def _get_enemy_at(self, position):
        """Get enemy at position (helper for move_player)."""
        return self.engine._get_enemy_at(position)

    def move_to(self, x: int, y: int, max_steps: int = 100, debug: bool = False) -> bool:
        """
        Move player to absolute position using pathfinding.

        Args:
            x: Target x coordinate
            y: Target y coordinate
            max_steps: Maximum number of steps to take (prevents infinite loops)
            debug: Enable debug logging for pathfinding diagnostics

        Returns:
            True if made progress (moved or attacked), False if blocked
            Note: Returns True even if destination not reached (when max_steps < full path)
        """
        import tcod
        import numpy as np
        from game_config import GameConfig
        import logging

        made_progress = False

        for step in range(max_steps):
            if self.player.x == x and self.player.y == y:
                return True

            # Build cost map from walls
            # TCOD expects: 0 or negative = blocked, positive = walkable with that cost
            # But pathfinder seems to prefer LOW costs, so use high values for walls
            cost = np.ones((GameConfig.MAP_HEIGHT, GameConfig.MAP_WIDTH), dtype=np.uint8)
            for wall_x, wall_y in self.game_map.walls:
                cost[wall_y, wall_x] = 0  # Blocked (0 or negative)

            if debug:
                logging.debug(f"[PATHFIND] Step {step}: ({self.player.x},{self.player.y}) -> ({x},{y})")
                # Check for obvious problems
                if cost[y, x] == 0:
                    logging.warning(f"[PATHFIND] Target ({x},{y}) is a wall!")
                if cost[self.player.y, self.player.x] == 0:
                    logging.warning(f"[PATHFIND] Player at ({self.player.x},{self.player.y}) is in a wall!")

            graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
            pathfinder = tcod.path.Pathfinder(graph)

            # CRITICAL: TCOD pathfinding uses (y, x) coordinates, not (x, y)!
            pathfinder.add_root((self.player.y, self.player.x))
            path = pathfinder.path_to((y, x))

            if len(path) == 0:
                if debug:
                    logging.debug(f"[PATHFIND] No path found from ({self.player.x},{self.player.y}) to ({x},{y})")
                return made_progress  # Return True if we made any progress before this

            # TCOD includes starting position as first element - skip it
            # Path returns (y, x) coordinates, so we need to swap them
            path_to_walk = [p for p in path if tuple(p) != (self.player.y, self.player.x)]

            if len(path_to_walk) == 0:
                # Already at destination (path only contains current position)
                return True

            # Path returns (y, x), swap to (x, y)
            next_y, next_x = path_to_walk[0]
            dx = next_x - self.player.x
            dy = next_y - self.player.y

            move_success = self.move_player(dx, dy)

            if debug and not move_success:
                logging.debug(f"[PATHFIND] Move blocked at ({self.player.x},{self.player.y}) with delta ({dx},{dy})")

            if not move_success:
                return made_progress  # Return True if we made progress before getting blocked

            made_progress = True  # Successfully moved or attacked

        # Reached max steps but made progress
        return made_progress

    def wait(self, turns: int = 1):
        """
        Wait for specified number of turns.

        Args:
            turns: Number of turns to wait
        """
        for _ in range(turns):
            self.engine.process_turn()

    def get_enemy_at(self, x: int, y: int) -> Optional[Enemy]:
        """
        Get enemy at specific position.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Enemy at position, or None if no enemy present
        """
        pos = Position(x, y)
        return self.engine._get_enemy_at(pos)

    def spawn_enemy(self, enemy_type: str, x: int, y: int) -> Enemy:
        """
        Spawn an enemy at specific position (for testing).

        Args:
            enemy_type: Type of enemy (e.g., 'drone', 'sentinel')
            x: X coordinate
            y: Y coordinate

        Returns:
            The spawned enemy
        """
        enemy = Enemy(Position(x, y), enemy_type)
        self.engine.enemies.append(enemy)
        return enemy

    def is_visible(self, x: int, y: int) -> bool:
        """
        Check if tile is visible to player.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            True if tile is in player's FOV
        """
        return (x, y) in self.engine.visible_tiles

    def is_explored(self, x: int, y: int) -> bool:
        """
        Check if tile has been explored.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            True if tile has been seen before
        """
        return (x, y) in self.game_map.explored_tiles

    def get_messages(self) -> List[str]:
        """
        Get all messages from message log.

        Returns:
            List of message strings
        """
        return [msg.text for msg in self.message_log.messages]

    def clear_messages(self):
        """Clear the message log."""
        self.message_log.messages.clear()

    def get_exploit_targets(self, exploit_name: str) -> List[Tuple[int, int]]:
        """
        Get valid targets for an exploit.

        Args:
            exploit_name: Name of the exploit

        Returns:
            List of (x, y) coordinates of valid targets
        """
        # This would integrate with the exploit system
        # For now, return enemy positions as potential targets
        return [(e.x, e.y) for e in self.enemies]

    def assert_no_errors(self):
        """Assert that no error messages are in the log."""
        messages = self.get_messages()
        for msg in messages:
            assert "error" not in msg.lower(), f"Error in message log: {msg}"

    def assert_alive(self):
        """Assert that player is still alive."""
        assert self.player.cpu > 0, f"Player is dead (CPU: {self.player.cpu})"
        assert not self.engine.game_over, "Game is over"

    def print_state(self):
        """Print current game state (for debugging)."""
        state = self.get_state()
        print(f"\n=== Game State (Turn {state['turn']}) ===")
        print(f"Player: HP={state['player_hp']}/{state['player_max_hp']}, "
              f"Heat={state['player_heat']}, Pos={state['player_pos']}")
        print(f"Enemies: {len(state['enemies'])}")
        for enemy in state['enemies']:
            print(f"  - {enemy['type']} at {enemy['pos']}, HP={enemy['hp']}, State={enemy['state']}")
        print(f"Visible tiles: {state['visible_tiles']}")
        print(f"Messages: {len(self.get_messages())}")
        print("=" * 40)

    def get_position_by_offset(self, dx: int, dy: int) -> Position:
        """
        Get position offset from player's current position.

        Args:
            dx: Offset in x direction
            dy: Offset in y direction

        Returns:
            Position object at player_x + dx, player_y + dy
        """
        return Position(self.player.x + dx, self.player.y + dy)
