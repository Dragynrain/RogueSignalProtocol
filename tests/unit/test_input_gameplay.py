#!/usr/bin/env python3
"""
Unit tests for game_input_gameplay.py - GameplayInputHandler.

Tests focus on:
- Movement keyboard input (WASD, arrows, numpad)
- Exploit hotkey usage (1-5)
- UI toggle keys (I, L, F, /, V)
- Wait/rest keys (space, period, KP_5)
- Mouse hover position updates
- Auto-walk cancellation behavior
- UI button click detection (Inv button, exploit bar)
- Gameplay left click (adjacent movement, auto-walk, pass turn)
"""

from unittest.mock import Mock, patch

import pytest
import tcod.event

from game_config import GameConfig
from game_entities import Position
from game_input_gameplay import GameplayInputHandler


def create_mock_game():
    """Create a mock game object for testing."""
    game = Mock()

    # Player
    game.player = Mock()
    game.player.x = 25
    game.player.y = 25
    game.player.position = Position(25, 25)
    game.player.inventory_manager = Mock()
    game.player.inventory_manager.equipped_exploits = [
        "buffer_overflow",
        "memory_leak",
        "sudo",
        None,
        None,
    ]

    # Settings
    game.settings = Mock()
    game.settings.graphics_mode = "glyph"

    # Game state
    game.mouse_hover_world_pos = None
    game.last_camera_offset = Position(0, 0)

    # Auto-walk
    game.autowalk = Mock()
    game.autowalk.is_active = Mock(return_value=False)
    game.autowalk.cancel = Mock()
    game.autowalk.start = Mock(return_value=True)

    # Methods
    game.move_player = Mock()
    game.maybe_process_turn = Mock()

    # UI state
    game.show_lore_viewer = False
    game.show_help = False
    game.show_achievements = False

    # Exploit system
    game.exploit_system = Mock()
    game.exploit_system.use_exploit = Mock()

    # Message log
    game.message_log = Mock()

    # Map
    game.game_map = Mock()
    game.game_map.width = GameConfig.MAP_WIDTH
    game.game_map.height = GameConfig.MAP_HEIGHT
    game.game_map.is_walkable = Mock(return_value=True)

    return game


def create_mock_renderer():
    """Create a mock renderer for testing."""
    renderer = Mock()
    renderer.context = Mock()
    renderer.context.sdl_window = Mock()
    renderer.context.sdl_window.size = (800, 600)
    return renderer


def create_mock_input_handler():
    """Create a mock parent InputHandler."""
    handler = Mock()
    handler._open_inventory = Mock()
    handler._enter_look_mode = Mock()
    handler._trigger_debug_export = Mock()
    return handler


class TestMovementKeys:
    """Test movement keyboard input."""

    def test_wasd_movement(self):
        """Test WASD movement keys."""
        game = create_mock_game()
        handler = GameplayInputHandler(game)

        # Test W (up)
        event = Mock()
        event.sym = tcod.event.KeySym.W
        event.mod = 0
        handler.handle_input(event)
        game.move_player.assert_called_with(0, -1)

        # Test A (left)
        event.sym = tcod.event.KeySym.A
        handler.handle_input(event)
        game.move_player.assert_called_with(-1, 0)

        # Test S (down)
        event.sym = tcod.event.KeySym.S
        handler.handle_input(event)
        game.move_player.assert_called_with(0, 1)

        # Test D (right)
        event.sym = tcod.event.KeySym.D
        handler.handle_input(event)
        game.move_player.assert_called_with(1, 0)

    def test_qezc_diagonal_movement(self):
        """Test QEZC diagonal movement keys."""
        game = create_mock_game()
        handler = GameplayInputHandler(game)

        # Test Q (up-left)
        event = Mock()
        event.sym = tcod.event.KeySym.Q
        event.mod = 0
        handler.handle_input(event)
        game.move_player.assert_called_with(-1, -1)

        # Test E (up-right)
        event.sym = tcod.event.KeySym.E
        handler.handle_input(event)
        game.move_player.assert_called_with(1, -1)

        # Test Z (down-left)
        event.sym = tcod.event.KeySym.Z
        handler.handle_input(event)
        game.move_player.assert_called_with(-1, 1)

        # Test C (down-right)
        event.sym = tcod.event.KeySym.C
        handler.handle_input(event)
        game.move_player.assert_called_with(1, 1)

    def test_arrow_key_movement(self):
        """Test arrow key movement."""
        game = create_mock_game()
        handler = GameplayInputHandler(game)

        event = Mock()
        event.mod = 0

        # Test arrow keys
        event.sym = tcod.event.KeySym.UP
        handler.handle_input(event)
        game.move_player.assert_called_with(0, -1)

        event.sym = tcod.event.KeySym.DOWN
        handler.handle_input(event)
        game.move_player.assert_called_with(0, 1)

        event.sym = tcod.event.KeySym.LEFT
        handler.handle_input(event)
        game.move_player.assert_called_with(-1, 0)

        event.sym = tcod.event.KeySym.RIGHT
        handler.handle_input(event)
        game.move_player.assert_called_with(1, 0)

    def test_numpad_movement(self):
        """Test numpad movement keys."""
        game = create_mock_game()
        handler = GameplayInputHandler(game)

        event = Mock()
        event.mod = 0

        # Test numpad 8 directions
        event.sym = tcod.event.KeySym.KP_8
        handler.handle_input(event)
        game.move_player.assert_called_with(0, -1)

        event.sym = tcod.event.KeySym.KP_2
        handler.handle_input(event)
        game.move_player.assert_called_with(0, 1)

        event.sym = tcod.event.KeySym.KP_4
        handler.handle_input(event)
        game.move_player.assert_called_with(-1, 0)

        event.sym = tcod.event.KeySym.KP_6
        handler.handle_input(event)
        game.move_player.assert_called_with(1, 0)

        # Diagonals
        event.sym = tcod.event.KeySym.KP_7
        handler.handle_input(event)
        game.move_player.assert_called_with(-1, -1)

        event.sym = tcod.event.KeySym.KP_9
        handler.handle_input(event)
        game.move_player.assert_called_with(1, -1)

        event.sym = tcod.event.KeySym.KP_1
        handler.handle_input(event)
        game.move_player.assert_called_with(-1, 1)

        event.sym = tcod.event.KeySym.KP_3
        handler.handle_input(event)
        game.move_player.assert_called_with(1, 1)

    def test_movement_clears_mouse_hover(self):
        """Test that keyboard movement clears mouse hover position."""
        game = create_mock_game()
        game.mouse_hover_world_pos = Position(20, 20)
        handler = GameplayInputHandler(game)

        event = Mock()
        event.sym = tcod.event.KeySym.W
        event.mod = 0
        handler.handle_input(event)

        # Mouse hover should be cleared
        assert game.mouse_hover_world_pos is None


class TestWaitRestKeys:
    """Test wait/rest keyboard input."""

    def test_space_wait(self):
        """Test spacebar for waiting/resting."""
        game = create_mock_game()
        handler = GameplayInputHandler(game)

        event = Mock()
        event.sym = tcod.event.KeySym.SPACE
        event.mod = 0
        handler.handle_input(event)

        game.maybe_process_turn.assert_called_once()

    def test_period_wait(self):
        """Test period key for waiting."""
        game = create_mock_game()
        handler = GameplayInputHandler(game)

        event = Mock()
        event.sym = tcod.event.KeySym.PERIOD
        event.mod = 0
        handler.handle_input(event)

        game.maybe_process_turn.assert_called_once()

    def test_numpad_5_wait(self):
        """Test numpad 5 for waiting."""
        game = create_mock_game()
        handler = GameplayInputHandler(game)

        event = Mock()
        event.sym = tcod.event.KeySym.KP_5
        event.mod = 0
        handler.handle_input(event)

        game.maybe_process_turn.assert_called_once()


class TestExploitHotkeys:
    """Test exploit hotkey usage (1-5 keys)."""

    def test_exploit_slot_1(self):
        """Test using exploit in slot 1."""
        game = create_mock_game()
        handler = GameplayInputHandler(game)

        event = Mock()
        event.sym = tcod.event.KeySym.N1
        event.mod = 0
        handler.handle_input(event)

        game.exploit_system.use_exploit.assert_called_once_with("buffer_overflow")

    def test_exploit_slot_2(self):
        """Test using exploit in slot 2."""
        game = create_mock_game()
        handler = GameplayInputHandler(game)

        event = Mock()
        event.sym = tcod.event.KeySym.N2
        event.mod = 0
        handler.handle_input(event)

        game.exploit_system.use_exploit.assert_called_once_with("memory_leak")

    def test_exploit_slot_3(self):
        """Test using exploit in slot 3."""
        game = create_mock_game()
        handler = GameplayInputHandler(game)

        event = Mock()
        event.sym = tcod.event.KeySym.N3
        event.mod = 0
        handler.handle_input(event)

        game.exploit_system.use_exploit.assert_called_once_with("sudo")

    def test_empty_exploit_slot(self):
        """Test using empty exploit slot still calls use_exploit with None."""
        game = create_mock_game()
        handler = GameplayInputHandler(game)

        event = Mock()
        event.sym = tcod.event.KeySym.N4  # Empty slot (None)
        event.mod = 0
        handler.handle_input(event)

        # Should call use_exploit with None (exploit system will handle invalid key)
        game.exploit_system.use_exploit.assert_called_once_with(None)

    def test_all_exploit_slots(self):
        """Test all exploit slot keys (1-5)."""
        game = create_mock_game()
        handler = GameplayInputHandler(game)

        event = Mock()
        event.mod = 0

        # Test all 5 slots
        for i, key in enumerate(
            [
                tcod.event.KeySym.N1,
                tcod.event.KeySym.N2,
                tcod.event.KeySym.N3,
                tcod.event.KeySym.N4,
                tcod.event.KeySym.N5,
            ]
        ):
            event.sym = key
            handler.handle_input(event)

        # All 5 should be called (first 3 with exploit keys, last 2 with None)
        assert game.exploit_system.use_exploit.call_count == 5


class TestUIToggleKeys:
    """Test UI toggle keys (I, L, F, /, V)."""

    def test_i_opens_inventory(self):
        """Test I key opens inventory."""
        game = create_mock_game()
        input_handler = create_mock_input_handler()
        handler = GameplayInputHandler(game, None, input_handler)

        event = Mock()
        event.sym = tcod.event.KeySym.I
        event.mod = 0
        handler.handle_input(event)

        input_handler._open_inventory.assert_called_once()

    def test_l_enters_look_mode(self):
        """Test L key enters look mode."""
        game = create_mock_game()
        input_handler = create_mock_input_handler()
        handler = GameplayInputHandler(game, None, input_handler)

        event = Mock()
        event.sym = tcod.event.KeySym.L
        event.mod = 0
        handler.handle_input(event)

        input_handler._enter_look_mode.assert_called_once()

    def test_f_opens_lore_viewer(self):
        """Test F key opens lore viewer."""
        game = create_mock_game()
        handler = GameplayInputHandler(game)

        event = Mock()
        event.sym = tcod.event.KeySym.F
        event.mod = 0
        handler.handle_input(event)

        assert game.show_lore_viewer is True

    def test_shift_slash_opens_help(self):
        """Test Shift+/ opens help."""
        game = create_mock_game()
        handler = GameplayInputHandler(game)

        event = Mock()
        event.sym = tcod.event.KeySym.SLASH
        event.mod = tcod.event.Modifier.LSHIFT
        handler.handle_input(event)

        assert game.show_help is True

    def test_v_opens_achievements(self):
        """Test V key opens achievements."""
        game = create_mock_game()
        handler = GameplayInputHandler(game)

        event = Mock()
        event.sym = tcod.event.KeySym.V
        event.mod = 0
        handler.handle_input(event)

        assert game.show_achievements is True


class TestAutoWalkCancellation:
    """Test auto-walk cancellation behavior."""

    def test_autowalk_cancels_on_movement_key(self):
        """Test that movement key cancels auto-walk."""
        game = create_mock_game()
        game.autowalk.is_active.return_value = True
        handler = GameplayInputHandler(game)

        event = Mock()
        event.sym = tcod.event.KeySym.W
        event.mod = 0
        handler.handle_input(event)

        # Auto-walk should be cancelled
        game.autowalk.cancel.assert_called_once()
        # Movement should still execute
        game.move_player.assert_called_with(0, -1)

    def test_autowalk_cancels_on_exploit_key(self):
        """Test that exploit key cancels auto-walk."""
        game = create_mock_game()
        game.autowalk.is_active.return_value = True
        handler = GameplayInputHandler(game)

        event = Mock()
        event.sym = tcod.event.KeySym.N1
        event.mod = 0
        handler.handle_input(event)

        # Auto-walk should be cancelled
        game.autowalk.cancel.assert_called_once()
        # Exploit should still be used
        game.exploit_system.use_exploit.assert_called_once()

    def test_autowalk_not_cancelled_by_help_key(self):
        """Test that help toggle doesn't cancel auto-walk."""
        game = create_mock_game()
        game.autowalk.is_active.return_value = True
        handler = GameplayInputHandler(game)

        event = Mock()
        event.sym = tcod.event.KeySym.SLASH
        event.mod = tcod.event.Modifier.LSHIFT
        handler.handle_input(event)

        # Auto-walk should NOT be cancelled (help is UI toggle)
        game.autowalk.cancel.assert_not_called()


class TestDebugExportHotkey:
    """Test Shift+F12 debug export hotkey."""

    def test_shift_f12_triggers_debug_export(self):
        """Test Shift+F12 triggers debug export."""
        game = create_mock_game()
        input_handler = create_mock_input_handler()
        handler = GameplayInputHandler(game, None, input_handler)

        event = Mock()
        event.sym = tcod.event.KeySym.F12
        event.mod = tcod.event.Modifier.SHIFT
        handler.handle_input(event)

        input_handler._trigger_debug_export.assert_called_once()


class TestMouseHoverUpdates:
    """Test mouse hover position updates."""

    def test_mouse_motion_updates_hover_position(self):
        """Test that mouse motion updates hover position."""
        game = create_mock_game()
        renderer = create_mock_renderer()
        handler = GameplayInputHandler(game, renderer)

        event = Mock()
        event.position = Mock()
        event.position.x = 400
        event.position.y = 300

        with patch(
            "game_input_gameplay.InputCoordinateConverter.pixel_to_world_position",
            return_value=Position(20, 15),
        ):
            result = handler.handle_mouse_motion(event)

        assert result is True
        assert game.mouse_hover_world_pos == Position(20, 15)

    def test_mouse_motion_clears_hover_when_outside_bounds(self):
        """Test that mouse outside bounds clears hover."""
        game = create_mock_game()
        game.mouse_hover_world_pos = Position(10, 10)
        renderer = create_mock_renderer()
        handler = GameplayInputHandler(game, renderer)

        event = Mock()
        event.position = Mock()
        event.position.x = 1000  # Outside bounds
        event.position.y = 1000

        with patch(
            "game_input_gameplay.InputCoordinateConverter.pixel_to_world_position",
            return_value=None,
        ):
            result = handler.handle_mouse_motion(event)

        assert result is False
        assert game.mouse_hover_world_pos is None


class TestGameplayLeftClick:
    """Test gameplay left click behavior."""

    def test_click_on_player_passes_turn(self):
        """Test that clicking on player position passes turn."""
        game = create_mock_game()
        renderer = create_mock_renderer()
        handler = GameplayInputHandler(game, renderer)

        event = Mock()
        event.position = Mock()
        event.position.x = 400
        event.position.y = 300

        # Click on player position (25, 25)
        with patch(
            "game_input_gameplay.InputCoordinateConverter.pixel_to_world_position",
            return_value=Position(25, 25),
        ):
            handler.handle_left_click(event)

        # Should pass turn (move 0, 0)
        game.move_player.assert_called_with(0, 0)

    def test_click_adjacent_tile_moves_immediately(self):
        """Test that clicking adjacent tile moves immediately."""
        game = create_mock_game()
        renderer = create_mock_renderer()
        handler = GameplayInputHandler(game, renderer)

        event = Mock()
        event.position = Mock()
        event.position.x = 400
        event.position.y = 300

        # Click adjacent tile (26, 25) - one tile to the right
        with patch(
            "game_input_gameplay.InputCoordinateConverter.pixel_to_world_position",
            return_value=Position(26, 25),
        ):
            handler.handle_left_click(event)

        # Should move immediately
        game.move_player.assert_called_with(1, 0)

    def test_click_distant_tile_starts_autowalk(self):
        """Test that clicking distant tile starts auto-walk."""
        game = create_mock_game()
        renderer = create_mock_renderer()
        handler = GameplayInputHandler(game, renderer)

        event = Mock()
        event.position = Mock()
        event.position.x = 400
        event.position.y = 300

        # Click distant tile (40, 40)
        with patch(
            "game_input_gameplay.InputCoordinateConverter.pixel_to_world_position",
            return_value=Position(40, 40),
        ):
            handler.handle_left_click(event)

        # Should start auto-walk
        game.autowalk.start.assert_called_once()
        # Should not move immediately
        game.move_player.assert_not_called()

    def test_click_outside_bounds_ignored(self):
        """Test that click outside valid area is ignored gracefully."""
        game = create_mock_game()
        renderer = create_mock_renderer()
        handler = GameplayInputHandler(game, renderer)

        event = Mock()
        event.position = Mock()
        event.position.x = 1000
        event.position.y = 1000

        # Click returns None (outside bounds)
        with patch(
            "game_input_gameplay.InputCoordinateConverter.pixel_to_world_position",
            return_value=None,
        ):
            result = handler.handle_left_click(event)

        # Should return True (event handled) but no action
        assert result is True
        game.move_player.assert_not_called()
        game.autowalk.start.assert_not_called()


class TestUIButtonClicks:
    """Test UI button click detection."""

    def test_inv_button_click(self):
        """Test inventory button click detection."""
        game = create_mock_game()
        renderer = create_mock_renderer()
        input_handler = create_mock_input_handler()
        handler = GameplayInputHandler(game, renderer, input_handler)

        event = Mock()
        event.position = Mock()

        # Calculate Inv button position (must match rendering code)
        inv_button_x = GameConfig.SCREEN_WIDTH - 6  # len("[Inv]") + 1
        inv_button_y = GameConfig.SCREEN_HEIGHT - 1

        # Mock pixel_to_char_coords to return Inv button tile position
        with patch(
            "game_input_gameplay.InputCoordinateConverter.get_window_dimensions",
            return_value=(800, 600),
        ):
            with patch(
                "game_input_gameplay.CoordinateHelpers.pixel_to_char_coords",
                return_value=(inv_button_x, inv_button_y),
            ):
                result = handler.handle_inv_button_click(event)

        assert result is True
        input_handler._open_inventory.assert_called_once()

    def test_exploit_bar_click_slot_1(self):
        """Test clicking on exploit bar slot 1."""
        game = create_mock_game()
        renderer = create_mock_renderer()
        handler = GameplayInputHandler(game, renderer)

        event = Mock()
        event.position = Mock()

        # Mock UIRenderer.get_exploit_at_click to return slot 0
        with patch(
            "game_input_gameplay.InputCoordinateConverter.get_window_dimensions",
            return_value=(800, 600),
        ):
            with patch(
                "game_input_gameplay.CoordinateHelpers.pixel_to_char_coords", return_value=(10, 48)
            ):  # Some position in exploit bar
                with patch("game_rendering_ui.UIRenderer.get_exploit_at_click", return_value=0):
                    result = handler.handle_exploit_bar_click(event)

        assert result is True
        game.exploit_system.use_exploit.assert_called_once_with("buffer_overflow")

    def test_exploit_bar_click_returns_false_when_no_exploit(self):
        """Test that clicking outside exploit bar returns False."""
        game = create_mock_game()
        renderer = create_mock_renderer()
        handler = GameplayInputHandler(game, renderer)

        event = Mock()
        event.position = Mock()

        # Mock UIRenderer.get_exploit_at_click to return None
        with patch(
            "game_input_gameplay.InputCoordinateConverter.get_window_dimensions",
            return_value=(800, 600),
        ):
            with patch(
                "game_input_gameplay.CoordinateHelpers.pixel_to_char_coords", return_value=(10, 10)
            ):  # Random position
                with patch("game_rendering_ui.UIRenderer.get_exploit_at_click", return_value=None):
                    result = handler.handle_exploit_bar_click(event)

        assert result is False
        game.exploit_system.use_exploit.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
