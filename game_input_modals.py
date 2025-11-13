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
from game_input_coordinates import InputCoordinateConverter
from game_ui import UniversalInputHandler


class InventoryInputHandler:
    """Handles inventory screen input (keyboard and mouse)."""

    def __init__(self, game, renderer=None):
        self.game = game
        self.renderer = renderer

    def handle_input(self, event: tcod.event.KeyDown) -> bool:
        """Handle keyboard input while inventory is open."""
        # Handle navigation using universal handler with callback
        if UniversalInputHandler.handle_list_navigation(self, event, 0, True, self.navigate):
            return True

        # Handle selection and other actions
        if UniversalInputHandler.is_confirm_key(event):
            self.use_selected_item()
        elif event.sym == tcod.event.KeySym.I or UniversalInputHandler.is_escape_key(event):
            self.game.show_inventory = False

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

    def use_selected_item(self):
        """Use or equip the selected inventory item, or unequip if selecting equipped exploit."""
        equipped = self.game.player.inventory_manager.equipped_exploits
        display_items = self.game.player.inventory_manager.get_display_items()
        selection = self.game.inventory_selection

        # Check if selecting an equipped exploit (first N items)
        if selection < len(equipped):
            # Enter/click on equipped exploit = unequip it
            exploit_name = equipped[selection]
            logging.debug(
                f"Inventory: Unequipping {exploit_name} from slot {selection}"
            )
            self.game.player.inventory_manager.unequip_exploit(exploit_name)
            return

        # Check if selecting an inventory item
        inventory_idx = selection - len(equipped)
        if 0 <= inventory_idx < len(display_items):
            item = display_items[inventory_idx]
            logging.debug(f"Inventory: Using item {item} at inventory index {inventory_idx}")
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


class LookModeInputHandler:
    """Handles look mode input (keyboard and mouse)."""

    def __init__(self, game, renderer=None):
        self.game = game
        self.renderer = renderer

    def handle_input(self, event: tcod.event.KeyDown) -> bool:
        """Handle keyboard input while in look mode."""
        from game_input import InputMappings

        # ESC or L exits look mode
        if UniversalInputHandler.is_escape_key(event) or event.sym == tcod.event.KeySym.L:
            logging.debug(
                f"Input: Exiting look mode from cursor ({self.game.look_cursor_position.x},{self.game.look_cursor_position.y})"
            )
            self.game.look_mode = False
            self.game.message_log.add_message("Look mode exited")
            return True

        # Movement keys - use shared mapping to avoid duplication
        if event.sym in InputMappings.MOVEMENT_MAP:
            dx, dy = InputMappings.MOVEMENT_MAP[event.sym]
            self.move_cursor(dx, dy)
            return True

        # Unhandled key - consume it and stay in look mode
        return True

    def enter_look_mode(self):
        """Enter look mode, starting cursor at player position."""
        self.game.look_mode = True
        self.game.look_cursor_position = Position(self.game.player.x, self.game.player.y)
        self.game.message_log.add_message("Look mode activated (ESC or L to exit)")
        logging.debug(
            f"Input: Entered look mode at player position ({self.game.player.x},{self.game.player.y})"
        )

    def move_cursor(self, dx: int, dy: int):
        """Move look mode cursor and update inspection info."""
        from game_config import GameConfig

        # Calculate new position
        new_x = max(0, min(GameConfig.MAP_WIDTH - 1, self.game.look_cursor_position.x + dx))
        new_y = max(0, min(GameConfig.MAP_HEIGHT - 1, self.game.look_cursor_position.y + dy))
        self.game.look_cursor_position = Position(new_x, new_y)

        # Inspection info is displayed in real-time via the inspection panel
        # No need to log to message log

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
            self.game.settings.graphics_mode if hasattr(self.game, "settings") else "glyph"
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
            self.game.settings.graphics_mode if hasattr(self.game, "settings") else "glyph"
        )
        world_pos = InputCoordinateConverter.pixel_to_world_position(
            event.position.x, event.position.y, self.renderer, self.game, graphics_mode
        )
        if world_pos:
            self.game.look_cursor_position = world_pos
            # Inspection happens automatically via the inspection panel
            return True
        return False


class TargetingInputHandler:
    """Handles targeting mode input (keyboard and mouse)."""

    def __init__(self, game, renderer=None):
        self.game = game
        self.renderer = renderer

    def handle_input(self, event: tcod.event.KeyDown) -> bool:
        """Handle keyboard input while in targeting mode."""
        from game_input import InputMappings

        # Movement keys - use shared mapping to avoid duplication
        if event.sym in InputMappings.MOVEMENT_MAP:
            dx, dy = InputMappings.MOVEMENT_MAP[event.sym]
            self.game._move_cursor(dx, dy)
        elif event.sym in (tcod.event.KeySym.RETURN, tcod.event.KeySym.KP_ENTER):
            logging.debug(
                f"Input: Targeting confirm - exploit={self.game.targeting_exploit}, target=({self.game.cursor_position.x},{self.game.cursor_position.y})"
            )
            self.game.exploit_system.execute_exploit(
                self.game.targeting_exploit, self.game.cursor_position
            )

        return True

    def handle_mouse_motion(self, event: tcod.event.MouseMotion) -> bool:
        """Handle mouse motion in targeting mode - update cursor position."""
        graphics_mode = (
            self.game.settings.graphics_mode if hasattr(self.game, "settings") else "glyph"
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
            self.game.settings.graphics_mode if hasattr(self.game, "settings") else "glyph"
        )
        world_pos = InputCoordinateConverter.pixel_to_world_position(
            event.position.x, event.position.y, self.renderer, self.game, graphics_mode
        )
        if world_pos:
            self.game.cursor_position = world_pos
            # Execute exploit at clicked position
            logging.debug(
                f"Input: Mouse targeting confirm - exploit={self.game.targeting_exploit}, target=({world_pos.x},{world_pos.y})"
            )
            self.game.exploit_system.execute_exploit(self.game.targeting_exploit, world_pos)
            return True
        return False




class AchievementsInputHandler:
    """Handles achievements screen input."""

    def __init__(self, game, renderer=None):
        self.game = game
        self.renderer = renderer

    def handle_input(self, event: tcod.event.KeyDown) -> bool:
        """Handle keyboard input while achievements screen is open."""
        # Get achievements menu from renderer
        if self.renderer and hasattr(self.renderer, "ui_renderer"):
            achievements_menu = (
                self.renderer.ui_renderer._achievements_menu
                if hasattr(self.renderer.ui_renderer, "_achievements_menu")
                else None
            )

            if achievements_menu:
                # Delegate to achievements menu's input handler
                action = achievements_menu.handle_input(event)
                if action == "back":
                    self.game.show_achievements = False
                    return True

        # Fallback: ESC or V closes achievements
        if UniversalInputHandler.is_escape_key(event) or event.sym == tcod.event.KeySym.V:
            self.game.show_achievements = False
            return True

        # Unhandled key - consume it and stay in achievements
        return True
