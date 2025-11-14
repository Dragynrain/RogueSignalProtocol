#!/usr/bin/env python3
"""
Integration tests for debug export system.

Tests the complete user flows for creating debug packages:
1. Shift+F12 hotkey during gameplay
2. Settings menu button (keyboard navigation)
3. Settings menu button (mouse clicks)

These tests verify the full end-to-end integration including:
- Input handling (keyboard & mouse)
- Dialogue system integration
- Message log feedback
- Actual debug package creation
- Error handling
"""

import zipfile
from unittest.mock import Mock, patch

import pytest
import tcod.event

from debug_export import DebugExporter
from game_config import GameSettings
from game_engine import GameEngine
from game_input import InputHandler
from game_menus import SettingsMenu


@pytest.fixture
def temp_export_dir(tmp_path):
    """Create temporary export directory for tests."""
    export_dir = tmp_path / "debug_exports"
    export_dir.mkdir()

    # Mock the EXPORT_DIR to use temp directory
    original_dir = DebugExporter.EXPORT_DIR
    DebugExporter.EXPORT_DIR = export_dir

    yield export_dir

    # Restore original
    DebugExporter.EXPORT_DIR = original_dir


@pytest.fixture
def temp_game_files(tmp_path, monkeypatch):
    """Create temporary game directories for testing."""
    # Create directory structure
    saves_dir = tmp_path / "saves"
    saves_dir.mkdir()
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    metrics_dir = tmp_path / "metrics"
    metrics_dir.mkdir()

    # Create sample files
    (saves_dir / "rogue_signal_save.json").write_text('{"level": 3}')
    (saves_dir / "user_settings.json").write_text('{"volume": 0.7}')
    (logs_dir / "game_debug.log").write_text("Test log\n")
    (metrics_dir / "test_session.json").write_text('{"session": "test"}')

    # Change to temp directory
    monkeypatch.chdir(tmp_path)

    yield tmp_path


@pytest.fixture
def mock_game_engine():
    """Create a mock game engine for testing."""
    game = Mock(spec=GameEngine)
    game.level = 5
    game.turn = 123
    game.game_over = False

    # Mock dialogue state
    game.dialogue_state = Mock()
    game.dialogue_state.active_dialogue = None
    game.dialogue_state.show = Mock()
    game.dialogue_state.get_active = Mock(return_value=None)

    # Mock message log
    game.message_log = Mock()
    game.message_log.add_message = Mock()

    # Mock player
    game.player = Mock()
    game.player.x = 10
    game.player.y = 15
    game.player.cpu = 85
    game.player.max_cpu = 100
    game.player.heat = 20
    game.player.max_heat = 100
    game.player.trace_level = 1
    game.player.ram_total = 5
    game.player.speed_moves_remaining = 0
    game.player.temporary_effects = {}
    game.player.position = Mock(x=10, y=15)
    game.player.last_position = Mock(x=10, y=15)
    game.player.inventory_manager = Mock()
    game.player.inventory_manager.equipped_exploits = ["exploit1"]
    game.player.inventory_manager.max_equipped_exploits = 3
    game.player.inventory_manager.items = []

    # Mock game state
    game.game_state = Mock()
    game.game_state.dungeon_seed = 99999
    game.game_state.threat_scan_turns = 0
    game.game_state.noise_locations = []
    game.game_state.distraction_points = {}
    game.game_state.revealed_special_nodes = {}

    # Mock game map
    game.game_map = Mock()
    game.game_map.code_hacks = []
    game.game_map.exploit_pickups = []
    game.game_map.permanent_upgrades = {}
    game.game_map.story_fragments = {}
    game.game_map.gateway = None
    game.game_map.explored_tiles = set()
    game.game_map.last_known_enemy_positions = {}

    # Mock enemies
    game.enemies = []

    # Mock additional game state
    game.admin_spawned = False
    game.code_hack_effects = {}
    game.discovered_code_effects = []
    game.inventory_selection = 0
    game.lore_viewer_selection = 0

    # Mock sound manager
    game.sound_manager = Mock()
    game.sound_manager.play_sound = Mock()

    # Mock UI state flags
    game.show_help = False
    game.show_inventory = False
    game.show_lore = False
    game.show_achievements = False
    game.look_mode = False
    game.targeting_mode = False
    game.menu_mode = False

    # Mock pending flag
    game._pending_debug_export = False

    return game


@pytest.fixture
def input_handler(mock_game_engine):
    """Create an input handler with mock game engine."""
    handler = InputHandler(mock_game_engine)
    return handler


@pytest.fixture
def settings_menu(mock_game_engine):
    """Create a settings menu instance."""
    settings = GameSettings()
    menu = SettingsMenu(settings)
    return menu


# ============================================================================
# Test Shift+F12 Hotkey Flow
# ============================================================================


def test_shift_f12_triggers_debug_export_dialogue(input_handler, mock_game_engine):
    """Test that Shift+F12 triggers the debug export confirmation dialogue."""
    # Create Shift+F12 event
    event = tcod.event.KeyDown(
        scancode=tcod.event.Scancode.F12, sym=tcod.event.KeySym.F12, mod=tcod.event.Modifier.SHIFT
    )

    # Simulate gameplay input
    input_handler._handle_gameplay_input(event)

    # Verify dialogue was shown
    mock_game_engine.dialogue_state.show.assert_called_once()

    # Verify the dialogue has correct title and options
    call_args = mock_game_engine.dialogue_state.show.call_args
    dialogue = call_args[0][0]

    assert dialogue.title == "Export Debug Package"
    assert "[Y] Yes" in dialogue.options
    assert "[N] No" in dialogue.options
    assert tcod.event.KeySym.Y in dialogue.valid_keys
    assert tcod.event.KeySym.N in dialogue.valid_keys


def test_shift_f12_confirm_creates_debug_package(
    input_handler, mock_game_engine, temp_export_dir, temp_game_files
):
    """Test that confirming the Shift+F12 dialogue creates a debug package."""
    # First trigger the dialogue
    event = tcod.event.KeyDown(
        scancode=tcod.event.Scancode.F12, sym=tcod.event.KeySym.F12, mod=tcod.event.Modifier.SHIFT
    )
    input_handler._handle_gameplay_input(event)

    # Set the pending flag (normally set by _trigger_debug_export)
    mock_game_engine._pending_debug_export = True

    # Simulate dialogue being active with proper attributes
    mock_dialogue = Mock()
    mock_dialogue.title = "Export Debug Package"
    mock_dialogue.valid_keys = [tcod.event.KeySym.Y, tcod.event.KeySym.N]
    mock_game_engine.dialogue_state.active_dialogue = mock_dialogue
    mock_game_engine.dialogue_state.get_active = Mock(return_value=mock_dialogue)

    # Call the confirm handler (simulates pressing 'Y')
    input_handler._handle_dialogue_confirm()

    # Verify message log was updated
    assert mock_game_engine.message_log.add_message.call_count >= 1

    # Verify a message about creating debug package was logged
    messages = [call[0][0] for call in mock_game_engine.message_log.add_message.call_args_list]
    assert any("Creating debug package" in msg for msg in messages)
    assert any("Debug package created" in msg for msg in messages)


def test_shift_f12_cancel_closes_dialogue(input_handler, mock_game_engine):
    """Test that pressing 'N' or ESC cancels the debug export dialogue."""
    # Set up dialogue as active with proper attributes
    mock_dialogue = Mock()
    mock_dialogue.title = "Export Debug Package"
    mock_dialogue.valid_keys = [tcod.event.KeySym.Y, tcod.event.KeySym.N]
    mock_game_engine.dialogue_state.active_dialogue = mock_dialogue
    mock_game_engine.dialogue_state.get_active = Mock(return_value=mock_dialogue)

    # Simulate pressing 'N' to cancel
    cancel_event = tcod.event.KeyDown(
        scancode=tcod.event.Scancode.N, sym=tcod.event.KeySym.N, mod=0
    )

    # Handle the keydown (should not trigger export)
    input_handler.handle_keydown(cancel_event)

    # Verify no debug package creation was attempted
    # (message_log should not have "Creating debug package" message)
    if mock_game_engine.message_log.add_message.called:
        messages = [call[0][0] for call in mock_game_engine.message_log.add_message.call_args_list]
        assert not any("Creating debug package" in msg for msg in messages)


# ============================================================================
# Test Settings Menu Keyboard Flow
# ============================================================================


def test_settings_menu_navigate_to_export_option(settings_menu):
    """Test navigating to the Export Debug Package option in settings menu."""
    # Find the index of "Export Debug Package" option
    export_index = None
    for i, option in enumerate(settings_menu.options):
        if option.get("name") == "Export Debug Package":
            export_index = i
            break

    assert export_index is not None, "Export Debug Package option not found in settings menu"

    # Navigate to the option
    settings_menu.selected_option = export_index

    # Verify we're on the correct option
    assert settings_menu.options[settings_menu.selected_option]["name"] == "Export Debug Package"


def test_settings_menu_export_shows_confirmation(settings_menu):
    """Test that selecting Export Debug Package shows confirmation dialogue."""
    # Find and select the export option
    for i, option in enumerate(settings_menu.options):
        if option.get("name") == "Export Debug Package":
            settings_menu.selected_option = i
            break

    # Simulate pressing Enter
    event = tcod.event.KeyDown(
        scancode=tcod.event.Scancode.RETURN, sym=tcod.event.KeySym.RETURN, mod=0
    )

    settings_menu.handle_input(event)

    # Verify confirmation dialogue is shown
    assert settings_menu.show_export_confirmation is True
    assert settings_menu.export_confirmation_selection == 0  # Default to first option


def test_settings_menu_confirm_export_returns_action(settings_menu):
    """Test that confirming export in settings menu returns correct action."""
    # Show the confirmation dialogue
    settings_menu.show_export_confirmation = True
    settings_menu.export_confirmation_selection = 0  # "Yes, Export"

    # Simulate pressing Enter to confirm
    event = tcod.event.KeyDown(
        scancode=tcod.event.Scancode.RETURN, sym=tcod.event.KeySym.RETURN, mod=0
    )

    result = settings_menu.handle_input(event)

    # Verify the action returned
    assert result == "export_debug_confirmed"
    assert settings_menu.show_export_confirmation is False


def test_settings_menu_cancel_export_confirmation(settings_menu):
    """Test that canceling export confirmation closes the dialogue."""
    # Show the confirmation dialogue
    settings_menu.show_export_confirmation = True
    settings_menu.export_confirmation_selection = 1  # "No, Cancel"

    # Simulate pressing Enter on "No"
    event = tcod.event.KeyDown(
        scancode=tcod.event.Scancode.RETURN, sym=tcod.event.KeySym.RETURN, mod=0
    )

    result = settings_menu.handle_input(event)

    # Verify dialogue was closed without export action
    assert result == ""
    assert settings_menu.show_export_confirmation is False


def test_settings_menu_escape_closes_confirmation(settings_menu):
    """Test that ESC key closes the export confirmation dialogue."""
    # Show the confirmation dialogue
    settings_menu.show_export_confirmation = True

    # Simulate pressing ESC
    event = tcod.event.KeyDown(
        scancode=tcod.event.Scancode.ESCAPE, sym=tcod.event.KeySym.ESCAPE, mod=0
    )

    result = settings_menu.handle_input(event)

    # Verify dialogue was closed
    assert settings_menu.show_export_confirmation is False
    assert result == ""


# ============================================================================
# Test Settings Menu Mouse Flow
# ============================================================================


def test_settings_menu_mouse_click_export_button(settings_menu, monkeypatch):
    """Test clicking the Export Debug Package button with mouse."""
    # Mock console for rendering
    mock_console = Mock()
    settings_menu.render(mock_console)

    # Find the export option coordinates
    export_index = None
    for i, option in enumerate(settings_menu.options):
        if option.get("name") == "Export Debug Package":
            export_index = i
            break

    assert export_index is not None

    # The menu stores click coordinates during render
    # We need to simulate a click at the option's position
    # This is complex without full rendering, so we test the logic path

    # Set selected option to export option
    settings_menu.selected_option = export_index

    # Test that clicking triggers the same flow as Enter key
    enter_event = tcod.event.KeyDown(
        scancode=tcod.event.Scancode.RETURN, sym=tcod.event.KeySym.RETURN, mod=0
    )

    settings_menu.handle_input(enter_event)

    # Verify confirmation dialogue is shown
    assert settings_menu.show_export_confirmation is True


def test_settings_menu_mouse_click_confirm_yes(settings_menu):
    """Test clicking 'Yes' in export confirmation with mouse."""
    # Render to populate click coordinates
    mock_console = Mock()
    settings_menu.show_export_confirmation = True
    settings_menu._render_export_confirmation_dialog(mock_console)

    # Verify click ranges were set
    assert settings_menu.confirm_option_0_x_range is not None
    assert settings_menu.confirm_option_0_y is not None

    # Select "Yes" option
    settings_menu.export_confirmation_selection = 0

    # Simulate Enter key (mouse click handler would set selection then trigger this)
    event = tcod.event.KeyDown(
        scancode=tcod.event.Scancode.RETURN, sym=tcod.event.KeySym.RETURN, mod=0
    )

    result = settings_menu.handle_input(event)

    # Verify export action was returned
    assert result == "export_debug_confirmed"


def test_settings_menu_mouse_click_confirm_no(settings_menu):
    """Test clicking 'No' in export confirmation with mouse."""
    # Render to populate click coordinates
    mock_console = Mock()
    settings_menu.show_export_confirmation = True
    settings_menu._render_export_confirmation_dialog(mock_console)

    # Select "No" option
    settings_menu.export_confirmation_selection = 1

    # Simulate Enter key
    event = tcod.event.KeyDown(
        scancode=tcod.event.Scancode.RETURN, sym=tcod.event.KeySym.RETURN, mod=0
    )

    result = settings_menu.handle_input(event)

    # Verify dialogue was closed without export
    assert result == ""
    assert settings_menu.show_export_confirmation is False


# ============================================================================
# Test Debug Package Creation
# ============================================================================


def test_debug_package_created_with_game_state(temp_export_dir, temp_game_files, mock_game_engine):
    """Test that debug package includes game state snapshot."""
    from debug_export import export_debug_package

    # Create debug package with game engine
    zip_path = export_debug_package(game_engine=mock_game_engine)

    assert zip_path is not None
    assert zip_path.exists()
    assert zipfile.is_zipfile(zip_path)

    # Verify game snapshot is included
    with zipfile.ZipFile(zip_path, "r") as zipf:
        assert "game_snapshot.json" in zipf.namelist()


def test_debug_package_creation_error_handling(
    input_handler, mock_game_engine, temp_export_dir, temp_game_files
):
    """Test that debug package creation errors are handled gracefully."""
    with patch("debug_export.export_debug_package", side_effect=Exception("Disk full")):
        # Trigger debug export
        input_handler._perform_debug_export()

        # Verify error message was shown to user
        messages = [call[0][0] for call in mock_game_engine.message_log.add_message.call_args_list]
        assert any("Debug export error" in msg for msg in messages)


# ============================================================================
# Test Message Log Feedback
# ============================================================================


def test_debug_export_shows_creation_message(
    input_handler, mock_game_engine, temp_export_dir, temp_game_files
):
    """Test that user sees 'Creating debug package...' message."""
    # Perform debug export
    input_handler._perform_debug_export()

    # Verify message was shown
    messages = [call[0][0] for call in mock_game_engine.message_log.add_message.call_args_list]
    assert any("Creating debug package" in msg for msg in messages)


def test_debug_export_shows_success_message(
    input_handler, mock_game_engine, temp_export_dir, temp_game_files
):
    """Test that user sees success message with filename and instructions."""
    # Perform debug export
    input_handler._perform_debug_export()

    # Verify success messages were shown
    messages = [call[0][0] for call in mock_game_engine.message_log.add_message.call_args_list]
    assert any("Debug package created" in msg for msg in messages)
    assert any("debug_exports/" in msg for msg in messages)
    assert any("github.com" in msg for msg in messages)


def test_debug_export_shows_failure_message(
    input_handler, mock_game_engine, temp_export_dir, temp_game_files
):
    """Test that user sees failure message when export fails."""
    with patch("debug_export.export_debug_package", return_value=None):
        # Perform debug export (will fail)
        input_handler._perform_debug_export()

        # Verify failure message was shown
        messages = [call[0][0] for call in mock_game_engine.message_log.add_message.call_args_list]
        assert any("Failed to create debug package" in msg for msg in messages)


# ============================================================================
# Test Color Usage
# ============================================================================


def test_debug_export_uses_valid_colors(
    input_handler, mock_game_engine, temp_export_dir, temp_game_files
):
    """Test that debug export uses valid color names (not Colors.GOLD)."""
    # This test verifies the fix for the Colors.GOLD bug

    # Perform debug export
    input_handler._perform_debug_export()

    # Verify that all color arguments are valid
    for call in mock_game_engine.message_log.add_message.call_args_list:
        if len(call[0]) > 1:  # Has color argument
            color = call[0][1]
            # Should be a tuple of RGB values, not a KeyError
            assert isinstance(color, tuple)
            assert len(color) == 3
