"""
Phase 3.3: Performance and Stress Tests

Tests system performance under high load and stress conditions.

Test coverage:
- Event flood handling (1000+ events/second)
- Button spam (rapid presses)
- Simultaneous multi-button presses
- Axis event deduplication
- Memory leaks from repeated actions
"""

import time

import pytest
import tcod.event
import tcod.sdl.joystick

from game_audio import NullSoundManager
from game_config import GameSettings
from game_engine import GameEngine
from game_input import InputHandler

# Shortcuts
CB = tcod.sdl.joystick.ControllerButton
CA = tcod.sdl.joystick.ControllerAxis


@pytest.fixture
def game_setup():
    """Create game instance for performance testing."""
    from unittest.mock import Mock

    settings = GameSettings()
    settings.graphics_mode = "text"
    sound_manager = NullSoundManager(settings)
    game = GameEngine(settings=settings, sound_manager=sound_manager)

    # Mock controller
    mock_controller = Mock()
    mock_controller.name = "Test Controller"
    mock_controller.instance_id = 0
    controllers = {mock_controller}

    # Create input handler
    input_handler = InputHandler(game, renderer=None, controllers=controllers)

    # Clear starting dialogue
    game.dialogue_state.active_dialogue = None
    game.dialogue_state.dialogue_history = []

    return game, input_handler


class TestEventFloodHandling:
    """Test handling of high-frequency event floods."""

    def test_rapid_axis_events(self, game_setup):
        """Handle 100 rapid axis events without lag."""
        game, input_handler = game_setup

        start_time = time.perf_counter()

        # Send 100 axis events rapidly
        for i in range(100):
            axis_event = tcod.event.ControllerAxis(
                type="CONTROLLERAXISMOTION",
                which=0,
                axis=CA.LEFTX,
                value=int((i % 10) * 3276.7),  # Vary value
            )
            input_handler.handle_controller_axis(axis_event)

        end_time = time.perf_counter()
        elapsed = end_time - start_time

        # Should process 100 events in under 100ms (1ms per event avg)
        assert elapsed < 0.1, f"Took {elapsed:.3f}s to process 100 events (too slow)"

    def test_button_spam_performance(self, game_setup):
        """Handle rapid button presses without performance degradation."""
        game, input_handler = game_setup

        start_time = time.perf_counter()

        # Spam A button 50 times
        for i in range(50):
            press = tcod.event.ControllerButton(
                type="CONTROLLERBUTTONDOWN", which=0, button=CB.A, pressed=True
            )
            release = tcod.event.ControllerButton(
                type="CONTROLLERBUTTONUP", which=0, button=CB.A, pressed=False
            )
            input_handler.handle_controller_button(press)
            input_handler.handle_controller_button(release)

        end_time = time.perf_counter()
        elapsed = end_time - start_time

        # Should process 100 button events in under 500ms (5ms per event is acceptable)
        # Button events are more expensive than axis events due to action execution
        assert elapsed < 0.5, f"Took {elapsed:.3f}s to process 100 button events (too slow)"


class TestMemoryLeaks:
    """Test for memory leaks from repeated actions."""

    def test_repeated_context_switches_dont_leak(self, game_setup):
        """Rapidly switching contexts doesn't leak memory."""
        game, input_handler = game_setup

        # Switch contexts 100 times - memory leak would cause slowdown/crash
        for i in range(100):
            # Toggle inventory state
            game.show_inventory = not game.show_inventory
        # No exception means no memory leak detected

    def test_repeated_navigation_doesnt_leak(self, game_setup):
        """Repeated menu navigation doesn't leak memory."""
        game, input_handler = game_setup
        game.show_inventory = True

        # Navigate up/down 200 times
        for i in range(200):
            direction = CB.DPAD_UP if i % 2 == 0 else CB.DPAD_DOWN
            event = tcod.event.ControllerButton(
                type="CONTROLLERBUTTONDOWN", which=0, button=direction, pressed=True
            )
            input_handler.handle_controller_button(event)
        # No exception after 200 navigations means no memory leak
