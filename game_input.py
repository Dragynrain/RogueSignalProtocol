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
    * AchievementsMenu: Achievement screen (from game_menu_achievements, accessed via renderer)
    * InputCoordinateConverter: Pixel-to-world coordinate conversion

This module provides the high-level routing logic while delegating
specific input handling to focused, testable submodules.
"""

import logging

import tcod
import tcod.event
import tcod.sdl.joystick

from game_config import GameConfig
from game_coordinate_helpers import CoordinateHelpers
from game_input_actions import InputAction, InputContext
from game_input_coordinates import InputCoordinateConverter
from game_input_dialogue import DialogueInputManager
from game_input_gamepad import GamepadInputHandler
from game_input_gameplay import GameplayInputHandler
from game_input_mappings import InputMapper
from game_input_modals import (
    InventoryInputHandler,
    LookModeInputHandler,
    TargetingInputHandler,
)
from game_input_device_tracker import InputDeviceType, set_last_device


class InputHandler:
    """Handles all user input and translates it to game actions."""

    def __init__(self, game, renderer=None, controllers=None):
        self.game = game
        self.renderer = renderer  # GameRenderer instance for help screen input

        # Gamepad support (Phase 2) - create shared InputMapper early
        # InputMapper is stateless (lookup tables only) - shared across all handlers
        # This ensures custom bindings apply consistently everywhere
        self.input_mapper = InputMapper()
        self.gamepad_handler = GamepadInputHandler(self.input_mapper, game, controllers or set())

        # Load custom bindings BEFORE initializing handlers (they'll share this mapper)
        keyboard_bindings = getattr(game.settings, "custom_keyboard_bindings", {}) if hasattr(game, "settings") else {}
        gamepad_bindings = getattr(game.settings, "custom_gamepad_bindings", {}) if hasattr(game, "settings") else {}
        self.input_mapper.load_custom_bindings(keyboard_bindings, gamepad_bindings)

        # Initialize specialized input handlers with SHARED InputMapper AND GamepadHandler
        # Sharing gamepad_handler ensures state (button_held, analog stick, settings) stays in sync
        self.dialogue_manager = DialogueInputManager(game, renderer)
        self.gameplay_handler = GameplayInputHandler(
            game, renderer,
            input_mapper=self.input_mapper,
            controllers=controllers,
            gamepad_handler=self.gamepad_handler
        )
        self.inventory_handler = InventoryInputHandler(
            game, renderer,
            input_mapper=self.input_mapper,
            controllers=controllers,
            gamepad_handler=self.gamepad_handler
        )
        self.look_mode_handler = LookModeInputHandler(
            game, renderer,
            input_mapper=self.input_mapper,
            controllers=controllers,
            gamepad_handler=self.gamepad_handler
        )
        self.targeting_handler = TargetingInputHandler(
            game, renderer,
            input_mapper=self.input_mapper,
            controllers=controllers,
            gamepad_handler=self.gamepad_handler
        )
        # Note: achievements_handler removed - using AchievementsMenu directly (Phase 4)

        # Lore viewer handler (lazy-initialized when first needed)
        self._lore_viewer_menu = None

    def handle_keydown(self, event: tcod.event.KeyDown) -> bool:
        """Handle keydown events.

        Args:
            event: The keyboard event to process

        Returns:
            True if game should continue, False if should exit
        """
        # Track input device for dynamic help text
        set_last_device(InputDeviceType.KEYBOARD)

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
            # Check renderer exists (may be None in headless tests)
            if self.renderer is None:
                # In headless mode, just handle ESC to close help
                if hasattr(event, 'sym') and event.sym == tcod.event.KeySym.ESCAPE:
                    self.game.show_help = False
                return True

            help_menu = self.renderer._get_or_create_help_menu()
            result = self.renderer.ui_renderer.handle_help_input(event, help_menu)
            if result == "back":
                self.game.show_help = False
                self.renderer.clear_help_menu()  # Clear menu cache
            return True

        if self.game.show_lore_viewer:
            # Delegate to lore menu's input handler
            # Check renderer exists (may be None in headless tests)
            if self.renderer is None:
                # In headless mode, just handle ESC to close lore viewer
                if hasattr(event, 'sym') and event.sym == tcod.event.KeySym.ESCAPE:
                    self.game.show_lore_viewer = False
                return True

            lore_menu = self._get_or_create_lore_viewer_menu()
            result = lore_menu.handle_input(event)
            if result == "back":
                self.game.show_lore_viewer = False
                self._lore_viewer_menu = None  # Clear menu cache
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
        """
        Handle input while achievements screen is open.

        Phase 4: Direct usage of AchievementsMenu with str→bool adapter.
        """
        # Get achievements menu from renderer
        if self.renderer and hasattr(self.renderer, "ui_renderer"):
            achievements_menu = (
                self.renderer.ui_renderer._achievements_menu
                if hasattr(self.renderer.ui_renderer, "_achievements_menu")
                else None
            )

            if achievements_menu:
                # Call achievements menu's handle_input (returns str: "back" or "")
                action = achievements_menu.handle_input(event)

                # Adapter: Convert str return to bool behavior
                if action == "back":
                    self.game.show_achievements = False
                    return True
                # Any other action (including "") means event was handled
                return True

        # Fallback if menu not available: ESC or V closes achievements
        if hasattr(event, 'sym'):
            modifier = getattr(event, 'mod', 0)
            action = self.input_mapper.get_action_for_key(event.sym, modifier=modifier)
            if action in (InputAction.CANCEL, InputAction.TOGGLE_ACHIEVEMENTS):
                self.game.show_achievements = False
                return True

        # Unhandled key - consume it and stay in achievements
        return True

    def _handle_targeting_input(self, event) -> bool:
        """Handle input while in targeting mode - delegated to TargetingInputHandler."""
        return self.targeting_handler.handle_input(event)

    def _handle_gameplay_input(self, event) -> bool:
        """Handle input during normal gameplay - delegated to GameplayInputHandler."""
        return self.gameplay_handler.handle_input(event)

    def _use_selected_inventory_item(self):
        """Use the currently selected item - delegated to InventoryInputHandler."""
        self.inventory_handler.use_selected_item()

    def _open_inventory(self):
        """Open the inventory screen - delegated to GameplayInputHandler."""
        self.gameplay_handler.open_inventory()

    def _use_exploit_slot(self, slot: int):
        """Use exploit in specified slot - delegated to GameplayInputHandler."""
        self.gameplay_handler.use_exploit_slot(slot)

    def _enter_look_mode(self):
        """Enter look mode - delegated to GameplayInputHandler."""
        self.gameplay_handler.enter_look_mode()

    def _get_or_create_lore_viewer_menu(self):
        """Get or create the lore viewer menu instance."""
        if self._lore_viewer_menu is None:
            if not self.renderer:
                raise RuntimeError(
                    "Lore viewer requires a renderer but none was provided. "
                    "This is a programming error - lore viewer should not be openable without a renderer."
                )
            from game_menu_help_lore import LoreMenu
            self._lore_viewer_menu = LoreMenu()  # LoreMenu takes no arguments
        return self._lore_viewer_menu

    def _get_current_context(self) -> InputContext:
        """
        Determine current game state context for input handling.

        Context determines which bindings are active (e.g., A button = wait in gameplay,
        confirm in menus). Mirrors existing priority logic in handle_keydown.

        Returns:
            Current InputContext enum value
        """
        # Priority order matches existing game_input.py:113-179 logic
        if (
            hasattr(self.game, "achievement_popup_manager")
            and self.game.achievement_popup_manager.has_active_popup()
        ):
            return InputContext.ACHIEVEMENT_POPUP
        elif self.game.dialogue_state.is_active():
            return InputContext.DIALOGUE
        elif self.game.game_over or self.game.player.cpu <= 0:
            return InputContext.GAME_OVER
        # Targeting and look mode have priority over inventory (for cursor control)
        elif self.game.targeting_mode:
            return InputContext.TARGETING
        elif self.game.look_mode:
            return InputContext.LOOK_MODE
        # Inventory comes after targeting/look mode
        elif self.game.show_inventory:
            return InputContext.INVENTORY
        # Menu contexts (specific menus take priority over main menu)
        elif self.game.show_settings:
            return InputContext.SETTINGS_MENU
        elif self.game.show_about:
            return InputContext.ABOUT_MENU
        elif self.game.show_help:
            return InputContext.HELP
        elif self.game.show_lore_viewer:
            return InputContext.LORE_VIEWER
        elif self.game.show_achievements:
            return InputContext.ACHIEVEMENTS_SCREEN
        # Main menu checked last (less specific)
        elif self.game.show_main_menu:
            return InputContext.MAIN_MENU
        else:
            return InputContext.GAMEPLAY

    def _execute_action(self, action: InputAction) -> bool:
        """
        Execute a game action (from keyboard or gamepad).

        Delegates to existing specialized handlers to avoid duplicating logic.
        Each handler has an execute_action() method added in Phases 3.2-3.3.

        Args:
            action: The InputAction to execute

        Returns:
            True if action was handled, False otherwise
        """
        context = self._get_current_context()

        # Achievement popups dismiss on any input (highest priority)
        if context == InputContext.ACHIEVEMENT_POPUP:
            if (
                hasattr(self.game, "achievement_popup_manager")
                and self.game.achievement_popup_manager.has_active_popup()
            ):
                self.game.achievement_popup_manager.dismiss_active_popup()
                return True  # Consumed by popup dismissal

        # Delegate to existing specialized handlers
        if context == InputContext.GAMEPLAY:
            return self.gameplay_handler.execute_action(action)
        elif context == InputContext.LOOK_MODE:
            return self.look_mode_handler.execute_action(action)
        elif context == InputContext.TARGETING:
            return self.targeting_handler.execute_action(action)
        elif context == InputContext.INVENTORY:
            return self.inventory_handler.execute_action(action)
        # Help menu is now handled directly in handle_controller_button() and handle_keydown()
        # to ensure consistent timing behavior (bypasses action system entirely)
        elif context == InputContext.HELP:
            # Help events are intercepted before reaching _execute_action()
            # This should not be reached for gamepad/keyboard events
            return True
        elif context == InputContext.ACHIEVEMENTS_SCREEN:
            # Simple handler: CANCEL closes achievements
            if action == InputAction.CANCEL:
                self.game.show_achievements = False
                return True
            # Other actions are consumed but ignored
            return True
        elif context == InputContext.LORE_VIEWER:
            # Simple handler: CANCEL closes lore viewer
            if action == InputAction.CANCEL:
                if self.game.lore_viewer_mode == "reading":
                    self.game.lore_viewer_mode = "list"
                else:
                    self.game.show_lore_viewer = False
                    self.game.lore_viewer_mode = "list"
                    self.game.lore_viewer_selection = 0
                return True
            # Other actions are consumed but ignored
            return True
        elif context == InputContext.SETTINGS_MENU:
            # Simple handler: CANCEL closes settings
            if action == InputAction.CANCEL:
                self.game.show_settings = False
                return True
            # Other actions handled by settings menu itself
            return True
        elif context == InputContext.ABOUT_MENU:
            # Simple handler: CANCEL closes about
            if action == InputAction.CANCEL:
                self.game.show_about = False
                return True
            # Other actions are consumed but ignored
            return True
        else:
            logging.warning(
                f"_execute_action: {action.name} in context {context.name} (handler not yet extended) - ignoring action"
            )
            # Return True to continue playing instead of False which would exit to menu
            return True

    def _trigger_debug_export(self):
        """Trigger debug package export - delegated to GameplayInputHandler."""
        self.gameplay_handler.trigger_debug_export()

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
        # event.position contains RAW PIXEL coordinates from SDL (not tile coords)
        if not hasattr(event, "position") or event.position is None:
            return False

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
            lore_menu = self._get_or_create_lore_viewer_menu()
            return lore_menu.handle_mouse_motion(event)

        # Normal gameplay: update hover position for visual feedback
        return self._handle_gameplay_mouse_motion(event)

    def handle_mouse_click(self, event: tcod.event.MouseButtonDown) -> bool:
        """Handle mouse click events.

        Args:
            event: The mouse click event with tile coordinates

        Returns:
            True if event was handled, False otherwise
        """
        # Track input device for dynamic help text (mouse = keyboard mode)
        set_last_device(InputDeviceType.KEYBOARD)

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
        # Track input device for dynamic help text (mouse = keyboard mode)
        set_last_device(InputDeviceType.KEYBOARD)

        # Dispatch to state-specific handlers
        if self.game.show_inventory:
            return self._handle_inventory_mouse_wheel(event)
        elif self.game.show_lore_viewer:
            # Delegate to lore menu's wheel handler
            # Check renderer exists (may be None in headless tests)
            if self.renderer is None:
                return False  # Can't scroll without renderer

            lore_menu = self._get_or_create_lore_viewer_menu()
            return lore_menu.handle_mouse_wheel(event)

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
            lore_menu = self._get_or_create_lore_viewer_menu()
            result = lore_menu.handle_mouse_click(event)
            if result == "back":
                self.game.show_lore_viewer = False
                self._lore_viewer_menu = None  # Clear menu cache
            return True

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
        """Handle mouse motion in inventory - delegated to InventoryInputHandler."""
        return self.inventory_handler.handle_mouse_motion(event)

    def _handle_inventory_left_click(self, event: tcod.event.MouseButtonDown) -> bool:
        """Handle left click in inventory - delegated to InventoryInputHandler."""
        return self.inventory_handler.handle_left_click(event)

    def _handle_inventory_mouse_wheel(self, event: tcod.event.MouseWheel) -> bool:
        """Handle mouse wheel in inventory - delegated to InventoryInputHandler."""
        return self.inventory_handler.handle_mouse_wheel(event)

    # =========================================================================
    # GAMEPAD EVENT HANDLING (Phase 2)
    # =========================================================================

    def handle_controller_device(self, event: tcod.event.ControllerDevice) -> None:
        """
        Handle controller connection/disconnection events.

        Args:
            event: Controller device add/remove event
        """
        self.gamepad_handler.handle_device_event(event)

    def handle_controller_button(self, event: tcod.event.ControllerButton) -> bool | None:
        """
        Handle controller button press/release events.

        Args:
            event: Controller button event

        Returns:
            True: Event was handled
            None: Event not handled, fall through to next handler
            False: Exit to main menu
        """
        # Track input device for dynamic help text
        set_last_device(InputDeviceType.GAMEPAD)

        # Priority check: Achievement popup (must match keyboard handling)
        # This MUST be checked before _get_current_context() to avoid returning False
        if (
            hasattr(self.game, "achievement_popup_manager")
            and self.game.achievement_popup_manager.has_active_popup()
        ):
            # Only dismiss on button press, not release
            if event.pressed:
                self.game.achievement_popup_manager.dismiss_active_popup()
            return True  # Consume the event - don't process further

        # Priority check: Active dialogue (must match keyboard handling)
        if self.game.dialogue_state.is_active():
            return self.dialogue_manager.handle_dialogue_gamepad_input(event)

        # Modal screens - handle directly (matching keyboard event flow)
        # This ensures gamepad uses same timing logic as keyboard
        if self.game.show_help:
            # Headless mode: Allow B button to close help (matches ESC on keyboard)
            if not self.renderer:
                # In headless mode, just handle B button to close help
                if isinstance(event, tcod.event.ControllerButton) and event.pressed and event.button == tcod.sdl.joystick.ControllerButton.B:
                    self.game.show_help = False
                return True

            # Delegate to help menu's input handler (supports pagination with proper timing)
            help_menu = self.renderer._get_or_create_help_menu()
            result = self.renderer.ui_renderer.handle_help_input(event, help_menu)
            if result == "back":
                self.game.show_help = False
                self.renderer.clear_help_menu()  # Clear menu cache
            return True

        # Lore viewer (data fragments) - handle raw events for navigation
        if self.game.show_lore_viewer:
            # Check renderer exists (may be None in headless tests)
            if self.renderer is None:
                # In headless mode, just handle B button to close lore viewer
                if isinstance(event, tcod.event.ControllerButton) and event.pressed and event.button == tcod.sdl.joystick.ControllerButton.B:
                    self.game.show_lore_viewer = False
                return True

            lore_menu = self._get_or_create_lore_viewer_menu()
            result = lore_menu.handle_input(event)
            if result == "back":
                self.game.show_lore_viewer = False
                self._lore_viewer_menu = None  # Clear menu cache
            return True

        # Achievements screen - pass raw events for navigation
        if self.game.show_achievements:
            return self._handle_achievements_input(event)

        # Inventory - pass raw events for navigation handling (D-pad + A/B buttons)
        if self.game.show_inventory:
            return self._handle_inventory_input(event)

        # Get current context
        context = self._get_current_context()

        # Get action from gamepad handler
        action = self.gamepad_handler.handle_button_event(event, context)

        # Execute action if found
        if action:
            # Special handling for EXIT_TO_MENU (START button = pause/menu)
            # Must mirror ESC key logic in game_loop.py
            if action == InputAction.EXIT_TO_MENU:
                # Don't allow menu if player is dead or dying
                if (
                    self.game.player.cpu <= 0
                    or self.game.game_over
                    or (hasattr(self.game, "pending_death_dialogue") and self.game.pending_death_dialogue)
                ):
                    return True  # Consume event, but don't exit

                # Auto-save and signal exit to main menu
                self.game.auto_save()
                return False  # False = exit to main menu

            return self._execute_action(action)

        # Return None (not False!) for unhandled events
        # False is reserved for "exit to main menu" signal
        return None

    def handle_controller_axis(self, event: tcod.event.ControllerAxis) -> bool | None:
        """
        Handle controller analog stick/trigger axis events.

        Args:
            event: Controller axis event

        Returns:
            True if event was handled
            None if event was not handled
            False ONLY if we explicitly want to exit to main menu
        """
        # Track input device for dynamic help text
        set_last_device(InputDeviceType.GAMEPAD)

        # CRITICAL: Update analog stick state FIRST, before any context handling
        # This ensures that analog_handler always has current stick positions
        # regardless of which context processes the event
        CA = tcod.sdl.joystick.ControllerAxis

        if event.axis == CA.LEFTX:
            self.gamepad_handler.analog_handler.update_left_stick(x=event.value)
        elif event.axis == CA.LEFTY:
            self.gamepad_handler.analog_handler.update_left_stick(y=event.value)
        elif event.axis == CA.RIGHTX:
            self.gamepad_handler.analog_handler.update_right_stick(x=event.value)
        elif event.axis == CA.RIGHTY:
            self.gamepad_handler.analog_handler.update_right_stick(y=event.value)

        # Priority check: Achievement popup (must match keyboard handling)
        # Analog stick movement should also dismiss achievement popups for consistent UX
        if (
            hasattr(self.game, "achievement_popup_manager")
            and self.game.achievement_popup_manager.has_active_popup()
        ):
            # Dismiss on significant stick movement (not every tiny axis event)
            if abs(event.value) > GameConfig.GAMEPAD_POPUP_DISMISS_RAW_THRESHOLD:
                self.game.achievement_popup_manager.dismiss_active_popup()
                return True  # Consume the event
            # Ignore tiny axis noise while popup is active
            return True

        # Help screen - pass raw axis events for left stick navigation
        if self.game.show_help:
            if self.renderer:
                help_menu = self.renderer._get_or_create_help_menu()
                self.renderer.ui_renderer.handle_help_input(event, help_menu)
            return True

        # Lore viewer (data fragments) - pass raw axis events for left stick navigation
        if self.game.show_lore_viewer:
            lore_menu = self._get_or_create_lore_viewer_menu()
            lore_menu.handle_input(event)
            return True

        # Achievements screen - pass raw axis events for left stick navigation
        if self.game.show_achievements:
            return self._handle_achievements_input(event)

        # Inventory - pass raw axis events for left stick navigation
        if self.game.show_inventory:
            return self._handle_inventory_input(event)

        # Get current context
        context = self._get_current_context()

        # Get action from gamepad handler (processes analog stick movement)
        action = self.gamepad_handler.handle_axis_event(event, context)

        # Execute action if found
        if action:
            return self._execute_action(action)

        # Return None for unhandled events, not False
        return None
