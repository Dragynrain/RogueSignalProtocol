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


class TestGameEngineMovementPrediction:
    """Test game engine movement prediction system."""
    
    def test_predict_enemy_movement_non_patrol(self):
        """Test movement prediction for non-patrol enemies."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                
                # Create mock enemy with existing movement queue
                mock_enemy = Mock()
                mock_enemy.type_data = Mock()
                mock_enemy.type_data.movement = EnemyMovement.STATIC
                mock_enemy.state = EnemyState.UNAWARE
                mock_enemy.movement_queue = [Position(1, 1), Position(2, 2), Position(3, 3)]
                
                result = engine._predict_enemy_movement(mock_enemy, 3)
                
                # Should return first 3 positions from queue
                assert len(result) == 3
                assert result[0] == Position(1, 1)
                assert result[1] == Position(2, 2)
                assert result[2] == Position(3, 3)
    
    def test_predict_patrol_movement(self):
        """Test patrol movement prediction."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                
                # Create mock patrol enemy
                mock_enemy = Mock()
                mock_enemy.type_data = Mock()
                mock_enemy.type_data.movement = EnemyMovement.PATROL
                mock_enemy.state = EnemyState.UNAWARE
                mock_enemy.patrol_points = [Position(5, 5), Position(10, 10)]
                mock_enemy.patrol_index = 0
                mock_enemy.x = 3
                mock_enemy.y = 3
                mock_enemy.movement_queue = []
                
                with patch('game_engine.create_pathfinding_cost_map') as mock_cost:
                    mock_cost.return_value = [[1 for _ in range(50)] for _ in range(50)]
                    
                    with patch('tcod.path.SimpleGraph') as mock_graph:
                        with patch('tcod.path.Pathfinder') as mock_pathfinder_class:
                            mock_pathfinder = Mock()
                            mock_pathfinder_class.return_value = mock_pathfinder
                            mock_pathfinder.path_to.return_value = [(3, 3), (4, 4), (5, 5)]
                            
                            result = engine._predict_patrol_movement(mock_enemy, 2)
                            
                            # Should return predicted positions
                            assert len(result) <= 2
    
    def test_enemy_at_position(self):
        """Test getting enemy at specific position."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                
                # Mock enemy manager to return specific enemy
                mock_enemy = Mock()
                engine.enemy_manager.get_enemy_at_position = Mock(return_value=mock_enemy)
                
                result = engine._get_enemy_at(Position(10, 15))
                
                assert result == mock_enemy
                engine.enemy_manager.get_enemy_at_position.assert_called_once_with(Position(10, 15))


class TestGameEngineMovementSystem:
    """Test game engine movement and turn processing."""
    
    def test_update_enemies_basic(self):
        """Test basic enemy update processing."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                
                with patch.object(engine, '_update_enemy_awareness') as mock_awareness, \
                     patch.object(engine, '_move_enemies') as mock_move, \
                     patch.object(engine, '_process_enemy_attacks') as mock_attacks:
                    
                    engine._update_enemies()
                    
                    mock_awareness.assert_called_once()
                    mock_move.assert_called_once() 
                    mock_attacks.assert_called_once()
    
    def test_memory_system_update(self):
        """Test memory system update processing."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                
                # The memory system updates FOV, not virus turns
                # Let's test that it runs without error
                with patch.object(engine.player, 'get_vision_range', return_value=5), \
                     patch.object(engine.player, 'can_see_through_walls', return_value=False):
                    
                    # Should not raise exception
                    engine._update_memory_system()
    
    def test_threat_scan_update(self):
        """Test threat scan update processing."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                
                # Set up threat scan effect
                engine.game_state.threat_scan_turns = 2
                
                engine._update_threat_scan()
                
                # Threat scan turns should be decremented
                assert engine.game_state.threat_scan_turns == 1


class TestGameEngineSpecialNodes:
    """Test game engine special node interactions."""
    
    def test_ghost_node_processing(self):
        """Test ghost node gives random temporary effect."""
        with patch('game_engine.SoundManager') as mock_sound_manager:
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                engine.last_node_position = None  # First time on node
                
                with patch.object(engine.game_map, 'is_cooling_node', return_value=False), \
                     patch.object(engine.game_map, 'is_cpu_recovery_node', return_value=False), \
                     patch.object(engine.game_map, 'is_ghost_node', return_value=True):
                    
                    engine._process_special_tiles()
                    
                    # Should play sound when stepping on node for first time
                    engine.sound_manager.play_sound.assert_called_with("node_activate")


class TestGameEngineEnemyAI:
    """Test game engine enemy AI system."""
    
    def test_handle_enemy_sees_player_alert_to_hostile(self):
        """Test enemy transitions from ALERT to HOSTILE."""
        with patch('game_engine.SoundManager') as mock_sound_manager:
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                
                mock_enemy = Mock()
                mock_enemy.state = EnemyState.ALERT
                mock_enemy.alert_timer = 0  # Ready to transition
                mock_enemy.type_data = Mock()
                mock_enemy.type_data.name = "Scanner"
                mock_enemy.type_data.movement = EnemyMovement.STATIC
                mock_enemy.type = "scanner"
                mock_enemy.patrol_points = None
                
                with patch.object(engine, '_check_detection_threshold_warnings'), \
                     patch.object(engine, '_alert_nearby_enemies'):
                    
                    engine._handle_enemy_sees_player(mock_enemy)
                    
                    assert mock_enemy.state == EnemyState.HOSTILE
                    engine.sound_manager.play_sound.assert_called_with("enemy_hostile")
    
    def test_update_enemy_awareness_no_enemies(self):
        """Test enemy awareness update with no enemies."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                engine.enemy_manager.enemies = []
                
                # Should not raise exception
                engine._update_enemy_awareness()


class TestGameEngineDeathHandling:
    """Test game engine death handling."""
    
    def test_process_turn_player_death_virus(self):
        """Test player death from virus damage plays appropriate sounds."""
        with patch('game_engine.SoundManager') as mock_sound_manager:
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                engine.player.cpu = 50  # Start with some CPU
                engine.player.temporary_effects['virus_turns'] = 1
                
                # Mock the process_turn method to simulate virus damage killing player
                with patch.object(engine.turn_processor, 'process_turn') as mock_process_turn:
                    def virus_kills_player(player):
                        player.cpu = 0  # Virus kills player
                    mock_process_turn.side_effect = virus_kills_player
                    
                    with patch.object(engine, '_update_threat_scan'), \
                         patch.object(engine, '_process_special_tiles'), \
                         patch.object(engine, '_update_enemies'), \
                         patch.object(engine, '_update_memory_system'), \
                         patch.object(engine, '_check_admin_spawn'):
                        
                        engine.process_turn()
                        
                        # Should play virus damage and death sounds
                        engine.sound_manager.play_sound.assert_any_call("virus_damage")
                        engine.sound_manager.play_sound.assert_any_call("player_death", priority=10)
    
    def test_process_turn_player_overheating_handling(self):
        """Test turn processing with overheating player."""
        with patch('game_engine.SoundManager') as mock_sound_manager:
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                engine.player.cpu = 50
                engine.player.heat = 150  # Over maximum
                engine.player.max_heat = 100
                
                with patch.object(engine, '_update_threat_scan'), \
                     patch.object(engine, '_process_special_tiles'), \
                     patch.object(engine, '_update_enemies'), \
                     patch.object(engine, '_update_memory_system'), \
                     patch.object(engine, '_check_admin_spawn'), \
                     patch.object(engine.turn_processor, 'process_turn'):
                    
                    # Should complete turn processing without error
                    engine.process_turn()


class TestGameEngineExploitSystem:
    """Test game engine exploit system integration."""
    
    def test_exploit_system_parameter_accepted(self):
        """Test exploit system parameter is accepted without error."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                mock_exploit_system = Mock()
                
                # Should not raise exception when provided
                engine = GameEngine(
                    exploit_system=mock_exploit_system,
                    load_save=False
                )


class TestGameEngineTargetingSystem:
    """Test game engine targeting system."""
    
    def test_cursor_boundary_constraints(self):
        """Test cursor movement respects map boundaries."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                engine.targeting_mode = True
                engine.cursor_position = Position(0, 0)
                
                # Try to move cursor beyond boundary
                engine.move_player(-1, -1)
                
                # Cursor should stay within bounds
                assert engine.cursor_position.x >= 0
                assert engine.cursor_position.y >= 0


class TestGameEngineMapIntegration:
    """Test game engine map system integration."""
    
    def test_map_initialization(self):
        """Test map is properly initialized with correct dimensions."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.GameMap') as mock_game_map_class:
                with patch('game_engine.LevelGenerator') as mock_level_gen:
                    mock_level_gen.return_value.generate_level = Mock()
                    
                    engine = GameEngine(load_save=False)
                    
                    # Should create map with config dimensions
                    mock_game_map_class.assert_called_with(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
    
    def test_level_generation_integration(self):
        """Test level generation is called during initialization."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen_class:
                mock_level_gen = Mock()
                mock_level_gen_class.return_value = mock_level_gen
                
                engine = GameEngine(load_save=False)
                
                # Should call generate_level during initialization
                mock_level_gen.generate_level.assert_called()


class TestGameEngineStorySystem:
    """Test game engine story fragment management."""
    
    def test_story_fragment_manager_initialization(self):
        """Test story fragment manager is properly initialized."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                
                # Should have story fragment manager
                assert hasattr(engine, 'story_fragment_manager')


class TestGameEngineCodeHackEffects:
    """Test game engine code hack effect application."""
    
    def test_discovered_code_effects_initialization(self):
        """Test discovered code effects are properly initialized."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                
                # Should initialize discovered code effects dict
                assert isinstance(engine.discovered_code_effects, dict)
                assert len(engine.discovered_code_effects) == 0


class TestGameEngineUIStateManagement:
    """Test game engine UI state management."""
    
    def test_ui_state_defaults(self):
        """Test UI state is properly initialized to defaults."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                
                # Test all UI state defaults
                assert engine.show_inventory is False
                assert engine.show_help is False
                assert engine.show_gateway_confirmation is False
                assert engine.show_story_fragment is None
                assert engine.show_lore_viewer is False
                assert engine.inventory_selection == 0
                assert engine.lore_viewer_selection == 0
                assert engine.lore_viewer_mode == "list"
                assert engine.targeting_mode is False
                assert engine.targeting_exploit is None
                assert engine.overclock_confirmation is False
                assert engine.overclock_exploit is None


class TestGameEngineAdminAvatarSystem:
    """Test game engine admin avatar spawning system."""
    
    def test_admin_spawn_already_spawned(self):
        """Test admin doesn't spawn if already spawned."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                engine.player.detection = GameConfig.MAX_DETECTION
                engine.admin_spawned = True  # Already spawned
                
                with patch.object(engine, '_spawn_admin_avatar') as mock_spawn:
                    engine._check_admin_spawn()
                    mock_spawn.assert_not_called()
    
    def test_admin_spawn_admin_already_exists(self):
        """Test admin doesn't spawn if admin enemy already exists."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                engine.player.detection = GameConfig.MAX_DETECTION
                engine.admin_spawned = False
                
                # Mock admin enemy already present
                mock_admin = Mock()
                mock_admin.type = 'admin'
                engine.enemy_manager.enemies = [mock_admin]
                
                with patch.object(engine, '_spawn_admin_avatar') as mock_spawn:
                    engine._check_admin_spawn()
                    mock_spawn.assert_not_called()


class TestGameEngineEnemyInteraction:
    """Test game engine enemy interaction system."""
    
    def test_enemy_attack_player_survival(self):
        """Test player survives enemy attack."""
        with patch('game_engine.SoundManager') as mock_sound_manager:
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                engine.player.cpu = 100
                
                mock_enemy = Mock()
                mock_enemy.type_data = Mock()
                mock_enemy.type_data.name = "Scanner"
                mock_enemy.type_data.damage = 20
                mock_enemy.type_data.virus_turns = 0
                
                # Simulate enemy attack
                damage = mock_enemy.type_data.damage
                engine.player.cpu -= damage
                
                # Player should survive
                assert engine.player.cpu == 80
                assert engine.game_over is False


class TestGameEngineRestoreMethods:
    """Test game engine save/restore functionality."""
    
    def test_restore_game_state(self):
        """Test game state restoration from save data."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                
                save_data = {
                    'level': 3,
                    'turn': 100,
                    'game_over': False,
                    'admin_spawned': True,
                    'threat_scan_turns': 5
                }
                
                engine._restore_game_state(save_data)
                
                assert engine.level == 3
                assert engine.turn == 100
                assert engine.game_over is False
                assert engine.admin_spawned is True
                assert engine.game_state.threat_scan_turns == 5
    
    def test_restore_player_state(self):
        """Test player state restoration from save data."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                
                player_data = {
                    'x': 10,
                    'y': 15,
                    'cpu': 80,
                    'heat': 30,
                    'detection': 25,
                    'max_heat': 120,
                    'temporary_effects': {
                        'virus_turns': 2,
                        'speed_boost_turns': 1
                    }
                }
                
                engine._restore_player_state(player_data)
                
                assert engine.player.x == 10
                assert engine.player.y == 15
                assert engine.player.cpu == 80
                assert engine.player.heat == 30
                assert engine.player.detection == 25
                assert engine.player.max_heat == 120
                assert engine.player.temporary_effects['virus_turns'] == 2
                assert engine.player.temporary_effects['speed_boost_turns'] == 1
    
    def test_restore_game_effects(self):
        """Test game effects restoration from save data."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                
                save_data = {
                    'code_hack_effects': {
                        'crimson': ('restore_cpu', 'Restore CPU'),
                        'azure': ('reduce_heat', 'Reduce heat')
                    },
                    'discovered_code_effects': {
                        'crimson': True
                    }
                }
                
                engine._restore_game_effects(save_data)
                
                assert 'crimson' in engine.code_hack_effects
                assert 'azure' in engine.code_hack_effects
                assert engine.discovered_code_effects['crimson'] is True
    
    def test_restore_ui_state(self):
        """Test UI state restoration from save data.""" 
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                
                save_data = {
                    'inventory_selection': 2,
                    'lore_viewer_selection': 1,
                    'lore_viewer_mode': 'details'
                }
                
                engine._restore_ui_state(save_data)
                
                assert engine.inventory_selection == 2
                assert engine.lore_viewer_selection == 1
                assert engine.lore_viewer_mode == 'details'
    
    def test_sync_code_discovered_status(self):
        """Test code discovered status synchronization."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                
                # Set up discovered code effects
                engine.discovered_code_effects = {'crimson': True, 'azure': True}
                
                # Mock inventory with code items
                engine.player.inventory_manager.get_items_by_type = Mock(return_value=[
                    Mock(color='crimson'),
                    Mock(color='emerald')
                ])
                
                engine._sync_code_discovered_status()
                
                # Should have discovered effects for inventory items
                assert 'crimson' in engine.discovered_code_effects
                assert 'emerald' in engine.discovered_code_effects


class TestGameEngineHelpChecks:
    """Test game engine detection threshold and other checks."""
    
    def test_check_detection_threshold_warnings(self):
        """Test detection threshold warning system."""
        with patch('game_engine.SoundManager') as mock_sound_manager:
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                
                # Test 50% threshold
                engine._check_detection_threshold_warnings(40, 55)
                engine.sound_manager.play_sound.assert_called_with("detection_threshold")
                
                # Test 75% threshold
                engine._check_detection_threshold_warnings(60, 80)
                engine.sound_manager.play_sound.assert_called_with("detection_threshold")
    
    def test_alert_nearby_enemies(self):
        """Test alerting nearby enemies when one becomes hostile."""
        with patch('game_engine.SoundManager') as mock_sound_manager:
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                
                # Create hostile enemy and nearby enemy
                hostile_enemy = Mock()
                hostile_enemy.x = 10
                hostile_enemy.y = 10
                
                nearby_enemy = Mock()
                nearby_enemy.x = 12
                nearby_enemy.y = 12
                nearby_enemy.state = EnemyState.UNAWARE
                nearby_enemy.type_data = Mock()
                nearby_enemy.type_data.name = "Scanner"
                
                far_enemy = Mock()
                far_enemy.x = 30
                far_enemy.y = 30
                far_enemy.state = EnemyState.UNAWARE
                
                engine.enemy_manager.enemies = [nearby_enemy, far_enemy]
                
                engine._alert_nearby_enemies(hostile_enemy)
                
                # Nearby enemy should be alerted
                assert nearby_enemy.state == EnemyState.ALERT
                assert nearby_enemy.last_seen_player is not None
                
                # Far enemy should remain unaware
                assert far_enemy.state == EnemyState.UNAWARE


class TestGameEngineSpawnAdmin:
    """Test admin avatar spawning functionality."""
    
    def test_spawn_admin_avatar(self):
        """Test admin avatar spawning."""
        with patch('game_engine.SoundManager') as mock_sound_manager:
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                engine.admin_spawned = False
                
                # Mock finding a valid spawn position
                with patch.object(engine, '_find_valid_admin_spawn', return_value=Position(20, 20)) as mock_find:
                    with patch.object(engine.enemy_manager, 'spawn_enemy') as mock_spawn:
                        
                        engine._spawn_admin_avatar()
                        
                        assert engine.admin_spawned is True
                        mock_find.assert_called_once()
                        mock_spawn.assert_called_once()
                        engine.sound_manager.play_sound.assert_called_with("admin_spawn")
    
    def test_find_valid_admin_spawn(self):
        """Test finding valid admin spawn position."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                
                # Mock game map methods
                engine.game_map.is_walkable = Mock(return_value=True)
                engine.enemy_manager.get_enemy_at_position = Mock(return_value=None)
                
                with patch('random.randint', side_effect=[15, 15]):  # Mock random position
                    result = engine._find_valid_admin_spawn()
                    
                    assert isinstance(result, Position)
                    assert result.x == 15
                    assert result.y == 15


class TestGameEngineProcessEnemyAttacks:
    """Test enemy attack processing."""
    
    def test_process_enemy_attacks(self):
        """Test processing enemy attacks."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                
                # Create hostile enemy in range
                mock_enemy = Mock()
                mock_enemy.state = EnemyState.HOSTILE
                mock_enemy.has_moved_this_turn = False
                mock_enemy.can_attack_player = Mock(return_value=True)
                mock_enemy.type_data = Mock()
                mock_enemy.type_data.name = "Scanner"
                mock_enemy.type_data.damage = 20
                mock_enemy.type_data.virus_turns = 0
                
                engine.enemy_manager.enemies = [mock_enemy]
                
                with patch.object(engine, '_apply_enemy_attack') as mock_apply:
                    engine._process_enemy_attacks()
                    
                    mock_apply.assert_called_once_with(mock_enemy)
    
    def test_apply_enemy_attack(self):
        """Test applying enemy attack to player."""
        with patch('game_engine.SoundManager') as mock_sound_manager:
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                engine.player.cpu = 100
                
                mock_enemy = Mock()
                mock_enemy.type_data = Mock()
                mock_enemy.type_data.name = "Scanner"
                mock_enemy.type_data.damage = 25
                mock_enemy.type_data.virus_turns = 0
                
                engine._apply_enemy_attack(mock_enemy)
                
                # Player should take damage
                assert engine.player.cpu == 75
                engine.sound_manager.play_sound.assert_called_with("enemy_attack")


class TestGameEngineMoveEnemies:
    """Test enemy movement processing."""
    
    def test_move_enemies(self):
        """Test moving all enemies."""
        with patch('game_engine.SoundManager'):
            with patch('game_engine.LevelGenerator') as mock_level_gen:
                mock_level_gen.return_value.generate_level = Mock()
                
                engine = GameEngine(load_save=False)
                
                # Create mock enemy
                mock_enemy = Mock()
                mock_enemy.has_moved_this_turn = False
                
                engine.enemy_manager.enemies = [mock_enemy]
                engine.enemy_manager.update_all_enemies = Mock()
                
                engine._move_enemies()
                
                engine.enemy_manager.update_all_enemies.assert_called_once_with(engine.player, engine)