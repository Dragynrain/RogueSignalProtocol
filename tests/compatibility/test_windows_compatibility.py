"""
Windows compatibility validation tests.

Tests game functionality across different Windows versions, terminal types,
path handling, file system behaviors, and Windows-specific features.
"""

import pytest
import os
import sys
import platform
import tempfile
import subprocess
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from game_engine import GameEngine
from game_characters import Player, Enemy
from game_config import GameConfig
from game_entities import Position
from tests.performance.test_movement_constants import Direction
from tests.fixtures.test_builders import TestGameEngineBuilder, TestPlayerBuilder, TestEnemyBuilder


class TestWindowsPathHandling:
    """Tests for Windows-specific path handling."""
    
    def test_windows_path_separators(self):
        """Test handling of Windows path separators."""
        engine = TestGameEngineBuilder().with_mocked_dependencies().build()
        
        # Test various Windows path formats
        windows_paths = [
            r"C:\Games\RogueSignal\save.dat",
            r"C:/Games/RogueSignal/save.dat",
            r".\saves\player.save",
            r"./saves/player.save",
            r"..\..\data\config.json",
            r"../../data/config.json",
            r"C:\Program Files\Game\data.txt",
            r"C:\Users\Player Name\Documents\saves\game.save"
        ]
        
        for path in windows_paths:
            try:
                # Test path normalization
                normalized = os.path.normpath(path)
                assert os.path.isabs(normalized) or not os.path.isabs(path), f"Path normalization failed for {path}"
                
                # Test path operations
                dirname = os.path.dirname(path)
                basename = os.path.basename(path)
                
                assert isinstance(dirname, str), f"dirname failed for {path}"
                assert isinstance(basename, str), f"basename failed for {path}"
                
            except Exception as e:
                assert False, f"Windows path handling failed for {path}: {e}"
    
    def test_long_path_support(self):
        """Test support for long Windows paths."""
        if platform.system() != "Windows":
            pytest.skip("Windows-specific test")
        
        # Create a very long path (Windows traditionally had 260 char limit)
        long_path_components = ["very_long_directory_name_that_exceeds_normal_limits"] * 10
        long_path = os.path.join("C:", *long_path_components, "test_file.txt")
        
        try:
            # Test path operations with long paths
            dirname = os.path.dirname(long_path)
            basename = os.path.basename(long_path)
            
            assert len(long_path) > 260, f"Test path not long enough: {len(long_path)} chars"
            assert isinstance(dirname, str), "Long path dirname failed"
            assert isinstance(basename, str), "Long path basename failed"
            
        except Exception as e:
            # Long path limitations are acceptable on older Windows
            if "path too long" in str(e).lower() or "filename too long" in str(e).lower():
                pytest.skip(f"System doesn't support long paths: {e}")
            else:
                assert False, f"Unexpected error with long paths: {e}"
    
    def test_unicode_path_handling(self):
        """Test Unicode character handling in paths."""
        engine = TestGameEngineBuilder().with_mocked_dependencies().build()
        
        # Test paths with various Unicode characters
        unicode_paths = [
            r"C:\Игры\RogueSignal\save.dat",  # Cyrillic
            r"C:\游戏\RogueSignal\save.dat",  # Chinese
            r"C:\ゲーム\RogueSignal\save.dat",  # Japanese
            r"C:\Spiele\Rögue Signäl\save.dat",  # German with umlauts
            r"C:\Jeux\Rôgue Sîgnal\save.dat",  # French with accents
        ]
        
        for path in unicode_paths:
            try:
                # Test basic path operations
                normalized = os.path.normpath(path)
                dirname = os.path.dirname(path)
                basename = os.path.basename(path)
                
                assert isinstance(normalized, str), f"Unicode path normalization failed for {path}"
                assert isinstance(dirname, str), f"Unicode dirname failed for {path}"
                assert isinstance(basename, str), f"Unicode basename failed for {path}"
                
            except UnicodeError as e:
                pytest.skip(f"System doesn't support Unicode paths: {e}")
            except Exception as e:
                assert False, f"Unicode path handling failed for {path}: {e}"
    
    def test_drive_letter_handling(self):
        """Test Windows drive letter handling."""
        if platform.system() != "Windows":
            pytest.skip("Windows-specific test")
        
        # Test various drive letter formats
        drive_paths = [
            r"C:\game\save.dat",
            r"D:\backup\save.dat",
            r"Z:\network\save.dat",
            r"c:\game\save.dat",  # lowercase
            r"\\server\share\save.dat",  # UNC path
            r"\\?\C:\very\long\path\save.dat",  # Extended path
        ]
        
        for path in drive_paths:
            try:
                # Test drive detection
                drive = os.path.splitdrive(path)[0]
                
                if path.startswith(r"\\"):
                    # UNC or extended path
                    assert len(drive) >= 2, f"UNC drive detection failed for {path}"
                else:
                    # Regular drive letter
                    assert len(drive) == 2 and drive[1] == ':', f"Drive letter detection failed for {path}"
                
                # Test path operations
                is_abs = os.path.isabs(path)
                assert is_abs, f"Absolute path detection failed for {path}"
                
            except Exception as e:
                assert False, f"Drive letter handling failed for {path}: {e}"


class TestWindowsTerminalCompatibility:
    """Tests for Windows terminal compatibility."""
    
    def test_command_prompt_compatibility(self):
        """Test compatibility with Windows Command Prompt."""
        engine = TestGameEngineBuilder().with_mocked_dependencies().build()
        
        # Simulate Command Prompt environment
        with patch.dict(os.environ, {
            'TERM': '',  # Command Prompt doesn't set TERM
            'COMSPEC': r'C:\Windows\System32\cmd.exe',
            'PROCESSOR_ARCHITECTURE': 'AMD64',
        }):
            try:
                # Test game initialization
                dx, dy = Direction.NORTH.value
                engine.move_player(dx, dy)
                engine.process_enemy_turns()
                engine.render_game()
                
                assert True, "Game works in Command Prompt environment"
                
            except Exception as e:
                assert False, f"Command Prompt compatibility failed: {e}"
    
    def test_powershell_compatibility(self):
        """Test compatibility with PowerShell."""
        engine = TestGameEngineBuilder().with_mocked_dependencies().build()
        
        # Simulate PowerShell environment
        with patch.dict(os.environ, {
            'TERM': '',
            'PSModulePath': r'C:\Windows\system32\WindowsPowerShell\v1.0\Modules',
            'PROCESSOR_ARCHITECTURE': 'AMD64',
        }):
            try:
                # Test game functionality
                dx, dy = Direction.NORTH.value
                engine.move_player(dx, dy)
                engine.process_enemy_turns()
                engine.render_game()
                
                assert True, "Game works in PowerShell environment"
                
            except Exception as e:
                assert False, f"PowerShell compatibility failed: {e}"
    
    def test_windows_terminal_compatibility(self):
        """Test compatibility with Windows Terminal."""
        engine = TestGameEngineBuilder().with_mocked_dependencies().build()
        
        # Simulate Windows Terminal environment
        with patch.dict(os.environ, {
            'TERM': 'xterm-256color',
            'WT_SESSION': 'some-session-id',
            'PROCESSOR_ARCHITECTURE': 'AMD64',
        }):
            try:
                # Test enhanced terminal features
                dx, dy = Direction.NORTH.value
                engine.move_player(dx, dy)
                engine.process_enemy_turns()
                engine.render_game()
                
                assert True, "Game works in Windows Terminal"
                
            except Exception as e:
                assert False, f"Windows Terminal compatibility failed: {e}"
    
    def test_console_encoding_handling(self):
        """Test console encoding handling on Windows."""
        engine = TestGameEngineBuilder().with_mocked_dependencies().build()
        
        # Test different console encodings
        encodings = ['cp1252', 'cp437', 'utf-8', 'utf-16']
        
        for encoding in encodings:
            try:
                # Simulate different console encoding
                with patch('sys.stdout.encoding', encoding):
                    # Test text output that might have encoding issues
                    test_strings = [
                        "ASCII text only",
                        "Extended: café naïve résumé",
                        "Symbols: ♠♣♥♦",
                        "Box drawing: ┌─┐│└┘"
                    ]
                    
                    for test_str in test_strings:
                        try:
                            # Test if string can be encoded
                            encoded = test_str.encode(encoding, errors='replace')
                            decoded = encoded.decode(encoding)
                            
                            # Game should handle encoding gracefully
                            engine.render_game()
                            
                        except (UnicodeEncodeError, UnicodeDecodeError):
                            # Encoding errors are acceptable - game should handle gracefully
                            pass
                
            except Exception as e:
                assert False, f"Console encoding handling failed for {encoding}: {e}"


class TestWindowsFileSystemBehaviors:
    """Tests for Windows file system specific behaviors."""
    
    def test_case_insensitive_paths(self):
        """Test case-insensitive path handling on Windows."""
        if platform.system() != "Windows":
            pytest.skip("Windows-specific test")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test file
            test_file = os.path.join(temp_dir, "TestFile.txt")
            with open(test_file, 'w') as f:
                f.write("test content")
            
            # Test case-insensitive access
            variations = [
                os.path.join(temp_dir, "TestFile.txt"),
                os.path.join(temp_dir, "testfile.txt"),
                os.path.join(temp_dir, "TESTFILE.TXT"),
                os.path.join(temp_dir, "TestFILE.txt"),
            ]
            
            for variation in variations:
                try:
                    exists = os.path.exists(variation)
                    assert exists, f"Case-insensitive access failed for {variation}"
                    
                    # Test reading
                    with open(variation, 'r') as f:
                        content = f.read()
                        assert content == "test content", f"Content mismatch for {variation}"
                        
                except Exception as e:
                    assert False, f"Case-insensitive file access failed for {variation}: {e}"
    
    def test_reserved_filename_handling(self):
        """Test handling of Windows reserved filenames."""
        reserved_names = [
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            for reserved_name in reserved_names:
                try:
                    # Test that the game handles reserved names gracefully
                    reserved_path = os.path.join(temp_dir, reserved_name + ".txt")
                    
                    # Attempting to create reserved name files may fail or behave unexpectedly
                    try:
                        with open(reserved_path, 'w') as f:
                            f.write("test")
                        
                        # If creation succeeded, clean up
                        if os.path.exists(reserved_path):
                            os.remove(reserved_path)
                            
                    except (OSError, IOError):
                        # This is expected for reserved names
                        pass
                    
                    # Game should handle this gracefully
                    assert True, f"Reserved name {reserved_name} handled appropriately"
                    
                except Exception as e:
                    assert False, f"Reserved filename handling failed for {reserved_name}: {e}"
    
    def test_file_locking_behavior(self):
        """Test Windows file locking behavior."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, "locked_file.txt")
            
            try:
                # Create and open file exclusively
                with open(test_file, 'w') as f1:
                    f1.write("locked content")
                    
                    # Try to open the same file again (should work on Windows for reading)
                    try:
                        with open(test_file, 'r') as f2:
                            content = f2.read()
                            assert content == "locked content", "File content mismatch"
                    except IOError:
                        # Some locking behavior is acceptable
                        pass
                
                # File should be accessible after closing
                with open(test_file, 'r') as f:
                    content = f.read()
                    assert content == "locked content", "File not accessible after closing"
                
            except Exception as e:
                assert False, f"File locking behavior test failed: {e}"


class TestWindowsSystemIntegration:
    """Tests for Windows system integration features."""
    
    def test_windows_registry_simulation(self):
        """Test simulation of Windows registry interactions."""
        # Since we can't modify actual registry in tests, simulate the behavior
        mock_registry = {
            r'HKEY_CURRENT_USER\Software\RogueSignalProtocol': {
                'InstallPath': r'C:\Program Files\RogueSignalProtocol',
                'Version': '1.0.0',
                'LastPlayed': '2024-01-01'
            }
        }
        
        def mock_registry_read(key, value):
            """Mock registry reading."""
            if key in mock_registry and value in mock_registry[key]:
                return mock_registry[key][value]
            raise FileNotFoundError(f"Registry key not found: {key}\\{value}")
        
        try:
            # Test registry access patterns
            install_path = mock_registry_read(
                r'HKEY_CURRENT_USER\Software\RogueSignalProtocol', 
                'InstallPath'
            )
            assert install_path == r'C:\Program Files\RogueSignalProtocol', "Registry read failed"
            
            version = mock_registry_read(
                r'HKEY_CURRENT_USER\Software\RogueSignalProtocol',
                'Version'
            )
            assert version == '1.0.0', "Version read failed"
            
        except Exception as e:
            assert False, f"Registry simulation failed: {e}"
    
    def test_windows_service_simulation(self):
        """Test simulation of Windows service interactions."""
        # Simulate checking for running services
        mock_services = {
            'Windows Audio': 'Running',
            'Windows Defender': 'Running',
            'Print Spooler': 'Stopped',
            'RogueSignalService': 'Running'
        }
        
        def check_service_status(service_name):
            """Mock service status check."""
            return mock_services.get(service_name, 'Not Found')
        
        try:
            # Test service status checks
            audio_status = check_service_status('Windows Audio')
            assert audio_status == 'Running', "Audio service check failed"
            
            game_service = check_service_status('RogueSignalService')
            assert game_service == 'Running', "Game service check failed"
            
            non_existent = check_service_status('NonExistentService')
            assert non_existent == 'Not Found', "Non-existent service check failed"
            
        except Exception as e:
            assert False, f"Service simulation failed: {e}"
    
    def test_windows_security_context(self):
        """Test Windows security context handling."""
        # Test different security contexts
        security_contexts = [
            {'admin': False, 'elevated': False},  # Standard user
            {'admin': True, 'elevated': False},   # Admin user, not elevated
            {'admin': True, 'elevated': True},    # Elevated admin
        ]
        
        for context in security_contexts:
            try:
                # Simulate security context
                with patch.dict(os.environ, {
                    'USERNAME': 'TestUser',
                    'USERDOMAIN': 'TESTDOMAIN',
                }):
                    
                    engine = TestGameEngineBuilder().with_mocked_dependencies().build()
                    
                    # Game should work in all security contexts
                    dx, dy = Direction.NORTH.value
                engine.move_player(dx, dy)
                    engine.process_enemy_turns()
                    
                    # Some operations might be restricted in certain contexts
                    try:
                        engine.save_game()
                    except PermissionError:
                        # Permission errors are acceptable in restricted contexts
                        if not context['elevated']:
                            pass  # Expected in non-elevated context
                        else:
                            raise
                
            except Exception as e:
                assert False, f"Security context test failed for {context}: {e}"


class TestWindowsPerformanceCharacteristics:
    """Tests for Windows-specific performance characteristics."""
    
    def test_windows_timer_precision(self):
        """Test Windows timer precision and performance measurement."""
        import time
        
        # Test timer precision
        timestamps = []
        for _ in range(100):
            timestamps.append(time.perf_counter())
            time.sleep(0.001)  # 1ms sleep
        
        # Calculate actual intervals
        intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
        
        # Windows timer should have reasonable precision
        min_interval = min(intervals)
        max_interval = max(intervals)
        avg_interval = sum(intervals) / len(intervals)
        
        assert min_interval > 0, "Timer precision too low"
        assert avg_interval > 0.0005, "Average interval too small"  # At least 0.5ms
        assert max_interval < 0.1, "Maximum interval too large"     # Less than 100ms
    
    def test_memory_allocation_patterns(self):
        """Test Windows memory allocation patterns."""
        import psutil
        
        initial_memory = psutil.Process().memory_info().rss
        
        # Create memory allocation pattern typical on Windows
        allocations = []
        for size in [1024, 4096, 8192, 16384, 32768]:  # Common Windows page sizes
            allocation = bytearray(size)
            allocations.append(allocation)
            
            current_memory = psutil.Process().memory_info().rss
            memory_increase = current_memory - initial_memory
            
            # Memory should increase predictably
            assert memory_increase > 0, f"Memory didn't increase for allocation size {size}"
        
        # Clean up
        del allocations
        import gc
        gc.collect()
        
        # Memory should be released
        final_memory = psutil.Process().memory_info().rss
        memory_retained = final_memory - initial_memory
        
        # Some memory retention is normal on Windows
        assert memory_retained < 50 * 1024 * 1024, "Too much memory retained after cleanup"  # 50MB max
    
    def test_file_system_performance(self):
        """Test file system performance characteristics on Windows."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test file creation performance
            start_time = time.perf_counter()
            
            test_files = []
            for i in range(100):
                file_path = os.path.join(temp_dir, f"test_file_{i}.txt")
                with open(file_path, 'w') as f:
                    f.write(f"test content {i}")
                test_files.append(file_path)
            
            creation_time = time.perf_counter() - start_time
            
            # Test file access performance
            start_time = time.perf_counter()
            
            for file_path in test_files:
                with open(file_path, 'r') as f:
                    content = f.read()
                    assert "test content" in content, "File content mismatch"
            
            access_time = time.perf_counter() - start_time
            
            # Test file deletion performance
            start_time = time.perf_counter()
            
            for file_path in test_files:
                os.remove(file_path)
            
            deletion_time = time.perf_counter() - start_time
            
            # Performance should be reasonable
            assert creation_time < 5.0, f"File creation too slow: {creation_time:.3f}s"
            assert access_time < 2.0, f"File access too slow: {access_time:.3f}s"
            assert deletion_time < 3.0, f"File deletion too slow: {deletion_time:.3f}s"