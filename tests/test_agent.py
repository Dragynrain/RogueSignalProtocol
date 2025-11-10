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
            True if move was successful, False if blocked
        """
        old_pos = (self.player.x, self.player.y)
        self.engine.move_player(dx, dy)
        new_pos = (self.player.x, self.player.y)
        return old_pos != new_pos

    def move_to(self, x: int, y: int, max_steps: int = 100) -> bool:
        """
        Move player to absolute position using pathfinding.

        Args:
            x: Target x coordinate
            y: Target y coordinate
            max_steps: Maximum number of steps to take (prevents infinite loops)

        Returns:
            True if reached destination, False if blocked or max_steps exceeded
        """
        import tcod
        import numpy as np
        from game_config import GameConfig

        for step in range(max_steps):
            if self.player.x == x and self.player.y == y:
                return True

            # Build cost map from walls (1 = walkable, 0 = blocked)
            # TCOD pathfinding needs numpy array
            cost = np.ones((GameConfig.MAP_HEIGHT, GameConfig.MAP_WIDTH), dtype=np.int8)
            for wall_x, wall_y in self.game_map.walls:
                cost[wall_y, wall_x] = 0

            graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
            pathfinder = tcod.path.Pathfinder(graph)

            pathfinder.add_root((self.player.x, self.player.y))
            path = pathfinder.path_to((x, y))

            if len(path) == 0:
                return False  # No path found

            next_x, next_y = path[0]
            dx = next_x - self.player.x
            dy = next_y - self.player.y

            if not self.move_player(dx, dy):
                return False  # Blocked

        return False  # Max steps exceeded

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
