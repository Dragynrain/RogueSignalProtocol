"""
Gamepad Menu Polling Tests - Test stick-based navigation via polling path.

These tests verify that analog stick navigation works through the polling path
in game_loop.py, not just through events. The polling path is critical because
stick-held state doesn't generate new events - only initial axis change does.

Coverage:
- Menu navigation with analog stick via polling
- Auto-repeat timing verification (0.3s initial, 0.12s repeat)
- Both polling branches in game_loop.py (gameplay vs modal scrolling)
- All menu types: Settings, Help, Achievements, Lore Viewer

Uses the game_with_gamepad fixture from tests/conftest.py.
Uses mock_time fixture for deterministic timing (no flaky time.sleep).
"""

import pytest
import tcod.event
import tcod.sdl.joystick

from rsp.core.config import GameConfig
from rsp.input.actions import InputAction, InputContext
from rsp.input.analog import AnalogStickHandler

# Shortcuts
CB = tcod.sdl.joystick.ControllerButton
CA = tcod.sdl.joystick.ControllerAxis

# Timing constants from game_config.py
MENU_INITIAL_DELAY = GameConfig.MENU_NAVIGATION_INITIAL_DELAY  # 0.3s
MENU_REPEAT_RATE = GameConfig.MENU_NAVIGATION_REPEAT_RATE  # 0.12s
SETTLING_PERIOD_SEC = 0.035  # 30ms settling + 5ms safety margin


@pytest.fixture
def analog_handler():
    """Create standalone analog handler for timing tests."""
    return AnalogStickHandler(deadzone=0.15, threshold=0.3, direction_locking=True)


class TestMenuNavigationPolling:
    """Test stick-based menu navigation via polling path."""

    def test_left_stick_generates_navigation_action_in_menu_context(self, game_with_gamepad):
        """Left stick deflection should generate NAVIGATE_UP/DOWN in menu context."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler

        # Set stick to full up (negative Y = up in SDL)
        axis_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.LEFTY, value=-32000  # Full up
        )

        # Handle in MAIN_MENU context
        action = gamepad.handle_axis_event(axis_event, InputContext.MAIN_MENU)

        # Should get NAVIGATE_UP action
        assert action == InputAction.NAVIGATE_UP

    def test_left_stick_generates_navigate_down_in_menu(self, game_with_gamepad):
        """Left stick down should generate NAVIGATE_DOWN."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler

        # Set stick to full down
        axis_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.LEFTY, value=32000  # Full down
        )

        # Handle in SETTINGS_MENU context
        action = gamepad.handle_axis_event(axis_event, InputContext.SETTINGS_MENU)

        assert action == InputAction.NAVIGATE_DOWN

    def test_left_stick_horizontal_in_settings_menu(self, game_with_gamepad):
        """Left stick horizontal should work in settings menu for value adjustment."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler

        # Full right on X axis
        axis_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.LEFTX, value=32000
        )

        action = gamepad.handle_axis_event(axis_event, InputContext.SETTINGS_MENU)

        assert action == InputAction.NAVIGATE_RIGHT

    def test_left_stick_horizontal_ignored_in_main_menu(self, game_with_gamepad):
        """Left stick horizontal should be ignored in main menu (vertical only)."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler

        # Full right on X axis
        axis_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.LEFTX, value=32000
        )

        # Main menu only uses vertical navigation
        action = gamepad.handle_axis_event(axis_event, InputContext.MAIN_MENU)

        # Should return None (ignored)
        assert action is None

    def test_analog_handler_menu_movement_with_timing(self, analog_handler):
        """Verify analog handler menu movement respects timing."""
        handler = analog_handler

        # Set stick to full up
        handler.update_left_stick(x=0, y=-32000)

        # First movement should be immediate (menu doesn't have settling period)
        movement1 = handler.get_left_stick_movement_menu()
        assert movement1 is not None
        assert movement1 == (0, -1)  # Up

        # Second movement immediately should be blocked
        movement2 = handler.get_left_stick_movement_menu()
        assert movement2 is None  # Blocked by auto-repeat timing

    def test_analog_handler_menu_repeat_after_delay(self, analog_handler, mock_time):
        """After initial delay, held stick should start repeating."""
        handler = analog_handler

        # Set stick to full up
        handler.update_left_stick(x=0, y=-32000)

        # First movement
        mock_time.advance(SETTLING_PERIOD_SEC)
        movement1 = handler.get_left_stick_movement_menu()
        assert movement1 is not None

        # Wait for initial delay (0.3s)
        mock_time.advance(MENU_INITIAL_DELAY + 0.01)

        # Should get repeat movement
        movement2 = handler.get_left_stick_movement_menu()
        assert movement2 is not None
        assert movement2 == (0, -1)

    def test_direction_change_resets_timing(self, analog_handler, mock_time):
        """Changing direction should allow immediate movement."""
        handler = analog_handler

        # Move up first
        handler.update_left_stick(x=0, y=-32000)
        mock_time.advance(SETTLING_PERIOD_SEC)
        movement1 = handler.get_left_stick_movement_menu()
        assert movement1 == (0, -1)

        # Change to down - should reset timing
        handler.update_left_stick(x=0, y=32000)
        mock_time.advance(SETTLING_PERIOD_SEC)

        # Should get immediate movement in new direction
        movement2 = handler.get_left_stick_movement_menu()
        assert movement2 is not None
        assert movement2 == (0, 1)  # Down

    def test_direction_change_allows_immediate_movement(self, analog_handler):
        """Changing to opposite direction should allow immediate movement."""
        handler = analog_handler

        # Move up - menu movement is immediate (no settling period)
        handler.update_left_stick(x=0, y=-32000)
        movement1 = handler.get_left_stick_movement_menu()
        assert movement1 is not None
        assert movement1 == (0, -1)  # Up

        # Change direction to DOWN - should get immediate movement
        handler.update_left_stick(x=0, y=32000)
        movement2 = handler.get_left_stick_movement_menu()
        assert movement2 is not None
        assert movement2 == (0, 1)  # Down (direction changed = immediate)

        # Change direction again to LEFT - should also be immediate
        handler.update_left_stick(x=-32000, y=0)
        movement3 = handler.get_left_stick_movement_menu()
        assert movement3 is not None
        assert movement3 == (-1, 0)  # Left

    def test_stick_release_resets_menu_state(self, analog_handler, mock_time):
        """Releasing stick should reset timing, allowing immediate re-push."""
        handler = analog_handler

        # Move up - first movement
        handler.update_left_stick(x=0, y=-32000)
        movement1 = handler.get_left_stick_movement_menu()
        assert movement1 is not None

        # Release stick - this should reset all state
        handler.update_left_stick(x=0, y=0)
        release_result = handler.get_left_stick_movement_menu()
        assert release_result is None  # Returns None on release

        # Small delay then push up AGAIN (same direction)
        mock_time.advance(0.05)
        handler.update_left_stick(x=0, y=-32000)

        # Should get IMMEDIATE movement (timing was reset by release)
        movement2 = handler.get_left_stick_movement_menu()
        assert movement2 is not None
        assert movement2 == (0, -1)  # Up


class TestAchievementsScreenPolling:
    """Test achievements screen uses faster auto-repeat."""

    def test_fast_repeat_context_detection(self, game_with_gamepad):
        """Achievements screen should use faster repeat rate."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler

        # Check that ACHIEVEMENTS_SCREEN is in fast_repeat_contexts
        assert InputContext.ACHIEVEMENTS_SCREEN in gamepad.fast_repeat_contexts

    def test_fast_repeat_rate_is_faster(self, game_with_gamepad):
        """Fast repeat rate should be faster than normal."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler

        normal_rate = gamepad.get_repeat_rate(InputContext.MAIN_MENU)
        fast_rate = gamepad.get_repeat_rate(InputContext.ACHIEVEMENTS_SCREEN)

        assert fast_rate < normal_rate

    def test_achievements_scrolling_via_stick(self, game_with_gamepad):
        """Stick should generate navigation in achievements context."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler

        # Set stick down
        axis_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.LEFTY, value=32000
        )

        action = gamepad.handle_axis_event(axis_event, InputContext.ACHIEVEMENTS_SCREEN)

        assert action == InputAction.NAVIGATE_DOWN


class TestHelpMenuPolling:
    """Test help menu uses horizontal stick navigation for pages."""

    def test_help_menu_horizontal_navigation(self, game_with_gamepad):
        """Help menu should accept left/right stick for page navigation."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler

        # Set stick right
        axis_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.LEFTX, value=32000
        )

        action = gamepad.handle_axis_event(axis_event, InputContext.HELP)

        assert action == InputAction.NAVIGATE_RIGHT

    def test_help_menu_vertical_navigation(self, game_with_gamepad):
        """Help menu should also accept vertical navigation."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler

        # Set stick down
        axis_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.LEFTY, value=32000
        )

        action = gamepad.handle_axis_event(axis_event, InputContext.HELP)

        assert action == InputAction.NAVIGATE_DOWN


class TestLoreViewerPolling:
    """Test lore viewer menu navigation."""

    def test_lore_viewer_horizontal_for_tabs(self, game_with_gamepad):
        """Lore viewer should use horizontal stick for tab switching."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler

        # Set stick left
        axis_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.LEFTX, value=-32000
        )

        action = gamepad.handle_axis_event(axis_event, InputContext.LORE_VIEWER)

        assert action == InputAction.NAVIGATE_LEFT

    def test_lore_viewer_vertical_for_scrolling(self, game_with_gamepad):
        """Lore viewer should use vertical stick for content scrolling."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler

        # Set stick up
        axis_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.LEFTY, value=-32000
        )

        action = gamepad.handle_axis_event(axis_event, InputContext.LORE_VIEWER)

        assert action == InputAction.NAVIGATE_UP


class TestGraphicsPreviewPolling:
    """Test graphics preview menu uses both axes."""

    def test_graphics_preview_horizontal_for_variants(self, game_with_gamepad):
        """Graphics preview should use horizontal for variant cycling."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler

        # Set stick right
        axis_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.LEFTX, value=32000
        )

        action = gamepad.handle_axis_event(axis_event, InputContext.GRAPHICS_PREVIEW)

        assert action == InputAction.NAVIGATE_RIGHT

    def test_graphics_preview_vertical_for_entity_selection(self, game_with_gamepad):
        """Graphics preview should use vertical for entity selection."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler

        # Set stick down
        axis_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.LEFTY, value=32000
        )

        action = gamepad.handle_axis_event(axis_event, InputContext.GRAPHICS_PREVIEW)

        assert action == InputAction.NAVIGATE_DOWN


class TestInventoryPolling:
    """Test inventory menu navigation."""

    def test_inventory_vertical_navigation(self, game_with_gamepad):
        """Inventory should use vertical stick for item selection."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler

        # Set stick up
        axis_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.LEFTY, value=-32000
        )

        action = gamepad.handle_axis_event(axis_event, InputContext.INVENTORY)

        assert action == InputAction.NAVIGATE_UP


# NOTE: TestSwapSticksMenuNavigation removed - covered by test_swap_sticks_issue1_menus.py


class TestGameplayPollingBranch:
    """Test the gameplay polling branch in game_loop.py."""

    def test_gameplay_movement_via_analog_handler(self, game_with_gamepad, mock_time):
        """Gameplay movement should use get_left_stick_movement_gameplay."""
        game, input_handler, _ = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        # Set stick right
        analog.update_left_stick(x=32000, y=0)

        # First call starts settling period (returns None)
        analog.get_left_stick_movement_gameplay(game.turn)

        # Wait for settling period to complete
        mock_time.advance(SETTLING_PERIOD_SEC)

        # Second call gets movement after settling
        movement = analog.get_left_stick_movement_gameplay(game.turn)

        assert movement is not None
        assert movement == (1, 0)  # Right

    def test_gameplay_movement_respects_turn_gating(self, game_with_gamepad, mock_time):
        """Gameplay movement should be gated by time-based auto-repeat."""
        game, input_handler, _ = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        initial_turn = game.turn

        # Set stick right
        analog.update_left_stick(x=32000, y=0)

        # Start settling, wait, then get first movement
        analog.get_left_stick_movement_gameplay(initial_turn)
        mock_time.advance(SETTLING_PERIOD_SEC)

        # First movement succeeds
        movement1 = analog.get_left_stick_movement_gameplay(initial_turn)
        assert movement1 is not None

        # Second movement immediately is blocked (time-based gating)
        movement2 = analog.get_left_stick_movement_gameplay(initial_turn)
        assert movement2 is None

    def test_modal_excludes_gameplay_polling(self, game_with_gamepad):
        """When modal is open, gameplay polling branch should not trigger."""
        game, input_handler, _ = game_with_gamepad

        # Open inventory
        game.show_inventory = True

        # Verify context is not GAMEPLAY
        context = input_handler._get_current_context()
        assert context != InputContext.GAMEPLAY
        assert context == InputContext.INVENTORY

    def test_help_excludes_gameplay_polling(self, game_with_gamepad):
        """When help is open, gameplay polling branch should not trigger."""
        game, input_handler, _ = game_with_gamepad

        # Open help
        game.show_help = True

        context = input_handler._get_current_context()
        assert context == InputContext.HELP


class TestModalScrollingPollingBranch:
    """Test the modal scrolling polling branch in game_loop.py."""

    def test_achievements_uses_modal_scrolling_path(self, game_with_gamepad):
        """Achievements screen should use modal scrolling path."""
        game, input_handler, _ = game_with_gamepad

        game.show_achievements = True

        context = input_handler._get_current_context()
        assert context == InputContext.ACHIEVEMENTS_SCREEN

    def test_help_uses_modal_scrolling_path(self, game_with_gamepad):
        """Help screen should use modal scrolling path."""
        game, input_handler, _ = game_with_gamepad

        game.show_help = True

        context = input_handler._get_current_context()
        assert context == InputContext.HELP


class TestButtonAutoRepeatInMenus:
    """Test D-pad button auto-repeat in menus."""

    def test_dpad_triggers_auto_repeat_tracking(self, game_with_gamepad):
        """D-pad press should start auto-repeat tracking in menu."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler

        # Press D-pad up
        button_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.DPAD_UP, pressed=True
        )

        gamepad.handle_button_event(button_event, InputContext.MAIN_MENU)

        # Should be tracking this button
        assert gamepad.button_held == CB.DPAD_UP
        assert gamepad.button_held_since > 0

    def test_button_release_stops_auto_repeat(self, game_with_gamepad):
        """Releasing button should stop auto-repeat tracking."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler

        # Press button
        press_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.DPAD_DOWN, pressed=True
        )
        gamepad.handle_button_event(press_event, InputContext.MAIN_MENU)

        # Release button
        release_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.DPAD_DOWN, pressed=False
        )
        gamepad.handle_button_event(release_event, InputContext.MAIN_MENU)

        # Should stop tracking
        assert gamepad.button_held is None

    def test_get_button_repeat_action_returns_none_before_delay(self, game_with_gamepad):
        """get_button_repeat_action should return None before initial delay."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler

        # Press button
        button_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.DPAD_UP, pressed=True
        )
        gamepad.handle_button_event(button_event, InputContext.MAIN_MENU)

        # Immediately check for repeat - should be None
        repeat_action = gamepad.get_button_repeat_action(InputContext.MAIN_MENU)
        assert repeat_action is None

    def test_get_button_repeat_action_returns_action_after_delay(self, game_with_gamepad, mock_time):
        """get_button_repeat_action should return action after initial delay."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler

        # Press button
        button_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.DPAD_UP, pressed=True
        )
        gamepad.handle_button_event(button_event, InputContext.MAIN_MENU)

        # Wait for initial delay
        mock_time.advance(MENU_INITIAL_DELAY + 0.02)

        # Should get repeat action
        repeat_action = gamepad.get_button_repeat_action(InputContext.MAIN_MENU)
        assert repeat_action == InputAction.NAVIGATE_UP
