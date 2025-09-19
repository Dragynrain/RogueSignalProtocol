#!/usr/bin/env python3
"""
Unit tests for game_engine.py - Game loop and state management.
Tests the core game engine, turn processing, and system integration.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from game_engine import GameEngine
from game_entities import Position, EnemyState, EnemyMovement
from game_characters import Player, Enemy
from game_config import GameConfig


class TestGameEngine:
    """Test GameEngine class functionality."""
    
    def test_game_engine_creation_defaults(self):
        """Test game engine creation with default dependencies."""
        with patch('game_engine.SoundManager') as mock_sound_manager:
            with patch('game_engine.GameStateManager') as mock_state_manager:
                with patch('game_engine.GameMap') as mock_game_map:
                    with patch('game_engine.LevelGenerator') as mock_level_gen:
                        with patch('game_engine.EnemyManager') as mock_enemy_manager:
                            with patch('game_engine.InputHandler') as mock_input_handler:
                                with patch.object(GameEngine, '_generate_procedural_level'):

                                    # Mock the level generation call
                                    mock_engine = Mock()
                                    mock_level_gen.return_value.generate_level = Mock()

                                    engine = GameEngine(load_save=False)

                                    # Should have created all required components
                                    assert hasattr(engine, 'game_state')
                                    assert hasattr(engine, 'game_map')
                                    assert hasattr(engine, 'level_generator')
                                    assert hasattr(engine, 'enemy_manager')
                                    assert hasattr(engine, 'sound_manager')
                                    assert hasattr(engine, 'player')
                                    assert hasattr(engine, 'message_log')
                                    assert hasattr(engine, 'turn_processor')
    
    def test_game_engine_creation_with_dependencies(self):
        """Test game engine creation with provided dependencies."""
        # Create mock dependencies
        mock_state_manager = Mock()
        mock_game_map = Mock()
        mock_level_generator = Mock()
        mock_enemy_manager = Mock()
        mock_exploit_system = Mock()
        mock_input_handler = Mock()
        mock_sound_manager = Mock()
        mock_settings = Mock()
        
        with patch.object(mock_sound_manager, 'preload_sounds'):
            with patch.object(mock_level_generator, 'generate_level'):
                with patch.object(GameEngine, '_generate_procedural_level'):
                    engine = GameEngine(
                        game_state_manager=mock_state_manager,
                        game_map=mock_game_map,
                        level_generator=mock_level_generator,
                        enemy_manager=mock_enemy_manager,
                        exploit_system=mock_exploit_system,
                        input_handler=mock_input_handler,
                        sound_manager=mock_sound_manager,
                        settings=mock_settings,
                        load_save=False
                    )
                
                # Should use provided dependencies
                assert engine.game_state == mock_state_manager
                assert engine.game_map == mock_game_map
                assert engine.level_generator == mock_level_generator
                assert engine.enemy_manager == mock_enemy_manager
                assert engine.sound_manager == mock_sound_manager
    
    def test_game_engine_player_initialization(self):
        """Test that player is properly initialized."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                
                assert isinstance(engine.player, Player)
                # Player position depends on level generation
                assert engine.player.position.x >= 2
                assert engine.player.position.y >= 2
                assert engine.player.cpu == 100
                assert engine.player.heat == 0
    
    def test_game_engine_properties(self):
        """Test game engine property accessors."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                
                # Test level property
                engine.game_state.level = 5
                assert engine.level == 5
                
                engine.level = 10
                assert engine.game_state.level == 10
                
                # Test turn property
                engine.game_state.turn = 25
                assert engine.turn == 25
                
                # Test game_over property
                engine.game_state.game_over = True
                assert engine.game_over is True
                
                engine.game_over = False
                assert engine.game_state.game_over is False
                
                # Test admin_spawned property
                engine.game_state.admin_spawned = True
                assert engine.admin_spawned is True
                
                engine.admin_spawned = False
                assert engine.game_state.admin_spawned is False
    
    def test_game_engine_enemy_access(self):
        """Test enemy access through game engine."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                
                # Mock some enemies
                mock_enemy1 = Mock()
                mock_enemy2 = Mock()
                engine.enemy_manager.enemies = [mock_enemy1, mock_enemy2]
                
                # Test enemies property
                assert engine.enemies == [mock_enemy1, mock_enemy2]
    
    def test_get_enemy_at_position(self):
        """Test getting enemy at specific position."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                
                position = Position(10, 10)
                mock_enemy = Mock()
                
                # Mock enemy manager response
                engine.enemy_manager.get_enemy_at_position = Mock(return_value=mock_enemy)
                
                result = engine._get_enemy_at(position)
                assert result == mock_enemy
                engine.enemy_manager.get_enemy_at_position.assert_called_once_with(position)
    
    def test_game_engine_ui_state_initialization(self):
        """Test UI state is properly initialized."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                
                # Test UI state defaults
                assert engine.show_inventory is False
                assert engine.show_help is False
                assert engine.show_gateway_confirmation is False
                assert engine.show_story_fragment is None
                assert engine.show_lore_viewer is False
                assert engine.inventory_selection == 0
                assert engine.lore_viewer_selection == 0
                assert engine.lore_viewer_mode == "list"
    
    def test_game_engine_targeting_system_initialization(self):
        """Test targeting system is properly initialized."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                
                # Test targeting state defaults
                assert engine.targeting_mode is False
                assert engine.targeting_exploit is None
                assert isinstance(engine.cursor_position, Position)
                assert engine.cursor_position.x == 0
                assert engine.cursor_position.y == 0
    
    def test_game_engine_overclocking_system_initialization(self):
        """Test overclocking system is properly initialized."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                
                # Test overclocking state defaults
                assert engine.overclock_confirmation is False
                assert engine.overclock_exploit is None
    
    def test_game_engine_code_system_initialization(self):
        """Test code patch system is properly initialized."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                
                # Test code systems
                assert isinstance(engine.code_hack_effects, dict)
                assert isinstance(engine.discovered_code_effects, dict)
                assert hasattr(engine, 'story_fragment_manager')
    
    @patch('game_engine.SaveGameManager')
    def test_game_engine_load_save_failure(self, mock_save_manager):
        """Test game engine handles save loading failure gracefully."""
        # Mock save loading to fail
        mock_save_manager.load_game.return_value = None
        
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                with patch.object(GameEngine, '_randomize_code_hacks') as mock_randomize:
                    with patch.object(GameEngine, '_generate_procedural_level') as mock_generate:
                        engine = GameEngine(load_save=True)
                        
                        # Should fall back to new game
                        mock_randomize.assert_called_once()
                        mock_generate.assert_called_once()
    
    @patch('game_engine.SaveGameManager')
    def test_game_engine_load_save_success(self, mock_save_manager):
        """Test game engine loads save successfully."""
        # Mock save data
        mock_save_data = {
            'player': {'x': 10, 'y': 15, 'cpu': 80},
            'level': 3,
            'turn': 100
        }
        mock_save_manager.load_game.return_value = mock_save_data
        
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                with patch.object(GameEngine, '_restore_game_state') as mock_restore_game:
                    with patch.object(GameEngine, '_restore_player_state') as mock_restore_player:
                        with patch.object(GameEngine, '_restore_game_effects') as mock_restore_effects:
                            with patch.object(GameEngine, '_sync_code_discovered_status') as mock_sync:
                                with patch.object(GameEngine, '_restore_ui_state') as mock_restore_ui:
                                    engine = GameEngine(load_save=True)
                                    
                                    # Should call all restore methods
                                    mock_restore_game.assert_called_once_with(mock_save_data)
                                    mock_restore_player.assert_called_once_with(mock_save_data['player'])
                                    mock_restore_effects.assert_called_once_with(mock_save_data)
                                    mock_sync.assert_called_once()
                                    mock_restore_ui.assert_called_once_with(mock_save_data)


class TestGameEngineIntegration:
    """Test game engine integration with other systems."""
    
    def test_enemy_manager_message_log_connection(self):
        """Test that enemy manager gets connected to message log."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                
                # Enemy manager should have the message log
                assert engine.enemy_manager.message_log == engine.message_log
    
    def test_turn_processor_initialization(self):
        """Test that turn processor is properly initialized with dependencies."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                
                # Turn processor should have required dependencies
                assert engine.turn_processor.game_state == engine.game_state
                assert engine.turn_processor.message_log == engine.message_log
    
    def test_sound_manager_preload(self):
        """Test that sound manager preloads sounds on initialization."""
        mock_sound_manager = Mock()
        
        with patch('game_engine.LevelGenerator') as mock_level_gen:
            mock_level_gen.return_value.generate_level = Mock()
            
            engine = GameEngine(
                sound_manager=mock_sound_manager,
                load_save=False
            )
            
            # Should have called preload_sounds
            mock_sound_manager.preload_sounds.assert_called_once()
    
    def test_input_handler_late_initialization(self):
        """Test that input handler is initialized after engine setup."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                with patch('game_engine.InputHandler') as mock_input_handler_class:
                    engine = GameEngine(load_save=False)
                    
                    # InputHandler should be created with engine reference
                    mock_input_handler_class.assert_called_once_with(engine)
                    assert engine.input_handler == mock_input_handler_class.return_value
    
    def test_provided_input_handler_not_overridden(self):
        """Test that provided input handler is not overridden."""
        mock_input_handler = Mock()
        
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(
                    input_handler=mock_input_handler,
                    load_save=False
                )
                
                # Should use provided input handler
                assert engine.input_handler == mock_input_handler


class TestGameEngineState:
    """Test game engine state management."""
    
    def test_level_property_access(self):
        """Test level property getter and setter."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                
                # Test getter
                engine.game_state.level = 5
                assert engine.level == 5
                
                # Test setter
                engine.level = 10
                assert engine.game_state.level == 10
    
    def test_turn_property_access(self):
        """Test turn property is read-only."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                
                # Test getter
                engine.game_state.turn = 50
                assert engine.turn == 50
                
                # Turn property should exist and be readable
                assert hasattr(engine, 'turn')
    
    def test_game_over_property_access(self):
        """Test game_over property getter and setter."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                
                # Test getter
                engine.game_state.game_over = True
                assert engine.game_over is True
                
                # Test setter
                engine.game_over = False
                assert engine.game_state.game_over is False
    
    def test_admin_spawned_property_access(self):
        """Test admin_spawned property getter and setter."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                
                # Test getter
                engine.game_state.admin_spawned = True
                assert engine.admin_spawned is True
                
                # Test setter
                engine.admin_spawned = False
                assert engine.game_state.admin_spawned is False


class TestGameEngineInitializationOrder:
    """Test that game engine components are initialized in correct order."""
    
    def test_initialization_order(self):
        """Test that components are initialized in the correct dependency order."""
        init_order = []
        
        # Mock constructors to track initialization order
        def track_init(name):
            def wrapper(*args, **kwargs):
                init_order.append(name)
                return Mock()
            return wrapper
        
        with patch('game_engine.GameStateManager', side_effect=track_init('GameStateManager')):
            with patch('game_engine.GameMap', side_effect=track_init('GameMap')):
                with patch('game_engine.LevelGenerator', side_effect=track_init('LevelGenerator')):
                    with patch('game_engine.EnemyManager', side_effect=track_init('EnemyManager')):
                        with patch('game_engine.SoundManager', side_effect=track_init('SoundManager')):
                            with patch('game_engine.MessageLog', side_effect=track_init('MessageLog')):
                                with patch('game_engine.TurnProcessor', side_effect=track_init('TurnProcessor')):
                                    with patch('game_engine.InputHandler', side_effect=track_init('InputHandler')):
                                        with patch.object(GameEngine, '_randomize_code_hacks'):
                                            with patch.object(GameEngine, '_generate_procedural_level'):
                                                engine = GameEngine(load_save=False)
        
        # Core dependencies should be initialized before dependent components
        game_state_idx = init_order.index('GameStateManager')
        game_map_idx = init_order.index('GameMap')
        message_log_idx = init_order.index('MessageLog')
        turn_processor_idx = init_order.index('TurnProcessor')
        input_handler_idx = init_order.index('InputHandler')
        
        # Turn processor depends on game state and message log
        assert game_state_idx < turn_processor_idx
        assert message_log_idx < turn_processor_idx
        
        # Input handler should be initialized last (depends on complete engine)
        assert input_handler_idx == len(init_order) - 1


class TestGameEngineErrorHandling:
    """Test game engine error handling."""
    
    def test_save_loading_exception_handling(self):
        """Test that save loading exceptions are handled gracefully."""
        with patch('game_engine.SaveGameManager') as mock_save_manager:
            # Make save loading return None (no save file)
            mock_save_manager.load_game.return_value = None

            with patch('game_engine.SoundManager'):
                with patch('game_engine.LevelGenerator') as mock_level_gen:
                    mock_level_gen.return_value.generate_level = Mock()

                    with patch.object(GameEngine, '_randomize_code_hacks') as mock_randomize:
                        with patch.object(GameEngine, '_generate_procedural_level') as mock_generate:
                            # Should not raise exception, should fall back to new game
                            engine = GameEngine(load_save=True)

                            # Should fall back to new game creation
                            mock_randomize.assert_called_once()
                            mock_generate.assert_called_once()
    
    def test_missing_dependency_fallback(self):
        """Test that missing dependencies fall back to defaults."""
        with patch('game_engine.SoundManager') as mock_sound_manager_class:
            with patch('game_engine.GameStateManager') as mock_state_manager_class:
                with patch('game_engine.GameMap') as mock_game_map_class:
                    with patch('game_engine.LevelGenerator') as mock_level_gen_class:
                        with patch('game_engine.EnemyManager') as mock_enemy_manager_class:
                            
                            # Mock return values
                            mock_sound_manager_class.return_value.preload_sounds = Mock()
                            mock_level_gen_class.return_value.generate_level = Mock()

                            # Mock level generation to avoid complex setup
                            with patch.object(GameEngine, '_generate_procedural_level'):
                                # Create engine with no dependencies provided
                                engine = GameEngine(load_save=False)

                                # Should have called constructors for all default dependencies
                                mock_sound_manager_class.assert_called_once()
                                mock_state_manager_class.assert_called_once()
                                mock_game_map_class.assert_called_once_with(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
                                mock_level_gen_class.assert_called_once()
                                mock_enemy_manager_class.assert_called_once()


class TestGameEngineConfiguration:
    """Test game engine respects configuration."""
    
    def test_map_size_from_config(self):
        """Test that map size is taken from configuration."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.GameMap') as mock_game_map_class:
                with patch('game_engine.LevelGenerator') as mock_level_gen:
                    mock_level_gen.return_value.generate_level = Mock()
                    
                    engine = GameEngine(load_save=False)
                    
                    # Should have created map with config dimensions
                    mock_game_map_class.assert_called_once_with(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
    
    def test_player_initial_position(self):
        """Test that player starts at expected position."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                
                # Player should start at initial position (can be 5,5 or spawn position)
                assert engine.player.position.x >= 2
                assert engine.player.position.y >= 2


class TestGameEngineTurnProcessing:
    """Test game engine turn processing and game loop mechanics."""

    def test_process_turn_basic_flow(self):
        """Test basic turn processing flow."""
        with patch('game_engine.SoundManager') as mock_sound_manager:
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()

                engine = GameEngine(load_save=False)

                # Mock all the methods that get called during turn processing
                with patch.object(engine, '_update_threat_scan') as mock_threat, \
                     patch.object(engine, '_process_special_tiles') as mock_tiles, \
                     patch.object(engine, '_update_enemies') as mock_enemies, \
                     patch.object(engine, '_update_memory_system') as mock_memory, \
                     patch.object(engine, '_check_admin_spawn') as mock_admin, \
                     patch.object(engine.turn_processor, 'process_turn') as mock_turn_proc:

                    engine.process_turn()

                    # Verify all update methods were called
                    mock_turn_proc.assert_called_once_with(engine.player)
                    mock_threat.assert_called_once()
                    mock_tiles.assert_called_once()
                    mock_enemies.assert_called_once()
                    mock_memory.assert_called_once()
                    mock_admin.assert_called_once()

    def test_process_turn_speed_boost_grant(self):
        """Test speed boost moves are granted at start of turn."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()

                engine = GameEngine(load_save=False)
                engine.player.temporary_effects['speed_boost_turns'] = 3
                engine.player.speed_moves_remaining = 0

                with patch.object(engine, '_update_threat_scan'), \
                     patch.object(engine, '_process_special_tiles'), \
                     patch.object(engine, '_update_enemies'), \
                     patch.object(engine, '_update_memory_system'), \
                     patch.object(engine, '_check_admin_spawn'), \
                     patch.object(engine.turn_processor, 'process_turn'):

                    engine.process_turn()

                    # Should grant 1 extra move
                    assert engine.player.speed_moves_remaining == 1

    def test_process_turn_virus_damage_sound(self):
        """Test virus damage triggers appropriate sound effects."""
        with patch('game_engine.SoundManager') as mock_sound_manager:
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()

                engine = GameEngine(load_save=False)
                engine.player.cpu = 100
                engine.player.temporary_effects['virus_turns'] = 2

                # Mock turn processor to simulate CPU damage
                def simulate_virus_damage(player):
                    player.cpu = 80  # Simulate damage

                with patch.object(engine, '_update_threat_scan'), \
                     patch.object(engine, '_process_special_tiles'), \
                     patch.object(engine, '_update_enemies'), \
                     patch.object(engine, '_update_memory_system'), \
                     patch.object(engine, '_check_admin_spawn'), \
                     patch.object(engine.turn_processor, 'process_turn', side_effect=simulate_virus_damage):

                    engine.process_turn()

                    # Should play virus damage sound
                    engine.sound_manager.play_sound.assert_called_with("virus_damage")


class TestGameEnginePlayerMovement:
    """Test game engine player movement and related mechanics."""

    def test_move_player_successful_movement(self):
        """Test successful player movement."""
        with patch('game_engine.SoundManager') as mock_sound_manager:
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()

                engine = GameEngine(load_save=False)

                # Mock successful movement
                with patch.object(engine.player, 'move', return_value=True), \
                     patch.object(engine, '_get_enemy_at', return_value=None), \
                     patch.object(engine, 'maybe_process_turn') as mock_process:

                    engine.move_player(1, 0)

                    # Verify movement attempt and sound
                    engine.player.move.assert_called_once_with(1, 0, engine.game_map)
                    engine.sound_manager.play_sound.assert_called_with("player_move")
                    mock_process.assert_called_once()

    def test_move_player_blocked_movement(self):
        """Test blocked player movement."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()

                engine = GameEngine(load_save=False)

                # Mock blocked movement
                with patch.object(engine.player, 'move', return_value=False), \
                     patch.object(engine, '_get_enemy_at', return_value=None), \
                     patch.object(engine, 'maybe_process_turn') as mock_process:

                    engine.move_player(1, 0)

                    # Verify no turn processing on blocked movement
                    mock_process.assert_not_called()

    def test_move_player_bump_attack(self):
        """Test bump attack when moving into enemy."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()

                engine = GameEngine(load_save=False)
                mock_enemy = Mock()

                with patch.object(engine, '_get_enemy_at', return_value=mock_enemy), \
                     patch.object(engine, '_perform_bump_attack') as mock_attack, \
                     patch.object(engine, 'maybe_process_turn') as mock_process:

                    engine.move_player(1, 0)

                    # Verify bump attack and turn processing
                    mock_attack.assert_called_once_with(mock_enemy)
                    mock_process.assert_called_once()

    def test_targeting_mode_cursor_movement(self):
        """Test cursor movement in targeting mode."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()

                engine = GameEngine(load_save=False)
                engine.targeting_mode = True
                engine.cursor_position = Position(5, 5)

                engine.move_player(1, 1)

                # Should move cursor, not player
                assert engine.cursor_position.x == 6
                assert engine.cursor_position.y == 6

    def test_maybe_process_turn_with_speed_moves(self):
        """Test turn processing skipped when speed moves remaining."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()

                engine = GameEngine(load_save=False)
                engine.player.speed_moves_remaining = 2

                with patch.object(engine, 'process_turn') as mock_process:
                    engine.maybe_process_turn()

                    # Should consume speed move but not process turn
                    assert engine.player.speed_moves_remaining == 1
                    mock_process.assert_not_called()

    def test_maybe_process_turn_without_speed_moves(self):
        """Test turn processing when no speed moves remaining."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()

                engine = GameEngine(load_save=False)
                engine.player.speed_moves_remaining = 0

                with patch.object(engine, 'process_turn') as mock_process:
                    engine.maybe_process_turn()

                    # Should process turn
                    mock_process.assert_called_once()


class TestGameEngineBumpAttack:
    """Test game engine bump attack mechanics."""

    def test_bump_attack_basic_damage(self):
        """Test basic bump attack damage calculation."""
        with patch('game_engine.SoundManager') as mock_sound_manager:
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()

                engine = GameEngine(load_save=False)

                # Create mock enemy
                mock_enemy = Mock()
                mock_enemy.type_data = Mock()
                mock_enemy.type_data.name = "Scanner"
                mock_enemy.type_data.movement = EnemyMovement.STATIC
                mock_enemy.cpu = 100
                mock_enemy.max_cpu = 100
                mock_enemy.patrol_points = None
                mock_enemy.take_damage = Mock(return_value=False)  # Enemy survives

                with patch.object(engine.game_map, 'is_shadow', return_value=False), \
                     patch.object(engine.player, 'is_invisible', return_value=False):

                    engine.player.temporary_effects['speed_boost_turns'] = 0

                    engine._perform_bump_attack(mock_enemy)

                    # Should apply base damage (30)
                    mock_enemy.take_damage.assert_called_once_with(30)
                    engine.sound_manager.play_sound.assert_called_with("player_attack")

    def test_bump_attack_stealth_bonus(self):
        """Test stealth bonus damage from shadows."""
        with patch('game_engine.SoundManager') as mock_sound_manager:
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()

                engine = GameEngine(load_save=False)

                mock_enemy = Mock()
                mock_enemy.type_data = Mock()
                mock_enemy.type_data.name = "Scanner"
                mock_enemy.type_data.movement = EnemyMovement.STATIC
                mock_enemy.patrol_points = None
                mock_enemy.take_damage = Mock(return_value=False)

                with patch.object(engine.game_map, 'is_shadow', return_value=True), \
                     patch.object(engine.player, 'is_invisible', return_value=False):

                    engine.player.temporary_effects['speed_boost_turns'] = 0

                    engine._perform_bump_attack(mock_enemy)

                    # Should apply base + stealth bonus (30 + 10 = 40)
                    mock_enemy.take_damage.assert_called_once_with(40)
                    engine.sound_manager.play_sound.assert_called_with("stealth_attack")


class TestGameEngineEnemySystem:
    """Test game engine enemy management and AI systems."""

    def test_update_enemy_awareness_sees_player(self):
        """Test enemy awareness update when enemy sees player."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()

                engine = GameEngine(load_save=False)

                mock_enemy = Mock()
                mock_enemy.can_see_player = Mock(return_value=True)
                engine.enemy_manager.enemies = [mock_enemy]

                with patch.object(engine, '_handle_enemy_sees_player') as mock_sees:
                    engine._update_enemy_awareness()
                    mock_sees.assert_called_once_with(mock_enemy)

    def test_handle_enemy_sees_player_unaware_to_alert(self):
        """Test enemy transitions from UNAWARE to ALERT when seeing player."""
        with patch('game_engine.SoundManager') as mock_sound_manager:
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()

                engine = GameEngine(load_save=False)

                mock_enemy = Mock()
                mock_enemy.state = EnemyState.UNAWARE
                mock_enemy.type_data = Mock()
                mock_enemy.type_data.name = "Scanner"

                engine._handle_enemy_sees_player(mock_enemy)

                assert mock_enemy.state == EnemyState.ALERT
                assert mock_enemy.alert_timer == 0
                assert mock_enemy.last_seen_player is not None
                engine.sound_manager.play_sound.assert_called_with("enemy_alert")


class TestGameEngineAdminSpawn:
    """Test game engine admin avatar spawning mechanics."""

    def test_check_admin_spawn_triggers(self):
        """Test admin spawn triggers at maximum detection."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()

                engine = GameEngine(load_save=False)
                engine.player.detection = GameConfig.MAX_DETECTION
                engine.admin_spawned = False
                engine.enemy_manager.enemies = []

                with patch.object(engine, '_spawn_admin_avatar') as mock_spawn:
                    engine._check_admin_spawn()
                    mock_spawn.assert_called_once()

    def test_check_admin_spawn_no_trigger_low_detection(self):
        """Test admin doesn't spawn at low detection."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()

                engine = GameEngine(load_save=False)
                engine.player.detection = 50
                engine.admin_spawned = False

                with patch.object(engine, '_spawn_admin_avatar') as mock_spawn:
                    engine._check_admin_spawn()
                    mock_spawn.assert_not_called()


class TestGameEngineLevelProgression:
    """Test game engine level progression and generation."""

    def test_next_level_progression(self):
        """Test progression to next level."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()

                engine = GameEngine(load_save=False)
                engine.level = 1

                with patch.object(engine, '_generate_procedural_level') as mock_gen, \
                     patch.object(engine, 'auto_save') as mock_save:

                    engine.next_level()

                    # Should advance level and generate new level
                    assert engine.level == 2
                    mock_gen.assert_called_once()
                    mock_save.assert_called_once()

    def test_next_level_victory_condition(self):
        """Test victory condition when reaching level 4."""
        with patch('game_engine.SoundManager') as mock_sound_manager:
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()

                engine = GameEngine(load_save=False)
                engine.level = 3

                with patch.object(engine, 'auto_save') as mock_save:
                    engine.next_level()

                    # Should trigger victory
                    assert engine.level == 4
                    assert engine.game_over is True
                    engine.sound_manager.play_music.assert_called_with("victory.ogg", loops=1)
                    mock_save.assert_called_once()


class TestGameEngineAutoSave:
    """Test game engine auto-save functionality."""

    @patch('game_engine.SaveGameManager')
    def test_auto_save_success(self, mock_save_manager):
        """Test successful auto-save operation."""
        mock_save_manager.save_game.return_value = True

        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()

                engine = GameEngine(load_save=False)
                engine.auto_save()

                # Should call save game with engine instance
                mock_save_manager.save_game.assert_called_once_with(engine)

    @patch('game_engine.SaveGameManager')
    def test_auto_save_game_over_skip(self, mock_save_manager):
        """Test auto-save is skipped when game is over."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()

                engine = GameEngine(load_save=False)
                engine.game_over = True

                engine.auto_save()

                # Should not attempt to save when game is over
                mock_save_manager.save_game.assert_not_called()


class TestGameEngineSpecialTiles:
    """Test game engine special tile processing."""

    def test_process_special_tiles_cooling_node(self):
        """Test cooling node reduces player heat."""
        with patch('game_engine.SoundManager') as mock_sound_manager:
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()

                engine = GameEngine(load_save=False)
                engine.player.heat = 50

                with patch.object(engine.game_map, 'is_cooling_node', return_value=True), \
                     patch.object(engine.game_map, 'is_cpu_recovery_node', return_value=False), \
                     patch.object(engine.game_map, 'is_ghost_node', return_value=False):

                    engine._process_special_tiles()

                    # Heat should be reduced
                    assert engine.player.heat == 30  # 50 - 20

    def test_process_special_tiles_cpu_recovery_node(self):
        """Test CPU recovery node restores player CPU."""
        with patch('game_engine.SoundManager') as mock_sound_manager:
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()

                engine = GameEngine(load_save=False)
                engine.player.cpu = 80
                engine.player.max_cpu = 100

                with patch.object(engine.game_map, 'is_cooling_node', return_value=False), \
                     patch.object(engine.game_map, 'is_cpu_recovery_node', return_value=True), \
                     patch.object(engine.game_map, 'is_ghost_node', return_value=False):

                    engine._process_special_tiles()

                    # CPU should be increased by recovery amount
                    from game_config import GameBalance
                    expected_cpu = 80 + GameBalance.CPU_RECOVERY_AMOUNT
                    assert engine.player.cpu == min(100, expected_cpu)


class TestGameEngineCodeEffects:
    """Test game engine code hack randomization and effects."""

    def test_randomize_code_hacks(self):
        """Test code hack effects are properly randomized."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()

                engine = GameEngine(load_save=False)

                # Should have 6 color effects
                assert len(engine.code_hack_effects) == 6

                # All expected colors should be present
                expected_colors = {'crimson', 'azure', 'emerald', 'golden', 'violet', 'silver'}
                assert set(engine.code_hack_effects.keys()) == expected_colors

                # Each effect should have (action, description) tuple
                for color, (action, desc) in engine.code_hack_effects.items():
                    assert isinstance(action, str)
                    assert isinstance(desc, str)
                    assert action in ['restore_cpu', 'reduce_heat', 'reduce_detection',
                                    'speed_boost', 'enhanced_vision', 'exploit_efficiency']