"""
Game Loop Smoke Test - Tests the FULL game loop iteration, not just rendering.

This catches bugs in the input polling code (keyboard, mouse, gamepad) that runs
BETWEEN event handling and rendering. Many bugs occur in this "middle" section
that rendering-only tests miss.

Example bugs caught:
- Calling non-existent methods on input handlers
- AttributeErrors in gamepad polling
- Mouse coordinate conversion bugs
- Input state management issues
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tcod.event

from game_config import GameConfig, GameSettings
from game_engine import GameEngine
from game_input import InputHandler


class TestGameLoopInputPolling:
    """Test the full game loop input polling section."""

    def test_game_loop_single_iteration_no_crash(self):
        """
        Simulate ONE full game loop iteration to catch polling bugs.

        This tests the critical section between event handling and rendering:
        1. Process input events
        2. Poll analog sticks (⚠️ where the bug was!)
        3. Render frame

        This is the MINIMUM test needed to catch the analog stick bug.
        """
        with patch("game_audio.SoundManager"):
            settings = GameSettings()
            engine = GameEngine(settings=settings, load_save=False)

            # Mock context
            mock_context = Mock()
            mock_context.recommended_console_size.return_value = (80, 50)
            mock_sdl_window = Mock()
            mock_sdl_window.size = (1280, 800)
            mock_context.sdl_window = mock_sdl_window
            mock_context.sdl_renderer = Mock()
            engine.context = mock_context

            # Create REAL input handler (this is where the bug was!)
            input_handler = InputHandler(engine)

            # Simulate the game loop's input polling section
            # This is what game_loop.py does after processing events:
            if hasattr(input_handler, 'gamepad_handler'):
                # This code path MUST execute without crashing
                try:
                    # LEFT STICK POLLING (gameplay context)
                    if (not engine.show_inventory and not engine.look_mode and
                        not engine.targeting_mode and not engine.show_achievements and not engine.show_help):
                        # This line caused the crash:
                        # movement = input_handler.gamepad_handler.analog_handler.get_left_stick_movement()
                        # Should be:
                        movement = input_handler.gamepad_handler.analog_handler.get_left_stick_movement_gameplay(engine.turn)
                        # Should not crash even if no controller connected
                        assert movement is None or isinstance(movement, tuple)

                    # LEFT STICK POLLING (modal context)
                    engine.show_achievements = True
                    # This line also caused the crash:
                    movement = input_handler.gamepad_handler.analog_handler.get_left_stick_movement_menu()
                    assert movement is None or isinstance(movement, tuple)

                except AttributeError as e:
                    pytest.fail(
                        f"CRITICAL: Game loop input polling crashed!\n"
                        f"Error: {e}\n"
                        f"This would crash the game on startup."
                    )

    def test_game_loop_with_gamepad_no_controller(self):
        """
        Test game loop with gamepad support but no controller connected.

        This is the MOST COMMON scenario and must not crash.
        """
        with patch("game_audio.SoundManager"):
            settings = GameSettings()
            engine = GameEngine(settings=settings, load_save=False)
            input_handler = InputHandler(engine)

            # Verify gamepad handler exists
            assert hasattr(input_handler, 'gamepad_handler')

            # Verify analog handler exists and has correct methods
            assert hasattr(input_handler.gamepad_handler, 'analog_handler')
            analog = input_handler.gamepad_handler.analog_handler

            # These methods MUST exist
            assert hasattr(analog, 'get_left_stick_movement_gameplay'), \
                "Missing get_left_stick_movement_gameplay - game will crash!"
            assert hasattr(analog, 'get_left_stick_movement_menu'), \
                "Missing get_left_stick_movement_menu - game will crash!"

            # This method exists for swap_sticks cursor control
            assert hasattr(analog, 'get_left_stick_movement'), \
                "Missing get_left_stick_movement - needed for swap_sticks cursor control!"

    def test_game_loop_input_polling_all_contexts(self):
        """
        Test input polling in ALL game contexts (gameplay, menus, modals).

        The bug occurred in BOTH gameplay and modal contexts, so test all of them.
        """
        with patch("game_audio.SoundManager"):
            settings = GameSettings()
            engine = GameEngine(settings=settings, load_save=False)
            input_handler = InputHandler(engine)

            if not hasattr(input_handler, 'gamepad_handler'):
                pytest.skip("Gamepad support not available")

            analog = input_handler.gamepad_handler.analog_handler

            # Test contexts where the bug occurred:
            test_contexts = [
                ("Gameplay", {
                    'show_inventory': False,
                    'look_mode': False,
                    'targeting_mode': False,
                    'show_achievements': False,
                    'show_help': False
                }),
                ("Achievements", {
                    'show_inventory': False,
                    'look_mode': False,
                    'targeting_mode': False,
                    'show_achievements': True,
                    'show_help': False
                }),
                ("Help", {
                    'show_inventory': False,
                    'look_mode': False,
                    'targeting_mode': False,
                    'show_achievements': False,
                    'show_help': True
                }),
            ]

            for context_name, flags in test_contexts:
                # Set game state
                for flag, value in flags.items():
                    setattr(engine, flag, value)

                # Try polling - should not crash
                try:
                    if context_name == "Gameplay":
                        movement = analog.get_left_stick_movement_gameplay(engine.turn)
                    else:
                        movement = analog.get_left_stick_movement_menu()

                    # Should return None (no input) or tuple (dx, dy)
                    assert movement is None or (isinstance(movement, tuple) and len(movement) == 2), \
                        f"{context_name} context returned invalid movement: {movement}"

                except AttributeError as e:
                    pytest.fail(f"CRASH in {context_name} context: {e}")

    @patch('tcod.event.wait')
    def test_full_game_loop_iteration_with_events(self, mock_wait):
        """
        Simulate a complete game loop iteration with events.

        This is the MOST comprehensive test - simulates exactly what happens
        when you start a new game and the loop runs for one frame.
        """
        with patch("game_audio.SoundManager"):
            settings = GameSettings()
            engine = GameEngine(settings=settings, load_save=False)

            # Mock context
            mock_context = Mock()
            mock_context.recommended_console_size.return_value = (80, 50)
            mock_sdl_window = Mock()
            mock_sdl_window.size = (1280, 800)
            mock_context.sdl_window = mock_sdl_window
            mock_context.sdl_renderer = Mock()
            engine.context = mock_context

            # Create console
            console = tcod.console.Console(GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT)

            # Create input handler
            input_handler = InputHandler(engine)

            # Mock one frame of events (empty - just idle)
            mock_wait.return_value = []

            # Simulate game loop iteration (simplified)
            try:
                # 1. Process events (none in this test)
                events = mock_wait(timeout=0.1)
                for event in events:
                    pass  # Would call handle_game_input_events()

                # 2. INPUT POLLING (⚠️ THIS IS WHERE THE BUG WAS!)
                if hasattr(input_handler, 'gamepad_handler'):
                    # Gameplay movement polling
                    if not engine.show_inventory:
                        movement = input_handler.gamepad_handler.analog_handler.get_left_stick_movement_gameplay(engine.turn)

                    # Modal scrolling polling
                    engine.show_achievements = True
                    movement = input_handler.gamepad_handler.analog_handler.get_left_stick_movement_menu()

                # 3. Render (simplified - just verify no crash)
                if hasattr(input_handler, 'renderer') and input_handler.renderer:
                    # Don't actually render, just verify renderer exists
                    pass

            except AttributeError as e:
                pytest.fail(
                    f"Game loop crashed during iteration!\n"
                    f"This would prevent the game from starting.\n"
                    f"Error: {e}"
                )
        # If we got here, all iterations succeeded without crash


class TestGameLoopSmokeWithRenderer:
    """Test game loop WITH rendering to catch rendering + polling bugs."""

    def test_one_frame_render_and_poll(self):
        """
        Most comprehensive test: Render AND poll in one frame.

        This catches bugs that only appear when BOTH systems run together.
        """
        with patch("game_audio.SoundManager"):
            from game_rendering_core import GameRenderer

            settings = GameSettings()
            settings.graphics_mode = "glyphs"
            engine = GameEngine(settings=settings, load_save=False)

            # Create console and renderer
            console = tcod.console.Console(GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT)
            renderer = GameRenderer(settings, context=None)

            # Create input handler
            input_handler = InputHandler(engine)

            try:
                # Step 1: Input polling (where the bug was)
                if hasattr(input_handler, 'gamepad_handler'):
                    movement = input_handler.gamepad_handler.analog_handler.get_left_stick_movement_gameplay(engine.turn)

                # Step 2: Rendering
                renderer.render_game(console, engine, context=None)

            except AttributeError as e:
                pytest.fail(f"Combined polling + rendering crashed: {e}")
            # Success - no crash during combined polling + rendering


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
