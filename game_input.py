"""
Rogue Signal Protocol - Game Input Module

Main input dispatcher and router for all player interactions.
Delegates to specialized handlers based on game state priority:
  1. Achievement popups (highest priority)
  2. Active dialogues
  3. Game over/death state
  4. Modal screens (help, inventory, look mode, targeting, lore, achievements)
  5. Normal gameplay (movement, exploits, UI interactions)

Architecture:
  - InputHandler: Main router that delegates to specialized handlers
  - InputMappings: Shared key definitions (movement, exploits)
  - Specialized handlers (imported from submodules):
    * DialogueInputManager: Dialogue confirmations and interactions
    * GameplayInputHandler: Movement, exploits, UI buttons, auto-walk
    * InventoryInputHandler: Inventory screen navigation and item use
    * LookModeInputHandler: Look mode cursor and examination
    * TargetingInputHandler: Targeting mode for exploits
    * AchievementsInputHandler: Achievement screen browsing
    * InputCoordinateConverter: Pixel-to-world coordinate conversion

This module provides the high-level routing logic while delegating
specific input handling to focused, testable submodules.
"""

import tcod
import tcod.event

from game_config import GameConfig
from game_coordinate_helpers import CoordinateHelpers
from game_input_coordinates import InputCoordinateConverter
from game_input_dialogue import DialogueInputManager
from game_input_gameplay import GameplayInputHandler
from game_input_modals import (
    AchievementsInputHandler,
    InventoryInputHandler,
    LookModeInputHandler,
    TargetingInputHandler,
)
from game_ui import UniversalInputHandler


class InputMappings:
    """Shared input mapping definitions to avoid duplication."""

    # Standard movement mapping for all input contexts
    MOVEMENT_MAP = {
        # WASD + QEZC (original)
        tcod.event.KeySym.W: (0, -1),
        tcod.event.KeySym.Q: (-1, -1),
        tcod.event.KeySym.E: (1, -1),
        tcod.event.KeySym.D: (1, 0),
        tcod.event.KeySym.C: (1, 1),
        tcod.event.KeySym.S: (0, 1),
        tcod.event.KeySym.Z: (-1, 1),
        tcod.event.KeySym.A: (-1, 0),
        # Arrow keys
        tcod.event.KeySym.UP: (0, -1),
        tcod.event.KeySym.DOWN: (0, 1),
        tcod.event.KeySym.LEFT: (-1, 0),
        tcod.event.KeySym.RIGHT: (1, 0),
        # Numpad
        tcod.event.KeySym.KP_8: (0, -1),
        tcod.event.KeySym.KP_9: (1, -1),
        tcod.event.KeySym.KP_6: (1, 0),
        tcod.event.KeySym.KP_3: (1, 1),
        tcod.event.KeySym.KP_2: (0, 1),
        tcod.event.KeySym.KP_1: (-1, 1),
        tcod.event.KeySym.KP_4: (-1, 0),
        tcod.event.KeySym.KP_7: (-1, -1),
    }


class InputHandler:
    """Handles all user input and translates it to game actions."""

    def __init__(self, game, renderer=None):
        self.game = game
        self.renderer = renderer  # GameRenderer instance for help screen input
        self.dialogue_manager = DialogueInputManager(game, renderer)
        self.gameplay_handler = GameplayInputHandler(game, renderer, self)
        self.inventory_handler = InventoryInputHandler(game, renderer)
        self.look_mode_handler = LookModeInputHandler(game, renderer)
        self.targeting_handler = TargetingInputHandler(game, renderer)
        self.achievements_handler = AchievementsInputHandler(game, renderer)

    def handle_keydown(self, event: tcod.event.KeyDown) -> bool:
        """Handle keydown events.

        Args:
            event: The keyboard event to process

        Returns:
            True if game should continue, False if should exit
        """
        # Log key event with current state context
        state_context = []
        if self.game.game_over:
            state_context.append("game_over")
        if self.game.dialogue_state.is_active():
            state_context.append("dialogue_active")
        if self.game.show_help:
            state_context.append("help_screen")
        if self.game.show_inventory:
            state_context.append("inventory")
        if self.game.look_mode:
            state_context.append("look_mode")
        if self.game.targeting_mode:
            state_context.append("targeting")

        # Priority 0: Achievement popup (highest priority - must consume input to prevent double-processing)
        if (
            hasattr(self.game, "achievement_popup_manager")
            and self.game.achievement_popup_manager.has_active_popup()
        ):
            self.game.achievement_popup_manager.dismiss_active_popup()
            return True  # Consume the event - don't process further

        # Priority 1: Active dialogue (highest priority overlay)
        # Check this BEFORE game_over to allow death dialogue to be shown
        if self.game.dialogue_state.is_active():
            return self._handle_dialogue_input(event)

        # Dead/game over state - any key should exit to main menu
        # Only reached if no dialogue is active (death dialogue would be active)
        # But also check for pending death dialogue (deferred by one frame for message visibility)
        if self.game.player.cpu <= 0 or self.game.game_over:
            # If death dialogue is pending, wait for it to appear - don't exit yet
            if hasattr(self.game, "pending_death_dialogue") and self.game.pending_death_dialogue:
                return True  # Keep playing until dialogue appears
            # Exit to main menu instead of showing pause menu when dead
            return False

        # Modal screens - handle non-escape keys
        if self.game.show_help:
            # Delegate to help menu's input handler (supports pagination)
            if self.renderer and hasattr(self.renderer, "ui_renderer"):
                help_menu = self.renderer._get_or_create_help_menu()
                result = self.renderer.ui_renderer.handle_help_input(event, help_menu)
                if result == "back":
                    self.game.show_help = False
                    self.renderer.clear_help_menu()  # Clear menu cache
                return True
            else:
                # Fallback: any key closes help
                self.game.show_help = False
                return True

        if self.game.show_lore_viewer:
            # Delegate to lore menu's input handler (same pattern as help)
            if self.renderer and hasattr(self.renderer, "_get_or_create_lore_menu"):
                lore_menu = self.renderer._get_or_create_lore_menu()
                result = lore_menu.handle_input(event)
                if result == "back":
                    self.game.show_lore_viewer = False
                    self.renderer.clear_lore_menu()  # Clear menu cache
                return True
            else:
                # Fallback: ESC closes lore viewer
                if UniversalInputHandler.is_escape_key(event):
                    self.game.show_lore_viewer = False
                return True

        if self.game.show_achievements:
            return self._handle_achievements_input(event)

        if self.game.show_inventory:
            return self._handle_inventory_input(event)

        if self.game.look_mode:
            return self._handle_look_mode_input(event)

        if self.game.targeting_mode:
            return self._handle_targeting_input(event)

        # Normal gameplay
        return self._handle_gameplay_input(event)

    def _handle_escape(self) -> bool:
        """Handle escape key for UI states."""
        g = self.game
        if g.show_lore_viewer:
            g.show_lore_viewer, g.lore_viewer_mode, g.lore_viewer_selection = False, "list", 0
        elif g.show_help:
            g.show_help = False
            if self.renderer and hasattr(self.renderer, "ui_renderer"):
                self.renderer.clear_help_menu()  # Clear menu cache
        elif g.show_achievements:
            g.show_achievements = False
        elif g.show_inventory:
            g.show_inventory = False
        elif g.look_mode:
            g.look_mode = False
            g.message_log.add_message("Look mode exited")
        elif g.targeting_mode:
            g.targeting_mode, g.targeting_exploit = False, None
            g.message_log.add_message("Targeting cancelled")
        return True

    def _handle_dialogue_input(self, event) -> bool:
        """Handle input when a dialogue is active."""
        return self.dialogue_manager.handle_dialogue_input(event)

    def _handle_dialogue_confirm(self) -> None:
        """Handle dialogue confirmation - delegated to DialogueInputManager."""
        return self.dialogue_manager.handle_confirm()

    def _handle_dialogue_dismiss(self) -> bool:
        """Handle dialogue dismissal - delegated to DialogueInputManager."""
        return self.dialogue_manager.handle_dismiss()

    def _handle_dialogue_dont_show_again(self) -> None:
        """Handle 'don't show again' - delegated to DialogueInputManager."""
        return self.dialogue_manager.handle_dont_show_again()

    def _perform_debug_export(self) -> None:
        """Perform debug package export - delegated to DialogueInputManager."""
        return self.dialogue_manager._perform_debug_export()

    def _handle_inventory_input(self, event) -> bool:
        """Handle input while inventory is open - delegated to InventoryInputHandler."""
        return self.inventory_handler.handle_input(event)

    def _handle_achievements_input(self, event) -> bool:
        """Handle input while achievements screen is open - delegated to AchievementsInputHandler."""
        return self.achievements_handler.handle_input(event)

    def _navigate_list(self, current_index, list_length, direction):
        """Generic list navigation helper."""
        if list_length > 0:
            if direction == -1:
                return max(0, current_index - 1)
            else:
                return min(list_length - 1, current_index + 1)
        return current_index

    def _handle_targeting_input(self, event) -> bool:
        """Handle input while in targeting mode - delegated to TargetingInputHandler."""
        return self.targeting_handler.handle_input(event)

    def _handle_gameplay_input(self, event) -> bool:
        """Handle input during normal gameplay - delegated to GameplayInputHandler."""
        return self.gameplay_handler.handle_input(event)

    def _navigate_inventory(self, direction: int):
        """Navigate inventory selection - delegated to InventoryInputHandler."""
        self.inventory_handler.navigate(direction)

    def _use_selected_inventory_item(self):
        """Use the currently selected item - delegated to InventoryInputHandler."""
        self.inventory_handler.use_selected_item()

    def _open_inventory(self):
        """Open the inventory screen - delegated to InventoryInputHandler."""
        self.game.sound_manager.play_sound("ui_menu_open")
        self.inventory_handler.open_inventory()

    def _use_exploit_slot(self, slot: int):
        """Use exploit in specified slot - delegated to GameplayInputHandler."""
        self.gameplay_handler.use_exploit_slot(slot)

    def _enter_look_mode(self):
        """Enter look mode - delegated to LookModeInputHandler."""
        # Reset mouse throttle timer for responsive first movement
        self.game.look_mode_mouse_last_update = 0.0
        self.game.sound_manager.play_sound("ui_menu_open")
        self.look_mode_handler.enter_look_mode()

    def _trigger_debug_export(self):
        """Trigger debug package export with confirmation dialog."""
        import tcod.event

        from game_dialogue_system import DialogueBox
        from game_entities import Colors

        # Create confirmation dialogue
        message = (
            "This will create a debug package containing:\n"
            "- Your save files and settings\n"
            "- Game logs and metrics\n"
            "- System information\n"
            "\n"
            "This package can help developers fix bugs.\n"
            "Package will be saved to: debug_exports/\n"
            "\n"
            "Continue?"
        )

        dialogue = DialogueBox(
            title="Export Debug Package",
            message=message,
            options=["[Y] Yes", "[N] No"],
            valid_keys=[tcod.event.KeySym.Y, tcod.event.KeySym.N, tcod.event.KeySym.ESCAPE],
            title_color=Colors.YELLOW,
            message_color=Colors.WHITE,
            border_color=Colors.YELLOW,
            bg_color=Colors.BLACK,
            format_data={},
            priority=5,
        )

        # Show dialogue
        self.game.dialogue_state.show(dialogue)

        # Store callback for when user confirms
        self.game._pending_debug_export = True

    def _handle_look_mode_input(self, event) -> bool:
        """Handle input while in look mode - delegated to LookModeInputHandler."""
        return self.look_mode_handler.handle_input(event)

    # ============================================================================
    # MOUSE EVENT HANDLERS
    # ============================================================================

    def handle_mouse_motion(self, event: tcod.event.MouseMotion) -> bool:
        """Handle mouse motion events.

        Args:
            event: The mouse motion event with tile coordinates

        Returns:
            True if event was handled, False otherwise
        """
        # After context.convert_event(), position contains TILE coordinates
        if not hasattr(event, "position") or event.position is None:
            return False

        # event.position contains RAW PIXEL coordinates from SDL
        # Handlers will convert to appropriate coordinate system (console or sprite grid)
        pixel_x = event.position.x
        pixel_y = event.position.y

        # Convert to console tile coordinates and store for hover effects
        window_width, window_height = InputCoordinateConverter.get_window_dimensions(
            self.renderer, self.game
        )
        tile_x, tile_y = CoordinateHelpers.pixel_to_char_coords(
            pixel_x, pixel_y, window_width, window_height
        )
        self.game.last_mouse_tile_x = tile_x
        self.game.last_mouse_tile_y = tile_y

        # Dispatch to state-specific handlers
        # Check dialogue FIRST (highest priority overlay)
        if self.game.dialogue_state.is_active():
            return self._handle_dialogue_mouse_motion(event)
        elif self.game.look_mode:
            return self._handle_look_mode_mouse_motion(event)
        elif self.game.targeting_mode:
            return self._handle_targeting_mouse_motion(event)
        elif self.game.show_inventory:
            return self._handle_inventory_mouse_motion(event)
        elif self.game.show_lore_viewer:
            # Delegate to lore menu's mouse handler
            if self.renderer and hasattr(self.renderer, "_get_or_create_lore_menu"):
                lore_menu = self.renderer._get_or_create_lore_menu()
                return lore_menu.handle_mouse_motion(event)
            return False

        # Normal gameplay: update hover position for visual feedback
        return self._handle_gameplay_mouse_motion(event)

    def handle_mouse_click(self, event: tcod.event.MouseButtonDown) -> bool:
        """Handle mouse click events.

        Args:
            event: The mouse click event with tile coordinates

        Returns:
            True if event was handled, False otherwise
        """
        # event.position contains RAW PIXEL coordinates from SDL
        # Handlers will convert to appropriate coordinate system (console or sprite grid)
        if not hasattr(event, "position") or event.position is None:
            return False

        # Dispatch to state-specific handlers based on button
        # Use MouseButton enum (not deprecated BUTTON_* constants)
        if event.button == tcod.event.MouseButton.LEFT:
            result = self._handle_left_click(event)
            return result
        elif event.button == tcod.event.MouseButton.RIGHT:
            result = self._handle_right_click(event)
            return result

        return False

    def handle_mouse_wheel(self, event: tcod.event.MouseWheel) -> bool:
        """Handle mouse wheel events.

        Args:
            event: The mouse wheel event

        Returns:
            True if event was handled, False otherwise
        """
        # Dispatch to state-specific handlers
        if self.game.show_inventory:
            return self._handle_inventory_mouse_wheel(event)
        elif self.game.show_lore_viewer:
            # Delegate to lore menu's wheel handler
            if self.renderer and hasattr(self.renderer, "_get_or_create_lore_menu"):
                lore_menu = self.renderer._get_or_create_lore_menu()
                return lore_menu.handle_mouse_wheel(event)
            return False

        return False

    def _is_valid_mouse_tile(self, tile_x: int, tile_y: int) -> bool:
        """Check if mouse tile coordinates are within valid screen bounds.

        Args:
            tile_x: Console X coordinate (0-79)
            tile_y: Console Y coordinate (0-49)

        Returns:
            True if coordinates are valid, False otherwise
        """

        return 0 <= tile_x < GameConfig.SCREEN_WIDTH and 0 <= tile_y < GameConfig.SCREEN_HEIGHT

    # ============================================================================
    # GAMEPLAY MOUSE HANDLERS (Phase 2)
    # ============================================================================

    def _handle_look_mode_mouse_motion(self, event: tcod.event.MouseMotion) -> bool:
        """Handle mouse motion in look mode - delegated to LookModeInputHandler."""
        return self.look_mode_handler.handle_mouse_motion(event)

    def _handle_targeting_mouse_motion(self, event: tcod.event.MouseMotion) -> bool:
        """Handle mouse motion in targeting mode - delegated to TargetingInputHandler."""
        return self.targeting_handler.handle_mouse_motion(event)

    def _handle_gameplay_mouse_motion(self, event: tcod.event.MouseMotion) -> bool:
        """Handle mouse motion in normal gameplay - delegated to GameplayInputHandler."""
        return self.gameplay_handler.handle_mouse_motion(event)

    def _handle_left_click(self, event: tcod.event.MouseButtonDown) -> bool:
        """Handle left mouse click based on current game state."""
        # Priority 0: Achievement popup (highest - must consume to prevent double-processing)
        if (
            hasattr(self.game, "achievement_popup_manager")
            and self.game.achievement_popup_manager.has_active_popup()
        ):
            self.game.achievement_popup_manager.dismiss_active_popup()
            return True  # Consume the event - don't process further

        # Priority: dialogue > look mode > targeting > gameplay
        if self.game.dialogue_state.is_active():
            return self._handle_dialogue_left_click(event)
        elif self.game.look_mode:
            return self._handle_look_mode_left_click(event)
        elif self.game.targeting_mode:
            return self._handle_targeting_left_click(event)
        elif self.game.show_inventory:
            return self._handle_inventory_left_click(event)
        elif self.game.show_lore_viewer:
            # Delegate to lore menu's click handler
            if self.renderer and hasattr(self.renderer, "_get_or_create_lore_menu"):
                lore_menu = self.renderer._get_or_create_lore_menu()
                result = lore_menu.handle_mouse_click(event)
                if result == "back":
                    self.game.show_lore_viewer = False
                    self.renderer.clear_lore_menu()
                return True
            return False

        # Check for UI button clicks (normal gameplay only)
        # These need to be checked before gameplay movement to intercept UI clicks
        if self._handle_inv_button_click(event):
            return True
        if self._handle_exploit_bar_click(event):
            return True

        # Gameplay: click adjacent tile to move
        return self._handle_gameplay_left_click(event)

    def _handle_right_click(self, event: tcod.event.MouseButtonDown) -> bool:
        """Handle right mouse click - universal cancel/close for in-game modals."""
        # Priority order: Handle most specific states first
        if self.game.targeting_mode:
            self.game.targeting_mode = False
            self.game.targeting_exploit = None
            self.game.message_log.add_message("Targeting cancelled")
            return True
        elif self.game.look_mode:
            self.game.look_mode = False
            self.game.message_log.add_message("Look mode exited")
            return True
        elif self.game.show_inventory:
            self.game.show_inventory = False
            return True
        elif self.game.show_lore_viewer:
            if self.game.lore_viewer_mode == "reading":
                # In reading mode, go back to list
                self.game.lore_viewer_mode = "list"
            else:
                # In list mode, close entirely
                self.game.show_lore_viewer = False
                self.game.lore_viewer_mode = "list"
                self.game.lore_viewer_selection = 0
            return True
        elif self.game.show_achievements:
            self.game.show_achievements = False
            return True
        elif self.game.show_help:
            self.game.show_help = False
            if self.renderer and hasattr(self.renderer, "clear_help_menu"):
                self.renderer.clear_help_menu()
            return True
        else:
            # Normal gameplay - consume the event to prevent any default behavior
            # Right-click during normal gameplay does nothing (safe!)
            return True

    def _handle_look_mode_left_click(self, event: tcod.event.MouseButtonDown) -> bool:
        """Handle left click in look mode - delegated to LookModeInputHandler."""
        return self.look_mode_handler.handle_left_click(event)

    def _handle_targeting_left_click(self, event: tcod.event.MouseButtonDown) -> bool:
        """Handle left click in targeting mode - delegated to TargetingInputHandler."""
        return self.targeting_handler.handle_left_click(event)

    def _handle_inv_button_click(self, event: tcod.event.MouseButtonDown) -> bool:
        """Handle left click on Inv button - delegated to GameplayInputHandler."""
        return self.gameplay_handler.handle_inv_button_click(event)

    def _handle_exploit_bar_click(self, event: tcod.event.MouseButtonDown) -> bool:
        """Handle left click on exploit bar - delegated to GameplayInputHandler."""
        return self.gameplay_handler.handle_exploit_bar_click(event)

    def _handle_gameplay_left_click(self, event: tcod.event.MouseButtonDown) -> bool:
        """Handle left click during gameplay - delegated to GameplayInputHandler."""
        return self.gameplay_handler.handle_left_click(event)

    # ============================================================================
    # MENU MOUSE HANDLERS (Phase 3) - Stubs for now
    # ============================================================================

    def _handle_dialogue_mouse_motion(self, event: tcod.event.MouseMotion) -> bool:
        """Handle mouse motion over dialogue - delegated to DialogueInputManager."""
        return self.dialogue_manager.handle_dialogue_mouse_motion(event)

    def _handle_dialogue_left_click(self, event: tcod.event.MouseButtonDown) -> bool:
        """Handle left click on dialogue buttons - delegated to DialogueInputManager."""
        return self.dialogue_manager.handle_dialogue_left_click(event)

    def _handle_inventory_mouse_motion(self, event: tcod.event.MouseMotion) -> bool:
        """Handle mouse motion in inventory - update selection on hover.

        Uses renderer's single source of truth for coordinate mapping.
        """
        from game_rendering_ui import UIRenderer

        # Convert pixel coordinates to console tile coordinates
        # Try to get context from renderer first, then game
        context = None
        if self.renderer and hasattr(self.renderer, "context"):
            context = self.renderer.context
        elif hasattr(self.game, "context"):
            context = self.game.context
        if context and hasattr(context, "sdl_window"):
            window_w, window_h = context.sdl_window.size
        else:
            window_w, window_h = (800, 600)

        tile_x, tile_y = CoordinateHelpers.pixel_to_char_coords(
            event.position.x, event.position.y, window_w, window_h
        )

        # Store mouse position for tooltip rendering
        self.game.mouse_tile_pos = (tile_x, tile_y)

        # Use renderer's click detection (single source of truth)
        selection_index = UIRenderer.get_inventory_item_at_click(tile_y)

        if selection_index is not None:
            # Update selection to hovered item
            self.game.inventory_selection = selection_index
            return True

        return False

    def _handle_inventory_left_click(self, event: tcod.event.MouseButtonDown) -> bool:
        """Handle left click in inventory - select and use item.

        Uses renderer's single source of truth for coordinate mapping.
        """
        from game_rendering_ui import UIRenderer

        # Convert pixel coordinates to console tile coordinates
        # Try to get context from renderer first, then game
        context = None
        if self.renderer and hasattr(self.renderer, "context"):
            context = self.renderer.context
        elif hasattr(self.game, "context"):
            context = self.game.context
        if context and hasattr(context, "sdl_window"):
            window_w, window_h = context.sdl_window.size
        else:
            window_w, window_h = (800, 600)

        _, tile_y = CoordinateHelpers.pixel_to_char_coords(
            event.position.x, event.position.y, window_w, window_h
        )

        # Use renderer's click detection (single source of truth)
        selection_index = UIRenderer.get_inventory_item_at_click(tile_y)

        if selection_index is not None:
            # Select and use the clicked item (same as pressing Enter)
            self.game.inventory_selection = selection_index
            self._use_selected_inventory_item()
            return True

        # Return True even for blank space clicks - we're in inventory mode,
        # so all clicks should be consumed. Returning False would cause
        # game_loop to misinterpret this as a death dialogue dismissal.
        return True

    def _handle_inventory_mouse_wheel(self, event: tcod.event.MouseWheel) -> bool:
        """Handle mouse wheel in inventory - scroll items."""
        # Scroll up/down based on wheel direction
        if event.y > 0:
            # Scroll up
            self.game.inventory_scroll_offset = max(0, self.game.inventory_scroll_offset - 1)
            return True
        elif event.y < 0:
            # Scroll down
            # Maximum scroll is total_lines - visible_height
            # We'll let the scroll manager handle clamping in the render function
            self.game.inventory_scroll_offset += 1
            return True

        return False
