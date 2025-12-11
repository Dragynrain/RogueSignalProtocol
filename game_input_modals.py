"""
game_input_modals.py - Modal Screen Input Handlers

Handles input for modal screens (inventory, look mode, targeting, lore viewer, achievements).
Each modal has its own focused handler class for maintainability.

This module was extracted from game_input.py to provide organized,
testable modal interaction logic separate from main game input routing.
"""

import logging

import tcod.event

from game_coordinate_helpers import CoordinateHelpers
from game_entities import Position
from game_input_actions import InputAction, InputContext
from game_input_base import BaseInputHandler
from game_input_coordinates import InputCoordinateConverter


class InventoryInputHandler(BaseInputHandler):
    """Handles inventory screen input (keyboard, mouse, and gamepad)."""

    def __init__(self, game, renderer=None, input_mapper=None, controllers=None, gamepad_handler=None):
        # Initialize BaseInputHandler with shared InputMapper, controllers, and gamepad_handler
        super().__init__(game, renderer, input_mapper=input_mapper, controllers=controllers,
                        gamepad_handler=gamepad_handler)

    def get_context(self) -> InputContext:
        """Get current input context for inventory."""
        return InputContext.INVENTORY

    def get_default_return(self) -> bool:
        """Inventory handler returns True by default (event consumed)."""
        return True

    def navigate(self, direction: int):
        """Navigate inventory selection across equipped exploits and inventory items."""
        # Get total selectable items (equipped exploits + inventory items)
        equipped_count = len(self.game.player.inventory_manager.equipped_exploits)
        inventory_items = len(self.game.player.inventory_manager.get_display_items())
        total_items = equipped_count + inventory_items

        if total_items > 0:
            self.game.inventory_selection = (
                self.game.inventory_selection + direction
            ) % total_items

    def execute_action(self, action: InputAction) -> bool:
        """
        Execute an InputAction in inventory context.

        Args:
            action: The InputAction to execute

        Returns:
            True if action was handled
        """

        # Navigation (handle both NAVIGATE_ and MOVE_ actions for keyboard compatibility)
        # Keyboard maps arrow keys to MOVE_*, gamepad maps to NAVIGATE_*
        if action == InputAction.NAVIGATE_UP or action == InputAction.MOVE_NORTH:
            self.navigate(-1)
            return True
        elif action == InputAction.NAVIGATE_DOWN or action == InputAction.MOVE_SOUTH:
            self.navigate(1)
            return True
        elif action == InputAction.NAVIGATE_PAGE_UP:
            # Page up = move 5 items up
            self.navigate(-5)
            return True
        elif action == InputAction.NAVIGATE_PAGE_DOWN:
            # Page down = move 5 items down
            self.navigate(5)
            return True
        # Confirm/Cancel
        elif action == InputAction.CONFIRM:
            self.use_selected_item()
            return True
        elif action == InputAction.CANCEL or action == InputAction.TOGGLE_INVENTORY:
            # Both CANCEL and TOGGLE_INVENTORY should close inventory
            self.game.show_inventory = False
            return True

        # Modal captures all input - return True to prevent fall-through to gameplay
        return self.get_default_return()

    def use_selected_item(self):
        """Use or equip the selected inventory item, or unequip if selecting equipped exploit."""
        equipped = self.game.player.inventory_manager.equipped_exploits
        display_items = self.game.player.inventory_manager.get_display_items()
        selection = self.game.inventory_selection

        # Check if selecting an equipped exploit (first N items)
        if selection < len(equipped):
            # Enter/click on equipped exploit = unequip it
            exploit_name = equipped[selection]
            self.game.player.inventory_manager.unequip_exploit(exploit_name)
            return

        # Check if selecting an inventory item
        inventory_idx = selection - len(equipped)
        if 0 <= inventory_idx < len(display_items):
            item = display_items[inventory_idx]
            # Call the item's use method directly
            item.use(self.game.player, self.game)
        else:
            logging.warning(
                f"Inventory: Invalid selection {selection} (equipped={len(equipped)}, inventory={len(display_items)})"
            )

    def open_inventory(self):
        """Open the inventory screen."""
        self.game.show_inventory = True

    def handle_mouse_motion(self, event: tcod.event.MouseMotion) -> bool:
        """Handle mouse motion in inventory - update selection on hover."""
        from game_rendering_ui import UIRenderer

        if not hasattr(event, "position") or event.position is None:
            return False

        # Convert pixel coordinates to console tile coordinates
        window_w, window_h = InputCoordinateConverter.get_window_dimensions(
            self.renderer, self.game
        )
        tile_x, tile_y = CoordinateHelpers.pixel_to_char_coords(
            event.position.x, event.position.y, window_w, window_h
        )

        # Ask the UI renderer which inventory item (if any) is being hovered
        # This is the single source of truth - no duplicated calculations!
        item_index = UIRenderer.get_inventory_item_at_coords(self.game, tile_x, tile_y)

        if item_index is not None:
            # Update selection to hovered item
            self.game.inventory_selection = item_index
            return True

        return False

    def handle_left_click(self, event: tcod.event.MouseButtonDown) -> bool:
        """Handle left click in inventory - use/equip the clicked item."""
        from game_rendering_ui import UIRenderer

        # Convert pixel coordinates to console tile coordinates
        window_w, window_h = InputCoordinateConverter.get_window_dimensions(
            self.renderer, self.game
        )
        tile_x, tile_y = CoordinateHelpers.pixel_to_char_coords(
            event.position.x, event.position.y, window_w, window_h
        )

        # Check if clicking on an item
        item_index = UIRenderer.get_inventory_item_at_coords(self.game, tile_x, tile_y)

        if item_index is not None:
            # Set selection and use item
            self.game.inventory_selection = item_index
            self.use_selected_item()
            return True

        return False

    def handle_mouse_wheel(self, event: tcod.event.MouseWheel) -> bool:
        """Handle mouse wheel in inventory - scroll the list."""
        display_items = self.game.player.inventory_manager.get_display_items()
        if not display_items:
            return False

        # Scroll direction: event.y < 0 means scroll down, > 0 means scroll up
        if event.y < 0:
            # Scroll down - increase offset
            max_offset = max(0, len(display_items) - 1)
            self.game.inventory_scroll_offset = min(
                self.game.inventory_scroll_offset + 1, max_offset
            )
        elif event.y > 0:
            # Scroll up - decrease offset
            self.game.inventory_scroll_offset = max(0, self.game.inventory_scroll_offset - 1)

        return True


class LookModeInputHandler(BaseInputHandler):
    """Handles look mode input (keyboard, gamepad, and mouse)."""

    def __init__(self, game, renderer=None, input_mapper=None, controllers=None, gamepad_handler=None):
        # Initialize BaseInputHandler with shared InputMapper, controllers, and gamepad_handler
        super().__init__(game, renderer, input_mapper=input_mapper, controllers=controllers,
                        gamepad_handler=gamepad_handler)

    def get_context(self) -> InputContext:
        """Get current input context for look mode."""
        return InputContext.LOOK_MODE

    def get_default_return(self) -> bool:
        """Look mode handler returns True by default (event consumed)."""
        return True

    def enter_look_mode(self):
        """Enter look mode, starting cursor at player position."""
        self.game.look_mode = True
        self.game.look_cursor_position = Position(self.game.player.x, self.game.player.y)
        self.game.message_log.add_message("Look mode activated (ESC or L to exit)")

    def move_cursor(self, dx: int, dy: int):
        """Move look mode cursor and update inspection info."""
        from game_config import GameConfig

        # Calculate new position
        new_x = max(0, min(GameConfig.MAP_WIDTH - 1, self.game.look_cursor_position.x + dx))
        new_y = max(0, min(GameConfig.MAP_HEIGHT - 1, self.game.look_cursor_position.y + dy))
        self.game.look_cursor_position = Position(new_x, new_y)

        # Inspection info is displayed in real-time via the inspection panel
        # No need to log to message log

    def execute_action(self, action: InputAction) -> bool:
        """
        Execute an InputAction in look mode context.

        Handles cursor movement for keyboard, gamepad (both sticks), and mouse.

        Args:
            action: The InputAction to execute

        Returns:
            True if action was handled
        """

        # Cursor movement - support full 8-way movement (MOVE actions work in look mode)
        if action == InputAction.MOVE_NORTH:
            self.move_cursor(0, -1)
            return True
        elif action == InputAction.MOVE_SOUTH:
            self.move_cursor(0, 1)
            return True
        elif action == InputAction.MOVE_WEST:
            self.move_cursor(-1, 0)
            return True
        elif action == InputAction.MOVE_EAST:
            self.move_cursor(1, 0)
            return True
        elif action == InputAction.MOVE_NORTHEAST:
            self.move_cursor(1, -1)
            return True
        elif action == InputAction.MOVE_NORTHWEST:
            self.move_cursor(-1, -1)
            return True
        elif action == InputAction.MOVE_SOUTHEAST:
            self.move_cursor(1, 1)
            return True
        elif action == InputAction.MOVE_SOUTHWEST:
            self.move_cursor(-1, 1)
            return True
        # 4-way navigation (D-pad fallback)
        elif action == InputAction.NAVIGATE_UP:
            self.move_cursor(0, -1)
            return True
        elif action == InputAction.NAVIGATE_DOWN:
            self.move_cursor(0, 1)
            return True
        elif action == InputAction.NAVIGATE_LEFT:
            self.move_cursor(-1, 0)
            return True
        elif action == InputAction.NAVIGATE_RIGHT:
            self.move_cursor(1, 0)
            return True
        # Confirm/Cancel
        elif action == InputAction.CONFIRM:
            # In look mode, confirm doesn't do anything (inspection is automatic)
            return True
        elif action == InputAction.CANCEL or action == InputAction.TOGGLE_LOOK_MODE:
            # Both CANCEL and TOGGLE_LOOK_MODE should exit look mode
            self.game.look_mode = False
            self.game.message_log.add_message("Look mode exited")
            return True

        # Modal captures all input - return True to prevent fall-through to gameplay
        return self.get_default_return()

    def handle_mouse_motion(self, event: tcod.event.MouseMotion) -> bool:
        """Handle mouse motion in look mode - update cursor position with throttling."""
        import time

        # Throttle mouse updates to 50ms intervals for smoother, more controlled movement
        current_time = time.time()
        time_since_last_update = current_time - self.game.look_mode_mouse_last_update

        if time_since_last_update < 0.05:  # 50ms throttle (20 updates/sec)
            return False

        # Only do expensive world conversion when not throttled
        graphics_mode = (
            self.game.settings.graphics_mode
            if hasattr(self.game, "settings") and self.game.settings is not None
            else "glyph"
        )
        world_pos = InputCoordinateConverter.pixel_to_world_position(
            event.position.x, event.position.y, self.renderer, self.game, graphics_mode
        )
        if world_pos:
            self.game.look_cursor_position = world_pos
            self.game.look_mode_mouse_last_update = current_time
            return True
        return False

    def handle_left_click(self, event: tcod.event.MouseButtonDown) -> bool:
        """Handle left click in look mode - inspect entity at cursor."""
        graphics_mode = (
            self.game.settings.graphics_mode
            if hasattr(self.game, "settings") and self.game.settings is not None
            else "glyph"
        )
        world_pos = InputCoordinateConverter.pixel_to_world_position(
            event.position.x, event.position.y, self.renderer, self.game, graphics_mode
        )
        if world_pos:
            self.game.look_cursor_position = world_pos
            # Inspection happens automatically via the inspection panel
            return True
        return False


class TargetingInputHandler(BaseInputHandler):
    """Handles targeting mode input (keyboard, gamepad, and mouse)."""

    def __init__(self, game, renderer=None, input_mapper=None, controllers=None, gamepad_handler=None):
        # Initialize BaseInputHandler with shared InputMapper, controllers, and gamepad_handler
        super().__init__(game, renderer, input_mapper=input_mapper, controllers=controllers,
                        gamepad_handler=gamepad_handler)

    def get_context(self) -> InputContext:
        """Get current input context for targeting mode."""
        return InputContext.TARGETING

    def get_default_return(self) -> bool:
        """Targeting handler returns True by default (event consumed)."""
        return True

    def execute_action(self, action: InputAction) -> bool:
        """
        Execute an InputAction in targeting mode context.

        Handles cursor movement (both sticks) and exploit execution.

        Args:
            action: The InputAction to execute

        Returns:
            True if action was handled
        """

        # Cursor movement - support both sticks (8-way left stick + 4-way right stick/D-pad)
        # Left stick (8-way)
        if action == InputAction.MOVE_NORTH:
            self.game._move_cursor(0, -1)
            return True
        elif action == InputAction.MOVE_SOUTH:
            self.game._move_cursor(0, 1)
            return True
        elif action == InputAction.MOVE_WEST:
            self.game._move_cursor(-1, 0)
            return True
        elif action == InputAction.MOVE_EAST:
            self.game._move_cursor(1, 0)
            return True
        elif action == InputAction.MOVE_NORTHEAST:
            self.game._move_cursor(1, -1)
            return True
        elif action == InputAction.MOVE_NORTHWEST:
            self.game._move_cursor(-1, -1)
            return True
        elif action == InputAction.MOVE_SOUTHEAST:
            self.game._move_cursor(1, 1)
            return True
        elif action == InputAction.MOVE_SOUTHWEST:
            self.game._move_cursor(-1, 1)
            return True
        # Right stick / D-pad (4-way)
        elif action == InputAction.NAVIGATE_UP:
            self.game._move_cursor(0, -1)
            return True
        elif action == InputAction.NAVIGATE_DOWN:
            self.game._move_cursor(0, 1)
            return True
        elif action == InputAction.NAVIGATE_LEFT:
            self.game._move_cursor(-1, 0)
            return True
        elif action == InputAction.NAVIGATE_RIGHT:
            self.game._move_cursor(1, 0)
            return True
        # Confirm = execute exploit at cursor
        elif action == InputAction.CONFIRM:
            if self.game.targeting_exploit is None:
                logging.warning("Confirm in targeting mode but no exploit selected")
                self.game.targeting_mode = False
                return True
            self.game.exploit_system.execute_exploit(
                self.game.targeting_exploit, self.game.cursor_position
            )
            return True
        # Cancel = exit targeting mode
        elif action == InputAction.CANCEL:
            self.game.targeting_mode = False
            self.game.targeting_exploit = None
            self.game.message_log.add_message("Targeting cancelled")
            return True
        # Block UI toggles in targeting mode (prevent accidental exits)
        elif action in (InputAction.TOGGLE_INVENTORY, InputAction.TOGGLE_ACHIEVEMENTS,
                        InputAction.TOGGLE_LORE_VIEWER, InputAction.TOGGLE_HELP):
            return True  # Silently ignore

        # Modal captures all input - return True to prevent fall-through to gameplay
        return self.get_default_return()

    def handle_mouse_motion(self, event: tcod.event.MouseMotion) -> bool:
        """Handle mouse motion in targeting mode - update cursor position."""
        graphics_mode = (
            self.game.settings.graphics_mode
            if hasattr(self.game, "settings") and self.game.settings is not None
            else "glyph"
        )
        world_pos = InputCoordinateConverter.pixel_to_world_position(
            event.position.x, event.position.y, self.renderer, self.game, graphics_mode
        )
        if world_pos:
            self.game.cursor_position = world_pos
            return True
        return False

    def handle_left_click(self, event: tcod.event.MouseButtonDown) -> bool:
        """Handle left click in targeting mode - execute exploit."""
        graphics_mode = (
            self.game.settings.graphics_mode
            if hasattr(self.game, "settings") and self.game.settings is not None
            else "glyph"
        )
        world_pos = InputCoordinateConverter.pixel_to_world_position(
            event.position.x, event.position.y, self.renderer, self.game, graphics_mode
        )
        if world_pos and self.game.targeting_exploit:
            self.game.cursor_position = world_pos
            # Execute exploit at clicked position
            self.game.exploit_system.execute_exploit(self.game.targeting_exploit, world_pos)
            return True
        return False


# AchievementsInputHandler removed in Phase 4
# Achievements input is now handled directly by AchievementsMenu (game_menu_achievements.py)
# with a str→bool adapter in game_input.py (_handle_achievements_input)
