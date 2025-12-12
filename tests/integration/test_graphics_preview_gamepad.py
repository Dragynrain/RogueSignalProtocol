"""
Graphics Preview Menu Gamepad Input Testing

Tests gamepad input for the Graphics Preview menu, specifically:
- D-pad navigation (should not multi-jump or auto-scroll)
- Left stick horizontal movement (should work for variant cycling)
- Button release handling (should stop auto-repeat)

BUGS BEING TESTED:
1. Left stick horizontal axis is completely ignored (only vertical works)
2. D-pad button releases are not handled, causing state confusion
3. Auto-repeat system is not polled, causing erratic behavior
"""

from unittest.mock import Mock

import pytest

from game_config import GameSettings


class TestGraphicsPreviewGamepadInput:
    """Test gamepad input for Graphics Preview menu."""

    @pytest.fixture
    def graphics_preview_menu(self):
        """Create graphics preview menu for testing."""
        from game_graphics_tiles import TileManager
        from game_menu_graphics_preview import GraphicsPreviewMenu

        # Create mock context
        context = Mock()
        context.sdl_renderer = None  # Will use glyph mode for testing

        settings = GameSettings()
        settings.graphics_mode = "glyph"  # Simpler for testing

        tile_manager = TileManager(context, settings)

        menu = GraphicsPreviewMenu(context, settings, tile_manager)

        # Ensure test data is available for entity navigation tests
        # This allows tests to run even if no sprites are loaded
        if not menu.entity_types:
            menu.entity_types = [
                ("terrain", "wall", "Wall"),
                ("terrain", "floor", "Floor"),
                ("player", "player", "Player"),
            ]
            menu.variants = {
                "wall": [0, 1],
                "floor": [0],
                "player": [0, 1, 2],
            }
            menu.selected_variants = {
                "wall": 0,
                "floor": 0,
                "player": 0,
            }
            menu.current_entity_index = 0

        yield menu

    # --------------------------------------------------------------------------
    # Left Stick Horizontal Movement Tests (BUG: Currently broken)
    # --------------------------------------------------------------------------

    def test_left_stick_horizontal_changes_variant(self, graphics_preview_menu):
        """
        LEFT STICK HORIZONTAL: Should cycle variants.

        Uses real TCOD events (isinstance checks require real types, not mocks).
        """
        import tcod.event

        menu = graphics_preview_menu

        # Get initial variant
        _, entity_key, _ = menu.entity_types[menu.current_entity_index]
        initial_variant = menu.selected_variants[entity_key]

        # Create left stick RIGHT event (LEFTX axis) - use real TCOD event
        event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION",
            which=0,
            axis=tcod.sdl.joystick.ControllerAxis.LEFTX,
            value=25000,  # Right direction (past threshold)
        )

        # Handle the event
        result = menu.handle_input(event)

        # Get new variant
        new_variant = menu.selected_variants[entity_key]

        # Variant should change (cycle right)
        assert new_variant != initial_variant, "Left stick horizontal should cycle variants"

    def test_left_stick_horizontal_left_cycles_variant_backward(self, graphics_preview_menu):
        """
        LEFT STICK HORIZONTAL LEFT: Should cycle variants backward.

        Uses real TCOD events (isinstance checks require real types, not mocks).
        """
        import tcod.event

        menu = graphics_preview_menu

        # Get initial variant
        _, entity_key, _ = menu.entity_types[menu.current_entity_index]
        initial_variant = menu.selected_variants[entity_key]

        # Create left stick LEFT event (LEFTX axis) - use real TCOD event
        event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION",
            which=0,
            axis=tcod.sdl.joystick.ControllerAxis.LEFTX,
            value=-25000,  # Left direction (past threshold)
        )

        # Handle the event
        result = menu.handle_input(event)

        # Get new variant
        new_variant = menu.selected_variants[entity_key]

        # Variant should change (cycle left)
        assert new_variant != initial_variant, "Left stick horizontal should cycle variants"

    # --------------------------------------------------------------------------
    # D-pad Variant Cycling Tests
    # --------------------------------------------------------------------------

    def test_dpad_left_right_cycles_variants(self, graphics_preview_menu):
        """D-pad LEFT/RIGHT: Should cycle variants correctly."""
        import tcod.event

        menu = graphics_preview_menu

        # Get initial variant
        _, entity_key, _ = menu.entity_types[menu.current_entity_index]
        initial_variant = menu.selected_variants[entity_key]

        # Press D-pad RIGHT - use real TCOD event
        event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN",
            which=0,
            button=tcod.sdl.joystick.ControllerButton.DPAD_RIGHT,
            pressed=True,
        )

        result = menu.handle_input(event)

        # Get new variant
        new_variant = menu.selected_variants[entity_key]

        # D-pad should work for variant cycling
        assert new_variant != initial_variant, "D-pad RIGHT should cycle variant forward"

    # NOTE: test_dpad_release_clears_held_state removed - covered by test_gamepad_auto_repeat.py

    def test_dpad_no_multi_jump_on_single_press(self, graphics_preview_menu):
        """
        D-pad SINGLE PRESS: Should only move selection once, not multiple times.

        Tests that a single button press moves selection exactly once.
        """
        import tcod.event

        menu = graphics_preview_menu

        initial_index = menu.current_entity_index

        # Single D-pad DOWN press - use real TCOD event
        event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN",
            which=0,
            button=tcod.sdl.joystick.ControllerButton.DPAD_DOWN,
            pressed=True,
        )

        menu.handle_input(event)

        # Should move exactly one position
        expected_index = (initial_index + 1) % len(menu.entity_types)
        assert (
            menu.current_entity_index == expected_index
        ), "Single D-pad press should move selection exactly once"

    # --------------------------------------------------------------------------
    # Left Stick Vertical Movement Tests (Should work)
    # --------------------------------------------------------------------------

    def test_left_stick_vertical_navigates_entities(self, graphics_preview_menu):
        """Left stick VERTICAL: Should navigate entity list."""
        import tcod.event

        menu = graphics_preview_menu

        initial_index = menu.current_entity_index

        # Left stick DOWN - use real TCOD event
        event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION",
            which=0,
            axis=tcod.sdl.joystick.ControllerAxis.LEFTY,
            value=25000,  # Down direction (past threshold)
        )

        menu.handle_input(event)

        # Should navigate down the list
        assert (
            menu.current_entity_index != initial_index
        ), "Left stick vertical should navigate entity list"

    # --------------------------------------------------------------------------
    # Integration Test: Real-world scenario
    # --------------------------------------------------------------------------

    def test_variant_cycling_with_stick_and_dpad_mixed(self, graphics_preview_menu):
        """
        INTEGRATION: Mix of stick horizontal and D-pad for variant cycling.

        Real-world usage: User tries both stick and D-pad to cycle variants.
        Both should work seamlessly.
        """
        import tcod.event

        menu = graphics_preview_menu

        _, entity_key, _ = menu.entity_types[menu.current_entity_index]
        initial_variant = menu.selected_variants[entity_key]

        # Try left stick horizontal RIGHT first - use real TCOD event
        stick_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION",
            which=0,
            axis=tcod.sdl.joystick.ControllerAxis.LEFTX,
            value=25000,  # Right direction
        )

        menu.handle_input(stick_event)
        variant_after_stick = menu.selected_variants[entity_key]

        # Try D-pad RIGHT - use real TCOD event
        dpad_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN",
            which=0,
            button=tcod.sdl.joystick.ControllerButton.DPAD_RIGHT,
            pressed=True,
        )

        menu.handle_input(dpad_event)
        variant_after_dpad = menu.selected_variants[entity_key]

        # At least ONE of them should have changed the variant
        assert (
            variant_after_stick != initial_variant or variant_after_dpad != variant_after_stick
        ), "Either stick or D-pad should cycle variants"

        # Both should work
        assert (
            variant_after_stick != initial_variant
        ), "Left stick horizontal should work for variant cycling!"
