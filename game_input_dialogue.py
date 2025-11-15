"""
game_input_dialogue.py - Dialogue Input Management

Handles all dialogue-related input processing including:
- Keyboard input (Y/N/D/ESC keys)
- Mouse clicks on dialogue buttons
- Mouse hover feedback
- Dialogue-specific actions (confirm, dismiss, disable)

This module was extracted from game_input.py to provide focused,
maintainable dialogue interaction logic.
"""

import logging

import tcod.event

from game_config import GameConfig
from game_coordinate_helpers import CoordinateHelpers
from game_input_coordinates import InputCoordinateConverter


class DialogueInputManager:
    """Handles dialogue input and confirmation flows."""

    def __init__(self, game, renderer=None):
        """
        Initialize dialogue input manager.

        Args:
            game: Game instance
            renderer: Optional GameRenderer instance for mouse coordinate conversion
        """
        self.game = game
        self.renderer = renderer

    def handle_dialogue_input(self, event: tcod.event.KeyDown) -> bool:
        """
        Main dialogue input dispatcher for keyboard events.

        Args:
            event: The keyboard event to process

        Returns:
            True if event was handled
        """
        from game_dialogue_system import DialogueInputHandler

        dialogue = self.game.dialogue_state.get_active()
        if not dialogue:
            return True

        # Use DialogueInputHandler to process input
        action = DialogueInputHandler.handle_input(dialogue, event.sym)

        # If dialogue handled the input, process it
        if action is not None:
            if action == "confirm":
                self.handle_confirm()
                return True
            elif action in ["cancel", "dismiss"]:
                should_continue = self.handle_dismiss()
                return should_continue
            elif action == "dont_show_again":
                self.handle_dont_show_again()
                return True

        # Dialogue is active - don't process other inputs
        return True

    def handle_confirm(self) -> None:
        """Handle dialogue confirmation (user pressed Y or clicked confirm button)."""
        dialogue = self.game.dialogue_state.get_active()
        if not dialogue:
            return

        # Check dialogue type by title (since we're using DialogueBox now)
        if "Export Debug Package" in dialogue.title:
            # User confirmed debug export
            self._perform_debug_export()
            self.game._pending_debug_export = False
        elif "OVERCLOCK WARNING" in dialogue.title:
            # Player confirmed overclock - re-execute the pending exploit
            self.game.overclock_confirmation = True
            # Re-execute the exploit that was cancelled
            if self.game.overclock_exploit and self.game.cursor_position:
                # Use stored cursor position (from targeting mode or direct execute_exploit call)
                self.game.exploit_system.execute_exploit(
                    self.game.overclock_exploit, self.game.cursor_position
                )
            elif self.game.overclock_exploit:
                # No cursor position - use player position (untargeted exploits)
                self.game.exploit_system.execute_exploit(
                    self.game.overclock_exploit, self.game.player.position
                )
        elif "FRIENDLY FIRE WARNING" in dialogue.title:
            # Player confirmed friendly fire - execute the pending exploit
            self.game.friendly_fire_confirmed = True
            # Re-execute the exploit that was cancelled
            if self.game.friendly_fire_exploit and self.game.friendly_fire_target:
                self.game.exploit_system.execute_exploit(
                    self.game.friendly_fire_exploit, self.game.friendly_fire_target
                )
        elif "SYSTEM CRASH" in dialogue.title:
            # Player confirmed System Crash - re-execute
            self.game.system_crash_confirmed = True
            # Re-execute System Crash
            self.game.exploit_system.execute_exploit("system_crash", self.game.player.position)
        elif "GATEWAY" in dialogue.title:
            # Player confirmed gateway - proceed to next level
            self.game.sound_manager.play_sound("level_complete")
            self.game.message_log.add_message("Gateway reached! Next network...")
            self.game.next_level()

        # Close dialogue
        self.game.dialogue_state.close()

    def handle_dismiss(self) -> bool:
        """
        Handle dialogue dismissal/cancellation (user pressed N/ESC or clicked cancel).

        Returns:
            True if game should continue, False if should exit to menu
        """
        dialogue = self.game.dialogue_state.get_active()
        if not dialogue:
            return True

        # Check dialogue type by title
        if "Export Debug Package" in dialogue.title:
            # User cancelled debug export
            self.game.message_log.add_message("Debug export cancelled")
            if hasattr(self.game, "_pending_debug_export"):
                self.game._pending_debug_export = False
        elif "UNDER ATTACK" in dialogue.title:
            # Close inventory when under attack (can't stay in inventory while being attacked)
            self.game.show_inventory = False
        elif "OVERCLOCK WARNING" in dialogue.title:
            # Cancel exploit use - just close dialogue
            pass
        elif "GATEWAY" in dialogue.title:
            # Player cancelled gateway
            self.game.message_log.add_message("Staying in current network")
        elif (
            "PURGED" in dialogue.title
            or "BREAKTHROUGH" in dialogue.title
            or "ROGUE SIGNAL ESTABLISHED" in dialogue.title
        ):
            # Death/victory messages - any key closes and returns to menu
            self.game.dialogue_state.close()
            return False  # Exit to main menu

        # Close dialogue
        self.game.dialogue_state.close()
        return True  # Continue game

    def handle_dont_show_again(self) -> None:
        """Handle 'don't show this again' option (user pressed D)."""
        from game_entities import Colors

        dialogue = self.game.dialogue_state.get_active()
        if not dialogue or not dialogue.user_pref_key:
            return

        # Disable this dialogue type
        self.game.dialogue_state.disable_dialogue(dialogue.user_pref_key)

        # Add message to log
        self.game.message_log.add_message(
            "Dialogue disabled. Re-enable in Settings if needed.", Colors.YELLOW
        )

        # For overclock and system crash warnings, pressing D should still execute the exploit
        if "OVERCLOCK WARNING" in dialogue.title or "SYSTEM CRASH" in dialogue.title:
            self.handle_confirm()
        else:
            self.game.dialogue_state.close()

    def handle_dialogue_mouse_motion(self, event: tcod.event.MouseMotion) -> bool:
        """
        Handle mouse motion over dialogue - provide visual feedback for hovering.

        Uses stored coordinates from last render to avoid recalculating dimensions.
        Future: Could add visual hover highlighting.

        Args:
            event: Mouse motion event

        Returns:
            True if hovering over dialogue option, False otherwise
        """
        dialogue = self.game.dialogue_state.get_active()
        if not dialogue:
            return False

        # Use coordinates from last render (don't recalculate!)
        if not self.game.dialogue_state.last_render_coords:
            return False  # Not rendered yet

        coords = self.game.dialogue_state.last_render_coords

        # Convert pixel coordinates to console tile coordinates
        window_w, window_h = InputCoordinateConverter.get_window_dimensions(
            self.renderer, self.game
        )
        tile_x, tile_y = CoordinateHelpers.pixel_to_char_coords(
            event.position.x, event.position.y, window_w, window_h
        )

        # Check if hovering over dialogue box
        if not (
            coords["box_x"] <= tile_x < coords["box_x"] + coords["box_width"]
            and coords["box_y"] <= tile_y < coords["box_y"] + coords["box_height"]
        ):
            return False  # Not hovering over dialogue

        # Check if hovering over the options row
        if tile_y != coords["options_y"]:
            return False  # Not hovering over options

        # Use get_option_at_click to determine which option is being hovered
        # (reuses the same click detection logic for consistency)
        from game_dialogue_system import UnifiedRenderer

        hovered_option = UnifiedRenderer.get_option_at_click(
            self.game.dialogue_state, tile_x, tile_y
        )

        if hovered_option is not None:
            # Future: Could set a hover state here that the renderer uses to highlight the option
            return True

        return False

    def handle_dialogue_left_click(self, event: tcod.event.MouseButtonDown) -> bool:
        """
        Handle left click on dialogue buttons.

        Dialogues have clickable option buttons like [Y] Confirm, [N] Cancel.
        We need to check if the click is within the dialogue box and on an option.

        Args:
            event: Mouse button down event

        Returns:
            True if click was handled, or should_continue value for death/victory dialogues
        """
        from game_dialogue_system import DialogueInputHandler, UnifiedRenderer

        dialogue = self.game.dialogue_state.get_active()
        if not dialogue:
            return False

        # Convert pixel coordinates to console tile coordinates
        # Get context for window size
        context = None
        if self.renderer and hasattr(self.renderer, "context"):
            context = self.renderer.context
        elif hasattr(self.game, "context"):
            context = self.game.context

        # Get window dimensions
        if context and hasattr(context, "sdl_window"):
            window_w, window_h = context.sdl_window.size
        else:
            window_w, window_h = (800, 600)

        # Simple conversion: pixels / (window_size / console_size)
        pixels_per_tile_x = window_w / GameConfig.SCREEN_WIDTH  # 80
        pixels_per_tile_y = window_h / GameConfig.SCREEN_HEIGHT  # 50

        tile_x = int(event.position.x / pixels_per_tile_x)
        tile_y = int(event.position.y / pixels_per_tile_y)

        # Clamp to valid range
        tile_x = max(0, min(GameConfig.SCREEN_WIDTH - 1, tile_x))
        tile_y = max(0, min(GameConfig.SCREEN_HEIGHT - 1, tile_y))

        # Ask the dialogue renderer which option (if any) was clicked
        # This is the single source of truth - no duplicated calculations!
        option_index = UnifiedRenderer.get_option_at_click(self.game.dialogue_state, tile_x, tile_y)

        # Determine action based on which option was clicked
        if option_index is not None:
            # Clicked on a specific option - use that option's key
            action = DialogueInputHandler.handle_input(dialogue, dialogue.valid_keys[option_index])
        else:
            # Clicked anywhere else (not on a button)
            # For death/victory dialogues, don't allow click-to-dismiss (prevent accidental exits)
            if (
                "PURGED" in dialogue.title
                or "BREAKTHROUGH" in dialogue.title
                or "ROGUE SIGNAL ESTABLISHED" in dialogue.title
            ):
                # Ignore clicks outside buttons for death/victory dialogues
                return True
            # Other dialogues: use first/default option (allows click-to-dismiss)
            action = DialogueInputHandler.handle_input(dialogue, dialogue.valid_keys[0])

        # Process the action (same logic as keyboard input)
        if action == "confirm":
            self.handle_confirm()
            return True
        elif action in ["cancel", "dismiss"]:
            should_continue = self.handle_dismiss()
            # For death/victory dialogues, should_continue will be False
            # We need to signal this to the game loop to exit to menu
            # Return the actual value instead of always True
            return should_continue
        elif action == "dont_show_again":
            self.handle_dont_show_again()
            return True

        return True  # Event was handled

    def _perform_debug_export(self) -> None:
        """Actually perform the debug package export."""
        from debug_export import export_debug_package
        from game_entities import Colors

        logging.info("Debug Export: Starting debug package creation")
        self.game.message_log.add_message("Creating debug package...", Colors.YELLOW)

        try:
            # Create the debug package
            zip_path = export_debug_package(game_engine=self.game)

            if zip_path:
                # Success!
                filename = zip_path.name
                self.game.message_log.add_message(
                    f"Debug package created: {filename}", Colors.GREEN
                )
                # Show exact path so user knows where to find it
                self.game.message_log.add_message(f"Location: {zip_path.parent}", Colors.CYAN)
                self.game.message_log.add_message(
                    "Report to: github.com/Dragynrain/RogueSignalProtocol", Colors.YELLOW
                )
                logging.info(f"Debug Export: Success - {zip_path}")
            else:
                # Failed
                self.game.message_log.add_message("Failed to create debug package", Colors.RED)
                logging.error("Debug Export: Failed - export_debug_package returned None")
        except Exception as e:
            # Error
            self.game.message_log.add_message(f"Debug export error: {str(e)}", Colors.RED)
            logging.error(f"Debug Export: Error - {e}", exc_info=True)
