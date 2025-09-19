#!/usr/bin/env python3
"""
Builder pattern test fixtures for TDD.
Provides fluent interfaces for creating test objects.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from unittest.mock import Mock

from game_entities import Position, EnemyState, EnemyMovement
from game_characters import Player, Enemy


class PlayerBuilder:
    """Builder for creating test Player objects with fluent interface."""
    
    def __init__(self):
        self._cpu = 100
        self._heat = 0
        self._detection = 0
        self._position = Position(5, 5)
        self._inventory = None
        self._temporary_effects = {}
        self._attributes = {}
    
    def with_cpu(self, cpu: int):
        """Set player CPU."""
        self._cpu = cpu
        return self
    
    def with_heat(self, heat: int):
        """Set player heat level."""
        self._heat = heat
        return self
    
    def with_detection(self, detection: int):
        """Set player detection level."""
        self._detection = detection
        return self
    
    def at_position(self, x: int, y: int):
        """Set player position."""
        self._position = Position(x, y)
        return self
    
    def with_effect(self, effect_name: str, duration: int):
        """Add temporary effect."""
        self._temporary_effects[effect_name] = duration
        return self
    
    def with_low_cpu(self):
        """Set player to low CPU (below 30)."""
        self._cpu = 25
        return self
    
    def with_high_heat(self):
        """Set player to high heat level."""
        self._heat = 80
        return self
    
    def critically_damaged(self):
        """Set player to critical state."""
        self._cpu = 10
        self._heat = 90
        self._detection = 95
        return self
    
    def with_attribute(self, name: str, value: Any):
        """Set custom attribute for testing."""
        self._attributes[name] = value
        return self
    
    def build(self) -> Mock:
        """Build the Player mock object."""
        player = Mock()
        player.cpu = self._cpu
        player.heat = self._heat
        player.detection = self._detection
        player.position = self._position
        player.temporary_effects = self._temporary_effects.copy()
        
        # Add any custom attributes
        for name, value in self._attributes.items():
            setattr(player, name, value)
        
        # Add common methods
        player.take_damage = Mock(return_value=10)
        player.is_alive = Mock(return_value=self._cpu > 0)
        player.get_position = Mock(return_value=self._position)
        
        return player


class EnemyBuilder:
    """Builder for creating test Enemy objects."""
    
    def __init__(self):
        self._x = 10
        self._y = 10
        self._enemy_type = "scanner"
        self._cpu = 100
        self._state = EnemyState.PATROL
        self._movement_type = EnemyMovement.RANDOM
        self._movement_queue = []
        self._last_target = None
        self._attributes = {}
    
    def of_type(self, enemy_type: str):
        """Set enemy type."""
        self._enemy_type = enemy_type
        return self
    
    def at_position(self, x: int, y: int):
        """Set enemy position."""
        self._x = x
        self._y = y
        return self
    
    def with_cpu(self, cpu: int):
        """Set enemy CPU."""
        self._cpu = cpu
        return self
    
    def in_state(self, state: EnemyState):
        """Set enemy state."""
        self._state = state
        return self
    
    def with_movement(self, movement_type: EnemyMovement):
        """Set movement type."""
        self._movement_type = movement_type
        return self
    
    def with_movement_queue(self, positions: List[Position]):
        """Set movement queue."""
        self._movement_queue = positions.copy()
        return self
    
    def targeting(self, target_position: Position):
        """Set target position."""
        self._last_target = target_position
        return self
    
    def hostile(self):
        """Make enemy hostile."""
        self._state = EnemyState.HOSTILE
        return self
    
    def alert(self):
        """Make enemy alert."""
        self._state = EnemyState.ALERT
        return self
    
    def disabled(self):
        """Make enemy disabled."""
        self._cpu = 0
        return self
    
    def build(self) -> Mock:
        """Build the Enemy mock object."""
        enemy = Mock()
        enemy.x = self._x
        enemy.y = self._y
        enemy.type = self._enemy_type
        enemy.cpu = self._cpu
        enemy.state = self._state
        enemy.movement_type = self._movement_type
        enemy.movement_queue = self._movement_queue.copy()
        enemy.last_target = self._last_target
        
        # Add common methods
        enemy.get_position = Mock(return_value=Position(self._x, self._y))
        enemy.is_alive = Mock(return_value=self._cpu > 0)
        enemy.can_see_position = Mock(return_value=False)
        
        return enemy


class GameStateBuilder:
    """Builder for creating test game state objects."""
    
    def __init__(self):
        self._level = 1
        self._turn = 0
        self._player = None
        self._enemies = []
        self._game_map = None
        self._message_log = None
        self._attributes = {}
    
    def at_level(self, level: int):
        """Set game level."""
        self._level = level
        return self
    
    def at_turn(self, turn: int):
        """Set turn number."""
        self._turn = turn
        return self
    
    def with_player(self, player):
        """Set player object."""
        self._player = player
        return self
    
    def with_enemies(self, enemies: List):
        """Set enemies list."""
        self._enemies = enemies.copy()
        return self
    
    def with_map(self, game_map):
        """Set game map."""
        self._game_map = game_map
        return self
    
    def with_message_log(self, message_log):
        """Set message log."""
        self._message_log = message_log
        return self
    
    def early_game(self):
        """Set early game state."""
        self._level = 1
        self._turn = 10
        return self
    
    def mid_game(self):
        """Set mid game state."""
        self._level = 3
        self._turn = 150
        return self
    
    def late_game(self):
        """Set late game state."""
        self._level = 5
        self._turn = 300
        return self
    
    def build(self) -> Mock:
        """Build the game state mock object."""
        game = Mock()
        game.level = self._level
        game.turn = self._turn
        game.player = self._player or PlayerBuilder().build()
        game.enemies = self._enemies
        game.game_map = self._game_map or Mock()
        game.message_log = self._message_log or Mock()
        
        # Add default attributes
        game.game_over = False
        game.show_inventory = False
        game.show_help = False
        game.targeting_mode = False
        
        return game


class ScenarioBuilder:
    """Builder for creating complete test scenarios."""
    
    def __init__(self):
        self._scenario_type = "basic"
        self._player_builder = PlayerBuilder()
        self._enemy_builders = []
        self._game_builder = GameStateBuilder()
    
    def player_vs_single_enemy(self):
        """Create player vs single enemy scenario."""
        self._scenario_type = "player_vs_enemy"
        self._enemy_builders = [EnemyBuilder().hostile().at_position(15, 15)]
        return self
    
    def player_surrounded(self):
        """Create player surrounded by enemies scenario.""" 
        self._scenario_type = "surrounded"
        self._enemy_builders = [
            EnemyBuilder().hostile().at_position(4, 5),
            EnemyBuilder().hostile().at_position(6, 5),
            EnemyBuilder().hostile().at_position(5, 4),
            EnemyBuilder().hostile().at_position(5, 6)
        ]
        return self
    
    def stealth_mission(self):
        """Create stealth scenario with patrolling enemies."""
        self._scenario_type = "stealth"
        self._player_builder.with_low_cpu().with_high_heat()
        self._enemy_builders = [
            EnemyBuilder().in_state(EnemyState.PATROL).at_position(20, 10),
            EnemyBuilder().in_state(EnemyState.PATROL).at_position(30, 15)
        ]
        return self
    
    def boss_fight(self):
        """Create boss fight scenario."""
        self._scenario_type = "boss"
        self._game_builder.late_game()
        self._enemy_builders = [
            EnemyBuilder().of_type("admin").hostile().with_cpu(200).at_position(25, 25)
        ]
        return self
    
    def with_custom_player(self, player_builder: PlayerBuilder):
        """Use custom player builder."""
        self._player_builder = player_builder
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build complete scenario."""
        player = self._player_builder.build()
        enemies = [builder.build() for builder in self._enemy_builders]
        game = self._game_builder.with_player(player).with_enemies(enemies).build()
        
        return {
            "type": self._scenario_type,
            "player": player,
            "enemies": enemies,
            "game": game
        }


# Convenience functions for common patterns
def player() -> PlayerBuilder:
    """Create a new PlayerBuilder."""
    return PlayerBuilder()

def enemy() -> EnemyBuilder:
    """Create a new EnemyBuilder."""
    return EnemyBuilder()

def game_state() -> GameStateBuilder:
    """Create a new GameStateBuilder."""
    return GameStateBuilder()

def scenario() -> ScenarioBuilder:
    """Create a new ScenarioBuilder."""
    return ScenarioBuilder()

# Common pre-built scenarios
@dataclass
class TestScenarios:
    """Collection of pre-built test scenarios."""
    
    @staticmethod
    def player_low_health():
        return player().with_cpu(15).with_high_heat().build()
    
    @staticmethod
    def enemy_hostile_nearby():
        return enemy().hostile().at_position(6, 6).build()
    
    @staticmethod
    def early_game_state():
        return game_state().early_game().build()
    
    @staticmethod
    def combat_scenario():
        return scenario().player_vs_single_enemy().build()
    
    @staticmethod
    def stealth_scenario():
        return scenario().stealth_mission().build()