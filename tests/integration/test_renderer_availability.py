"""
Phase 3.2: Renderer Availability Failure Tests

Tests that modal actions handle renderer being None gracefully.
From .claude/gamepad.md - common failure mode when InputHandler
initialized without renderer parameter.

Test coverage:
- Help screen actions when renderer is None
- Lore viewer actions when renderer is None
- Achievements screen when renderer is None
- Inventory when renderer is None (should still work)
- Graceful degradation without crashes
"""

import pytest
import tcod.event
import tcod.sdl.joystick

from rsp.core.config import GameSettings
from rsp.core.engine import GameEngine
from rsp.input.handler import InputHandler
from rsp.systems.audio import NullSoundManager

# Shortcuts
CB = tcod.sdl.joystick.ControllerButton


@pytest.fixture
def headless_game():
    """Create game instance WITHOUT renderer (headless mode)."""
    settings = GameSettings()
    settings.graphics_mode = "text"
    sound_manager = NullSoundManager(settings)
    game = GameEngine(settings=settings, sound_manager=sound_manager)

    # Create input handler WITHOUT renderer (this is the crash scenario)
    input_handler = InputHandler(game, renderer=None, controllers=set())

    # Clear starting dialogue
    game.dialogue_state.active_dialogue = None
    game.dialogue_state.dialogue_history = []

    return game, input_handler


class TestHelpScreenWithoutRenderer:
    """Test help screen behavior when renderer is None."""

    def test_help_screen_opens_but_degrades_gracefully(self, headless_game):
        """Opening help without renderer doesn't crash."""
        game, input_handler = headless_game

        # Try to open help screen
        game.show_help = True

        # Send escape key to close
        esc_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.ESCAPE,
            sym=tcod.event.KeySym.ESCAPE,
            mod=tcod.event.Modifier.NONE,
        )

        # Should handle without crashing
        result = input_handler.handle_keydown(esc_event)
        assert result is True

        # Help should be closed
        assert game.show_help is False

    def test_help_screen_gamepad_without_renderer(self, headless_game):
        """Opening help with gamepad without renderer doesn't crash."""
        game, input_handler = headless_game

        # Open help screen
        game.show_help = True

        # Send B button to close (gamepad escape)
        b_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.B, pressed=True
        )

        # Should handle without crashing
        result = input_handler.handle_controller_button(b_event)
        assert result is True

        # Help should be closed
        assert game.show_help is False

    def test_help_navigation_degraded_without_renderer(self, headless_game):
        """Help navigation is degraded but doesn't crash without renderer."""
        game, input_handler = headless_game

        # Open help screen
        game.show_help = True

        # Try to navigate with D-pad (won't work without renderer, but shouldn't crash)
        dpad_down = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.DPAD_DOWN, pressed=True
        )

        # Should handle without crashing
        result = input_handler.handle_controller_button(dpad_down)
        assert result is True  # Handled (degraded mode)


class TestLoreViewerWithoutRenderer:
    """Test lore viewer behavior when renderer is None."""

    def test_lore_viewer_keyboard_esc_without_renderer(self, headless_game):
        """Lore viewer handles ESC without renderer."""
        game, input_handler = headless_game

        # Force lore viewer open (normally prevented, but tests might do this)
        game.show_lore_viewer = True

        # Send escape to close
        esc_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.ESCAPE,
            sym=tcod.event.KeySym.ESCAPE,
            mod=tcod.event.Modifier.NONE,
        )

        # Should handle without crashing
        result = input_handler.handle_keydown(esc_event)
        assert result is True

        # Lore viewer should be closed
        assert game.show_lore_viewer is False

    def test_lore_viewer_gamepad_without_renderer(self, headless_game):
        """Lore viewer handles B button without renderer."""
        game, input_handler = headless_game

        # Force lore viewer open
        game.show_lore_viewer = True

        # Send B button to close
        b_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.B, pressed=True
        )

        # Should handle without crashing (new fix)
        result = input_handler.handle_controller_button(b_event)
        assert result is True

        # Lore viewer should be closed
        assert game.show_lore_viewer is False

    def test_lore_viewer_navigation_degraded_without_renderer(self, headless_game):
        """Lore viewer navigation degraded but doesn't crash without renderer."""
        game, input_handler = headless_game

        # Force lore viewer open
        game.show_lore_viewer = True

        # Try to navigate (won't work without renderer, but shouldn't crash)
        dpad_down = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.DPAD_DOWN, pressed=True
        )

        # Should handle without crashing
        result = input_handler.handle_controller_button(dpad_down)
        assert result is True  # Handled (degraded mode)


class TestInventoryWithoutRenderer:
    """Test inventory behavior when renderer is None (inventory should still work!)."""

    def test_inventory_works_without_renderer(self, headless_game):
        """Inventory is functional without renderer (no visual needed for logic)."""
        game, input_handler = headless_game

        # Open inventory
        game.show_inventory = True

        # Send escape to close inventory (simpler test - just verify no crash)
        esc_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.ESCAPE,
            sym=tcod.event.KeySym.ESCAPE,
            mod=tcod.event.Modifier.NONE,
        )

        # Should handle without crashing
        result = input_handler.handle_keydown(esc_event)
        assert result is True

        # Inventory should be closed
        assert game.show_inventory is False

    def test_inventory_gamepad_without_renderer(self, headless_game):
        """Inventory handles gamepad input without renderer."""
        game, input_handler = headless_game

        # Open inventory
        game.show_inventory = True

        # Navigate with D-pad
        dpad_down = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.DPAD_DOWN, pressed=True
        )

        # Should handle without crashing
        result = input_handler.handle_controller_button(dpad_down)
        assert result is True


class TestGracefulDegradation:
    """Test graceful degradation patterns."""

    def test_renderer_none_doesnt_crash_modal_actions(self, headless_game):
        """All modal screens handle renderer=None gracefully."""
        game, input_handler = headless_game

        # Test each modal screen
        modals = [
            ("show_help", "Help screen"),
            ("show_lore_viewer", "Lore viewer"),
            ("show_inventory", "Inventory"),
            ("show_achievements", "Achievements"),
        ]

        for modal_attr, modal_name in modals:
            # Open modal
            setattr(game, modal_attr, True)

            # Send B button
            b_event = tcod.event.ControllerButton(
                type="CONTROLLERBUTTONDOWN", which=0, button=CB.B, pressed=True
            )

            # Should handle without crashing
            try:
                result = input_handler.handle_controller_button(b_event)
                assert result is True, f"{modal_name} should handle B button"
            except AttributeError as e:
                pytest.fail(f"{modal_name} crashed with renderer=None: {e}")
            except RuntimeError as e:
                # RuntimeError from _get_lore_menu is OK if proper guard exists
                assert "renderer" in str(e).lower(), f"Unexpected error: {e}"

            # Clean up
            setattr(game, modal_attr, False)

    def test_opening_modals_protected_when_renderer_none(self, headless_game):
        """Modal screens that require renderer can't be opened without one."""
        game, input_handler = headless_game

        # Try to open lore viewer with F key (should be blocked)
        f_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.F, sym=tcod.event.KeySym.F, mod=tcod.event.Modifier.NONE
        )

        input_handler.handle_keydown(f_event)

        # Lore viewer should NOT open (renderer required)
        assert game.show_lore_viewer is False, "Lore viewer should not open without renderer"
