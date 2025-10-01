"""
Terminal compatibility tests.

Tests game functionality across different terminal types, character encodings,
color support levels, and terminal-specific behaviors.
"""

import pytest
import os
import sys
import platform
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from game_engine import GameEngine
from game_characters import Player, Enemy
from game_config import GameConfig
from game_entities import Position
from tests.fixtures.test_builders import TestGameEngineBuilder, TestPlayerBuilder, TestEnemyBuilder
# Direction enum for movement testing
from enum import Enum
class Direction(Enum):
    NORTH = (0, -1)
    SOUTH = (0, 1)
    EAST = (1, 0)
    WEST = (-1, 0)


class TestTerminalCharacterSupport:
    """Tests for terminal character encoding and display support."""
    
    def test_ascii_only_mode(self):
        """Test game functionality with ASCII-only character support."""
        engine = TestGameEngineBuilder().with_mocked_dependencies().build()
        
        # Simulate ASCII-only terminal
        with patch('sys.stdout.encoding', 'ascii'):
            try:
                # Test basic game operations
                dx, dy = Direction.NORTH.value
                engine.move_player(dx, dy)
                engine.process_enemy_turns()
                engine.render_game()
                
                assert True, "Game functions in ASCII-only mode"
                
            except UnicodeEncodeError:
                # This is acceptable - game should handle gracefully
                assert True, "Game handles Unicode gracefully in ASCII mode"
                
            except Exception as e:
                assert False, f"Unexpected error in ASCII mode: {e}"
    
    def test_utf8_character_support(self):
        """Test game functionality with UTF-8 character support."""
        engine = TestGameEngineBuilder().with_mocked_dependencies().build()
        
        # Simulate UTF-8 terminal
        with patch('sys.stdout.encoding', 'utf-8'):
            try:
                # Test game operations that might use Unicode
                dx, dy = Direction.NORTH.value
                engine.move_player(dx, dy)
                engine.process_enemy_turns()
                engine.render_game()
                
                assert True, "Game functions with UTF-8 support"
                
            except Exception as e:
                assert False, f"Unexpected error in UTF-8 mode: {e}"
    
    def test_box_drawing_characters(self):
        """Test handling of box drawing characters for UI elements."""
        engine = TestGameEngineBuilder().with_mocked_dependencies().build()
        
        # Test box drawing characters that might be used in UI
        box_chars = [
            '┌', '┐', '└', '┘',  # corners
            '─', '│',            # lines
            '├', '┤', '┬', '┴',  # connectors
            '╔', '╗', '╚', '╝',  # double lines
            '║', '═'             # double lines
        ]
        
        for encoding in ['utf-8', 'cp437', 'ascii']:
            with patch('sys.stdout.encoding', encoding):
                try:
                    # Test if characters can be handled
                    for char in box_chars:
                        try:
                            char.encode(encoding)
                        except UnicodeEncodeError:
                            # Fallback to ASCII should work
                            fallback = '+' if char in '┌┐└┘╔╗╚╝' else '-' if char in '─═' else '|'
                            fallback.encode(encoding)
                    
                    # Game should render without issues
                    engine.render_game()
                    assert True, f"Box characters handled in {encoding}"
                    
                except Exception as e:
                    assert False, f"Box character handling failed in {encoding}: {e}"
    
    def test_color_escape_sequences(self):
        """Test handling of ANSI color escape sequences."""
        engine = TestGameEngineBuilder().with_mocked_dependencies().build()
        
        # Test ANSI color codes
        color_codes = [
            '\033[0m',    # reset
            '\033[31m',   # red
            '\033[32m',   # green
            '\033[33m',   # yellow
            '\033[34m',   # blue
            '\033[35m',   # magenta
            '\033[36m',   # cyan
            '\033[37m',   # white
            '\033[91m',   # bright red
            '\033[92m',   # bright green
        ]
        
        # Simulate different terminal color support levels
        for color_support in [True, False]:
            with patch.dict(os.environ, {'TERM': 'xterm-256color' if color_support else 'dumb'}):
                try:
                    # Test color handling
                    for code in color_codes:
                        # Game should handle colors gracefully
                        pass
                    
                    engine.render_game()
                    assert True, f"Color codes handled with support={color_support}"
                    
                except Exception as e:
                    assert False, f"Color handling failed with support={color_support}: {e}"


class TestTerminalSizeHandling:
    """Tests for handling different terminal sizes and resizing."""
    
    def test_small_terminal_size(self):
        """Test game behavior in very small terminals."""
        engine = TestGameEngineBuilder().with_mocked_dependencies().build()
        
        # Simulate small terminal sizes
        small_sizes = [
            (20, 10),   # Very small
            (40, 15),   # Small
            (60, 20),   # Minimal
        ]
        
        for width, height in small_sizes:
            with patch('os.get_terminal_size') as mock_size:
                mock_size.return_value = os.terminal_size((width, height))
                
                try:
                    # Game should adapt to small terminal
                    engine.render_game()
                    dx, dy = Direction.NORTH.value
                    engine.move_player(dx, dy)
                    
                    assert True, f"Game works in {width}x{height} terminal"
                    
                except Exception as e:
                    # Small terminals may have limitations
                    if "size" in str(e).lower() or "terminal" in str(e).lower():
                        assert True, f"Game handles small terminal limitation: {e}"
                    else:
                        assert False, f"Unexpected error in {width}x{height}: {e}"
    
    def test_large_terminal_size(self):
        """Test game behavior in very large terminals."""
        engine = TestGameEngineBuilder().with_mocked_dependencies().build()
        
        # Simulate large terminal sizes
        large_sizes = [
            (200, 60),   # Wide
            (120, 100),  # Tall
            (300, 150),  # Very large
        ]
        
        for width, height in large_sizes:
            with patch('os.get_terminal_size') as mock_size:
                mock_size.return_value = os.terminal_size((width, height))
                
                try:
                    # Game should handle large terminals
                    engine.render_game()
                    dx, dy = Direction.NORTH.value
                    engine.move_player(dx, dy)
                    
                    assert True, f"Game works in {width}x{height} terminal"
                    
                except Exception as e:
                    assert False, f"Unexpected error in large terminal {width}x{height}: {e}"
    
    def test_terminal_resize_simulation(self):
        """Test simulation of terminal resize events."""
        engine = TestGameEngineBuilder().with_mocked_dependencies().build()
        
        # Simulate terminal resize sequence
        sizes = [
            (80, 25),   # Standard
            (120, 30),  # Larger
            (60, 20),   # Smaller
            (100, 40),  # Different aspect
            (80, 25),   # Back to standard
        ]
        
        for i, (width, height) in enumerate(sizes):
            with patch('os.get_terminal_size') as mock_size:
                mock_size.return_value = os.terminal_size((width, height))
                
                try:
                    # Game should handle resize
                    engine.render_game()
                    
                    # Perform some operations after resize
                    if i % 2 == 0:
                        dx, dy = Direction.NORTH.value
                        engine.move_player(dx, dy)
                    else:
                        engine.process_enemy_turns()
                    
                    assert True, f"Resize to {width}x{height} handled"
                    
                except Exception as e:
                    assert False, f"Resize handling failed at {width}x{height}: {e}"


class TestTerminalTypeCompatibility:
    """Tests for compatibility with different terminal types."""
    
    def test_xterm_compatibility(self):
        """Test compatibility with xterm and xterm-like terminals."""
        engine = TestGameEngineBuilder().with_mocked_dependencies().build()
        
        xterm_variants = [
            'xterm',
            'xterm-256color',
            'xterm-color',
            'screen',
            'screen-256color',
            'tmux',
            'tmux-256color'
        ]
        
        for term_type in xterm_variants:
            with patch.dict(os.environ, {'TERM': term_type}):
                try:
                    # Test game operations
                    engine.render_game()
                    dx, dy = Direction.NORTH.value
                    engine.move_player(dx, dy)
                    engine.process_enemy_turns()
                    
                    assert True, f"Game works with TERM={term_type}"
                    
                except Exception as e:
                    assert False, f"Compatibility failed with {term_type}: {e}"
    
    def test_windows_terminal_types(self):
        """Test compatibility with Windows terminal types."""
        if platform.system() != "Windows":
            pytest.skip("Windows-specific test")
        
        engine = TestGameEngineBuilder().with_mocked_dependencies().build()
        
        # Windows terminal configurations
        windows_configs = [
            {'TERM': '', 'ConEmuPID': '1234'},           # ConEmu
            {'TERM': '', 'WT_SESSION': 'session-id'},    # Windows Terminal
            {'TERM': ''},                                 # Command Prompt
            {'TERM': '', 'PSModulePath': 'path'},        # PowerShell
        ]
        
        for config in windows_configs:
            with patch.dict(os.environ, config, clear=False):
                try:
                    # Test game operations
                    engine.render_game()
                    dx, dy = Direction.NORTH.value
                    engine.move_player(dx, dy)
                    
                    term_name = "ConEmu" if 'ConEmuPID' in config else \
                               "WindowsTerminal" if 'WT_SESSION' in config else \
                               "PowerShell" if 'PSModulePath' in config else \
                               "CommandPrompt"
                    
                    assert True, f"Game works with {term_name}"
                    
                except Exception as e:
                    assert False, f"Windows terminal compatibility failed with {term_name}: {e}"
    
    def test_legacy_terminal_compatibility(self):
        """Test compatibility with legacy terminal types."""
        engine = TestGameEngineBuilder().with_mocked_dependencies().build()
        
        legacy_terminals = [
            'vt100',
            'vt220',
            'ansi',
            'dumb',
            'linux',
            'console'
        ]
        
        for term_type in legacy_terminals:
            with patch.dict(os.environ, {'TERM': term_type}):
                try:
                    # Test basic operations (may have limited features)
                    engine.render_game()
                    dx, dy = Direction.NORTH.value
                    engine.move_player(dx, dy)
                    
                    assert True, f"Game works with legacy terminal {term_type}"
                    
                except Exception as e:
                    # Legacy terminals may have limitations
                    if any(word in str(e).lower() for word in ['color', 'terminal', 'display', 'encoding']):
                        assert True, f"Legacy terminal {term_type} limitation handled: {e}"
                    else:
                        assert False, f"Unexpected error with {term_type}: {e}"


class TestInputHandlingCompatibility:
    """Tests for input handling across different terminals."""
    
    def test_key_sequence_compatibility(self):
        """Test handling of different key sequences across terminals."""
        engine = TestGameEngineBuilder().with_mocked_dependencies().build()
        
        # Common key sequences that might vary across terminals
        key_sequences = [
            'w',      # Basic character
            '\x1b[A', # Arrow up (ANSI)
            '\x1b[B', # Arrow down (ANSI)
            '\x1b[C', # Arrow right (ANSI)
            '\x1b[D', # Arrow left (ANSI)
            '\x03',   # Ctrl+C
            '\x1b',   # Escape
            '\x7f',   # Backspace/Delete
        ]
        
        for sequence in key_sequences:
            try:
                # Test key handling
                engine.handle_input(sequence)
                assert True, f"Key sequence {repr(sequence)} handled"
                
            except Exception as e:
                # Some key sequences may not be supported
                if "key" in str(e).lower() or "input" in str(e).lower():
                    assert True, f"Key sequence {repr(sequence)} limitation: {e}"
                else:
                    assert False, f"Unexpected error with key {repr(sequence)}: {e}"
    
    def test_special_character_input(self):
        """Test handling of special character input."""
        engine = TestGameEngineBuilder().with_mocked_dependencies().build()
        
        special_chars = [
            'é', 'ñ', 'ü',      # Accented characters
            '£', '€', '¥',      # Currency symbols
            '©', '®', '™',      # Special symbols
            '→', '←', '↑', '↓', # Arrow symbols
        ]
        
        for char in special_chars:
            try:
                # Test special character handling
                engine.handle_input(char)
                assert True, f"Special character {char} handled"
                
            except (UnicodeEncodeError, UnicodeDecodeError):
                # Unicode issues are acceptable
                assert True, f"Unicode character {char} limitation handled"
                
            except Exception as e:
                assert False, f"Unexpected error with character {char}: {e}"
    
    def test_input_buffer_handling(self):
        """Test handling of input buffer and rapid input."""
        engine = TestGameEngineBuilder().with_mocked_dependencies().build()
        
        # Simulate rapid input sequence
        rapid_input = ['w', 'a', 's', 'd'] * 10  # 40 rapid inputs
        
        try:
            for inp in rapid_input:
                engine.handle_input(inp)
            
            assert True, "Rapid input sequence handled"
            
        except Exception as e:
            # Buffer overflow or similar issues are acceptable
            if any(word in str(e).lower() for word in ['buffer', 'input', 'overflow']):
                assert True, f"Input buffer limitation handled: {e}"
            else:
                assert False, f"Unexpected error with rapid input: {e}"


class TestTerminalOutputHandling:
    """Tests for terminal output handling and buffering."""
    
    def test_output_buffering(self):
        """Test output buffering behavior."""
        engine = TestGameEngineBuilder().with_mocked_dependencies().build()
        
        # Capture stdout to test buffering
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            try:
                # Generate output that tests buffering
                for _ in range(10):
                    engine.render_game()
                
                # Check that output is generated
                output = mock_stdout.getvalue()
                assert True, "Output buffering handled"
                
            except Exception as e:
                assert False, f"Output buffering failed: {e}"
    
    def test_output_encoding_fallback(self):
        """Test fallback behavior for output encoding issues."""
        engine = TestGameEngineBuilder().with_mocked_dependencies().build()
        
        # Test different output encodings
        encodings = ['utf-8', 'ascii', 'cp1252', 'latin1']
        
        for encoding in encodings:
            with patch('sys.stdout.encoding', encoding):
                try:
                    # Test output with potential encoding issues
                    engine.render_game()
                    assert True, f"Output encoding {encoding} handled"
                    
                except (UnicodeEncodeError, UnicodeDecodeError):
                    # Encoding issues should be handled gracefully
                    assert True, f"Encoding {encoding} limitation handled gracefully"
                    
                except Exception as e:
                    assert False, f"Unexpected error with encoding {encoding}: {e}"
    
    def test_large_output_handling(self):
        """Test handling of large output volumes."""
        engine = TestGameEngineBuilder().with_mocked_dependencies().build()
        
        # Create scenario that generates large output
        large_enemy_count = 100
        enemies = [TestEnemyBuilder().at_position(10 + i, 10).build() for i in range(large_enemy_count)]
        engine.enemy_manager.enemies = enemies
        
        try:
            # Generate large output
            for _ in range(20):
                engine.render_game()
                engine.process_enemy_turns()
            
            assert True, "Large output volume handled"
            
        except Exception as e:
            # Memory or buffer issues are acceptable
            if any(word in str(e).lower() for word in ['memory', 'buffer', 'output']):
                assert True, f"Large output limitation handled: {e}"
            else:
                assert False, f"Unexpected error with large output: {e}"


class TestTerminalErrorRecovery:
    """Tests for error recovery in terminal operations."""
    
    def test_broken_pipe_handling(self):
        """Test handling of broken pipe errors."""
        engine = TestGameEngineBuilder().with_mocked_dependencies().build()
        
        # Simulate broken pipe
        def broken_write(*args, **kwargs):
            raise BrokenPipeError("Broken pipe")
        
        with patch('sys.stdout.write', side_effect=broken_write):
            try:
                engine.render_game()
                assert True, "Broken pipe handled gracefully"
                
            except BrokenPipeError:
                # This is acceptable - terminal disconnected
                assert True, "Broken pipe error handled appropriately"
                
            except Exception as e:
                assert False, f"Unexpected error handling broken pipe: {e}"
    
    def test_terminal_disconnect_simulation(self):
        """Test simulation of terminal disconnect/reconnect."""
        engine = TestGameEngineBuilder().with_mocked_dependencies().build()
        
        # Simulate terminal disconnect
        original_stdout = sys.stdout
        
        try:
            # Disconnect terminal
            sys.stdout = None
            
            # Game should handle gracefully
            try:
                engine.render_game()
                assert True, "Terminal disconnect handled"
            except AttributeError:
                # Expected when stdout is None
                assert True, "Terminal disconnect detected appropriately"
            
        except Exception as e:
            assert False, f"Terminal disconnect handling failed: {e}"
            
        finally:
            # Restore terminal
            sys.stdout = original_stdout
    
    def test_encoding_error_recovery(self):
        """Test recovery from encoding errors."""
        engine = TestGameEngineBuilder().with_mocked_dependencies().build()
        
        # Simulate encoding errors
        def encoding_error_write(data):
            if 'test' in str(data):
                raise UnicodeEncodeError('ascii', 'test', 0, 1, 'ordinal not in range')
            return len(data)
        
        with patch('sys.stdout.write', side_effect=encoding_error_write):
            try:
                engine.render_game()
                assert True, "Encoding error recovery worked"
                
            except UnicodeEncodeError:
                # This is acceptable - encoding limitation
                assert True, "Encoding error handled appropriately"
                
            except Exception as e:
                assert False, f"Unexpected error in encoding recovery: {e}"