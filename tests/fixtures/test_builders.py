"""
Test builders for creating mock game objects and scenarios.
Provides fluent builder pattern for clean test setup.
"""

from unittest.mock import Mock, MagicMock
from game_entities import Position


class TestGameEngineBuilder:
    """Builder for creating test GameEngine instances."""
    
    def __init__(self):
        self._engine = Mock()
        self._setup_default_engine()
    
    def _setup_default_engine(self):
        """Set up default engine behavior."""
        self._engine.player = Mock()
        self._engine.player.position = Position(10, 10)
        self._engine.player.cpu = 100
        self._engine.player.temporary_effects = {'speed_boost_turns': 0}
        self._engine.player.speed_moves_remaining = 0
        
        self._engine.enemy_manager = Mock()
        self._engine.enemy_manager.enemies = []
        
        self._engine.targeting_mode = False
        self._engine.game_over = False
        
        # Mock methods
        self._engine.move_player = Mock(return_value=True)
        self._engine.process_enemy_turns = Mock(return_value=True)
        self._engine.render_game = Mock(return_value=True)
        self._engine.save_game = Mock(return_value=True)
        self._engine.handle_input = Mock(return_value=True)
        
    def with_mocked_dependencies(self):
        """Add mocked dependencies to the engine."""
        return self
    
    def with_player_at(self, x, y):
        """Set player position."""
        self._engine.player.position = Position(x, y)
        return self
    
    def with_cpu(self, cpu):
        """Set player CPU."""
        self._engine.player.cpu = cpu
        return self
    
    def with_enemies(self, enemies):
        """Set enemies list."""
        self._engine.enemy_manager.enemies = enemies
        return self
    
    def build(self):
        """Build and return the engine."""
        return self._engine


class TestPlayerBuilder:
    """Builder for creating test Player instances."""
    
    def __init__(self):
        self._player = Mock()
        self._setup_default_player()
    
    def _setup_default_player(self):
        """Set up default player behavior."""
        self._player.position = Position(10, 10)
        self._player.cpu = 100
        self._player.max_cpu = 100
        self._player.inventory = Mock()
        self._player.inventory.items = []
        self._player.cpu_upgrades = []
        self._player.temporary_effects = {'speed_boost_turns': 0}
        self._player.speed_moves_remaining = 0
        
    def at_position(self, x, y):
        """Set player position."""
        self._player.position = Position(x, y)
        return self
    
    def with_cpu(self, cpu):
        """Set player CPU."""
        self._player.cpu = cpu
        return self
    
    def with_max_cpu(self, max_cpu):
        """Set player max CPU."""
        self._player.max_cpu = max_cpu
        return self
    
    def with_inventory_items(self, items):
        """Set inventory items."""
        self._player.inventory.items = items
        return self
    
    def build(self):
        """Build and return the player."""
        return self._player


class TestEnemyBuilder:
    """Builder for creating test Enemy instances."""
    
    def __init__(self):
        self._enemy = Mock()
        self._setup_default_enemy()
    
    def _setup_default_enemy(self):
        """Set up default enemy behavior."""
        self._enemy.position = Position(15, 15)
        self._enemy.cpu = 50
        self._enemy.max_cpu = 50
        self._enemy.alert_level = "unaware"
        self._enemy.movement_type = "RANDOM"
        self._enemy.vision_range = 5
        self._enemy.movement_queue = []
        self._enemy.last_known_player_position = None
        self._enemy.calculate_path_to = Mock(return_value=[])
        
    def at_position(self, x, y):
        """Set enemy position."""
        self._enemy.position = Position(x, y)
        return self
    
    def with_cpu(self, cpu):
        """Set enemy CPU."""
        self._enemy.cpu = cpu
        return self
    
    def hostile(self):
        """Make enemy hostile."""
        self._enemy.alert_level = "hostile"
        return self
    
    def unaware(self):
        """Make enemy unaware."""
        self._enemy.alert_level = "unaware"
        return self
    
    def with_movement_type(self, movement_type):
        """Set movement type."""
        self._enemy.movement_type = movement_type
        return self
    
    def with_vision_range(self, vision_range):
        """Set vision range."""
        self._enemy.vision_range = vision_range
        return self
    
    def with_movement_queue(self, movement_queue):
        """Set movement queue."""
        self._enemy.movement_queue = movement_queue
        return self
    
    def tracking_player_at(self, x, y):
        """Set enemy to track player at position."""
        self._enemy.last_known_player_position = Position(x, y)
        self._enemy.alert_level = "tracking"
        return self
    
    def build(self):
        """Build and return the enemy."""
        return self._enemy


class TestScenarioBuilder:
    """Builder for creating test scenarios with multiple components."""
    
    def __init__(self):
        self._scenario = {
            'engine': None,
            'player': None,
            'enemies': [],
            'level': None
        }
    
    def with_engine(self, engine_builder=None):
        """Add engine to scenario."""
        if engine_builder is None:
            engine_builder = TestGameEngineBuilder()
        self._scenario['engine'] = engine_builder.build()
        return self
    
    def with_player(self, player_builder=None):
        """Add player to scenario."""
        if player_builder is None:
            player_builder = TestPlayerBuilder()
        self._scenario['player'] = player_builder.build()
        return self
    
    def with_enemies(self, enemy_builders):
        """Add enemies to scenario."""
        self._scenario['enemies'] = [builder.build() for builder in enemy_builders]
        return self
    
    def with_level(self, level_mock):
        """Add level to scenario."""
        self._scenario['level'] = level_mock
        return self
    
    def build(self):
        """Build and return the scenario."""
        return self._scenario


# Convenience functions for quick test setup
def player():
    """Quick player builder."""
    return TestPlayerBuilder()

def enemy():
    """Quick enemy builder."""
    return TestEnemyBuilder()

def engine():
    """Quick engine builder."""
    return TestGameEngineBuilder()

def scenario():
    """Quick scenario builder."""
    return TestScenarioBuilder()