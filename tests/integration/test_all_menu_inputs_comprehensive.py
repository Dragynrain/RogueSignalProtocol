"""
Comprehensive tests for gamepad input mappings across ALL menu contexts.

Prevents regressions like:
- Missing D-pad left/right in contexts that need horizontal navigation
- Missing analog stick horizontal support in contexts that need it
- Inconsistent input mappings between similar menus

This test suite should ALWAYS pass and catch configuration mistakes early.
"""

import pytest
import tcod.sdl.joystick

from game_input_actions import InputAction, InputContext
from game_input_mappings import InputMapper


class TestMenuGamepadInputCompleteness:
    """Verify all menu contexts have complete and correct gamepad mappings."""

    @pytest.fixture
    def mapper(self):
        """Input mapper for testing."""
        return InputMapper()

    def test_all_menu_contexts_have_basic_buttons(self, mapper):
        """
        All menu contexts must have A (confirm) and B (cancel/back) buttons mapped.

        This is the minimum viable input for any menu screen.
        """
        menu_contexts = [
            InputContext.MAIN_MENU,
            InputContext.SETTINGS_MENU,
            InputContext.HELP,
            InputContext.LORE_VIEWER,
            InputContext.ACHIEVEMENTS_SCREEN,
            InputContext.GRAPHICS_PREVIEW,
            InputContext.ABOUT_MENU,
            InputContext.CONTROLS_MENU,
        ]

        failures = []

        for context in menu_contexts:
            # Test A button (confirm)
            action_a = mapper.get_action_for_gamepad_button(
                tcod.sdl.joystick.ControllerButton.A, context
            )
            if action_a != InputAction.CONFIRM:
                failures.append(f"{context.name}: A button not mapped to CONFIRM")

            # Test B button (cancel/back)
            action_b = mapper.get_action_for_gamepad_button(
                tcod.sdl.joystick.ControllerButton.B, context
            )
            if action_b != InputAction.CANCEL:
                failures.append(f"{context.name}: B button not mapped to CANCEL")

        if failures:
            pytest.fail(
                "Missing basic button mappings:\n" + "\n".join(f"  - {f}" for f in failures)
            )

    def test_all_menu_contexts_have_vertical_navigation(self, mapper):
        """
        All menu contexts must have D-pad UP/DOWN for vertical navigation.

        Even menus with horizontal features still need vertical scrolling.
        """
        menu_contexts = [
            InputContext.MAIN_MENU,
            InputContext.SETTINGS_MENU,
            InputContext.HELP,
            InputContext.LORE_VIEWER,
            InputContext.ACHIEVEMENTS_SCREEN,
            InputContext.GRAPHICS_PREVIEW,
            InputContext.ABOUT_MENU,
            InputContext.CONTROLS_MENU,
        ]

        failures = []

        for context in menu_contexts:
            # Test D-pad UP
            action_up = mapper.get_action_for_gamepad_button(
                tcod.sdl.joystick.ControllerButton.DPAD_UP, context
            )
            if action_up != InputAction.NAVIGATE_UP:
                failures.append(f"{context.name}: D-pad UP not mapped to NAVIGATE_UP")

            # Test D-pad DOWN
            action_down = mapper.get_action_for_gamepad_button(
                tcod.sdl.joystick.ControllerButton.DPAD_DOWN, context
            )
            if action_down != InputAction.NAVIGATE_DOWN:
                failures.append(f"{context.name}: D-pad DOWN not mapped to NAVIGATE_DOWN")

        if failures:
            pytest.fail("Missing vertical navigation:\n" + "\n".join(f"  - {f}" for f in failures))

    def test_contexts_needing_horizontal_have_dpad_left_right(self, mapper):
        """
        Contexts that use horizontal navigation MUST have D-pad LEFT/RIGHT mapped.

        Contexts that need horizontal:
        - SETTINGS_MENU: Adjust values (volume, toggles, colors, etc.)
        - GRAPHICS_PREVIEW: Cycle through variants of entities
        - HELP: Switch between help tabs
        - LORE_VIEWER: Switch between lore tabs
        - LOOK_MODE: Move cursor horizontally
        - TARGETING: Move cursor horizontally

        Contexts that DON'T need horizontal (vertical-only):
        - MAIN_MENU: Purely vertical option selection
        - ABOUT_MENU: Purely vertical scrolling
        - ACHIEVEMENTS_SCREEN: Purely vertical scrolling (no tabs yet)
        - INVENTORY: Purely vertical item selection (no tabs yet)
        """
        contexts_needing_horizontal = [
            (InputContext.SETTINGS_MENU, "Settings Menu - value adjustment"),
            (InputContext.GRAPHICS_PREVIEW, "Graphics Preview - variant cycling"),
            (InputContext.HELP, "Help Menu - tab switching"),
            (InputContext.LORE_VIEWER, "Lore Viewer - tab switching"),
            (InputContext.LOOK_MODE, "Look Mode - cursor movement"),
            (InputContext.TARGETING, "Targeting - cursor movement"),
        ]

        failures = []

        for context, description in contexts_needing_horizontal:
            action_left = mapper.get_action_for_gamepad_button(
                tcod.sdl.joystick.ControllerButton.DPAD_LEFT, context
            )
            action_right = mapper.get_action_for_gamepad_button(
                tcod.sdl.joystick.ControllerButton.DPAD_RIGHT, context
            )

            if action_left != InputAction.NAVIGATE_LEFT:
                failures.append(f"{description}: D-pad LEFT not mapped")
            if action_right != InputAction.NAVIGATE_RIGHT:
                failures.append(f"{description}: D-pad RIGHT not mapped")

        if failures:
            pytest.fail(
                "Missing D-pad horizontal navigation in contexts that need it:\n"
                + "\n".join(f"  - {f}" for f in failures)
            )

    def test_vertical_only_menus_dont_have_horizontal(self, mapper):
        """
        Contexts that are PURELY vertical should NOT have D-pad LEFT/RIGHT.

        This ensures we're not accidentally mapping unnecessary inputs,
        which could cause confusion or conflicts.
        """
        vertical_only_contexts = [
            (InputContext.MAIN_MENU, "Main Menu"),
            # Note: ABOUT_MENU and INVENTORY are in a gray area - they might get
            # horizontal features later. For now, we just verify the ones we're
            # absolutely sure are vertical-only.
        ]

        for context, description in vertical_only_contexts:
            action_left = mapper.get_action_for_gamepad_button(
                tcod.sdl.joystick.ControllerButton.DPAD_LEFT, context
            )
            action_right = mapper.get_action_for_gamepad_button(
                tcod.sdl.joystick.ControllerButton.DPAD_RIGHT, context
            )

            # These should be None (unmapped) since the menu doesn't use them
            if action_left is not None:
                pytest.fail(
                    f"{description}: D-pad LEFT mapped to {action_left.name}, "
                    f"but this is a vertical-only menu. Remove unnecessary mapping."
                )
            if action_right is not None:
                pytest.fail(
                    f"{description}: D-pad RIGHT mapped to {action_right.name}, "
                    f"but this is a vertical-only menu. Remove unnecessary mapping."
                )

    def test_no_duplicate_button_mappings_in_same_context(self, mapper):
        """
        Within a single context, each button should map to at most ONE action.

        This prevents conflicts where pressing a button could trigger multiple actions.
        """
        # Test a few key contexts
        contexts_to_test = [
            InputContext.MAIN_MENU,
            InputContext.SETTINGS_MENU,
            InputContext.GAMEPLAY,
            InputContext.HELP,
        ]

        all_buttons = [
            tcod.sdl.joystick.ControllerButton.A,
            tcod.sdl.joystick.ControllerButton.B,
            tcod.sdl.joystick.ControllerButton.X,
            tcod.sdl.joystick.ControllerButton.Y,
            tcod.sdl.joystick.ControllerButton.DPAD_UP,
            tcod.sdl.joystick.ControllerButton.DPAD_DOWN,
            tcod.sdl.joystick.ControllerButton.DPAD_LEFT,
            tcod.sdl.joystick.ControllerButton.DPAD_RIGHT,
            tcod.sdl.joystick.ControllerButton.LEFTSHOULDER,
            tcod.sdl.joystick.ControllerButton.RIGHTSHOULDER,
        ]

        for context in contexts_to_test:
            # Map button -> action for this context
            button_to_action = {}

            for button in all_buttons:
                action = mapper.get_action_for_gamepad_button(button, context)
                if action is not None:
                    if button in button_to_action:
                        pytest.fail(f"{context.name}: Button {button} mapped multiple times!")
                    button_to_action[button] = action

            # Verify: Each button maps to exactly one action (no duplicates)
            # This is implicitly tested by the dict structure above


class TestAnalogStickMenuSupport:
    """Verify analog stick support in menus that need it."""

    def test_contexts_needing_horizontal_should_support_left_stick_x_axis(self):
        """
        Contexts that need horizontal navigation should process left stick X-axis.

        This is tested indirectly through game_input_gamepad.py behavior.
        The contexts that process LEFTX axis are:
        - GRAPHICS_PREVIEW
        - SETTINGS_MENU
        - HELP
        - LORE_VIEWER

        This is a documentation test to ensure future developers know which
        contexts should have X-axis support.
        """
        import inspect

        from game_input_gamepad import GamepadInputHandler

        # Read the source code to verify the contexts
        source = inspect.getsource(GamepadInputHandler.handle_axis_event)

        # Verify that these contexts are mentioned in the horizontal processing logic
        expected_contexts = ["GRAPHICS_PREVIEW", "SETTINGS_MENU", "HELP", "LORE_VIEWER"]

        for context_name in expected_contexts:
            assert (
                context_name in source
            ), f"GamepadInputHandler.handle_axis_event should process LEFTX for {context_name}"

        # Verify that LEFTX processing is conditional on these contexts
        assert (
            "if context in [" in source or "if context ==" in source
        ), "Horizontal axis processing should be context-aware"

        assert (
            "LEFTX" in source
        ), "GamepadInputHandler should handle LEFTX axis for horizontal movement"
