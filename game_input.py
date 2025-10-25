"""
Rogue Signal Protocol - Game Input Module

Handles all player input and translates to game actions.
Provides InputHandler for in-game controls and InputMappings for shared key definitions.
Supports movement, combat, inventory, menu navigation, and look mode.
"""

import logging
import tcod
import tcod.event
from typing import Optional, Tuple
from game_config import GameConfig
from game_data import GameData
from game_inventory import CodeHack, ExploitItem
from game_ui import UniversalInputHandler
from game_entities import Position
from game_coordinate_helpers import CoordinateHelpers



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
        tcod.event.KeySym.KP_7: (-1, -1)
    }


class InputHandler:
    """Handles all user input and translates it to game actions."""

    def __init__(self, game, renderer=None):
        self.game = game
        self.renderer = renderer  # GameRenderer instance for help screen input

    def _get_window_dimensions(self) -> Tuple[int, int]:
        """
        Get window dimensions from context.

        Tries renderer.context first, then game.context, then fallback.

        Returns:
            Tuple of (window_width, window_height) in pixels
        """
        context = None
        if self.renderer and hasattr(self.renderer, 'context'):
            context = self.renderer.context
        elif hasattr(self.game, 'context'):
            context = self.game.context

        if context and hasattr(context, 'sdl_window'):
            return context.sdl_window.size
        return (800, 600)  # Fallback

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

        logging.debug(f"Input: Key {event.sym.name}, state=[{','.join(state_context) if state_context else 'gameplay'}]")

        # Priority 1: Active dialogue (highest priority overlay)
        # Check this BEFORE game_over to allow death dialogue to be shown
        if self.game.dialogue_state.is_active():
            return self._handle_dialogue_input(event)

        # Dead/game over state - any key should exit to main menu
        # Only reached if no dialogue is active (death dialogue would be active)
        if self.game.player.cpu <= 0 or self.game.game_over:
            # Exit to main menu instead of showing pause menu when dead
            return False

        # Modal screens - handle non-escape keys
        if self.game.show_help:
            # Delegate to help menu's input handler (supports pagination)
            if self.renderer and hasattr(self.renderer, 'ui_renderer'):
                result = self.renderer.ui_renderer.screen_renderer.handle_help_input(event)
                if result == "back":
                    self.game.show_help = False
                return True
            else:
                # Fallback: any key closes help
                self.game.show_help = False
                return True

        if self.game.show_story_fragment is not None:
            # Any key closes the story fragment display
            self.game.show_story_fragment = None
            return True

        if self.game.show_lore_viewer:
            return self._handle_lore_viewer_input(event)

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
        if g.show_story_fragment is not None:
            g.show_story_fragment = None
        elif g.show_lore_viewer:
            g.show_lore_viewer, g.lore_viewer_mode, g.lore_viewer_selection = False, "list", 0
        elif g.show_help:
            g.show_help = False
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
        from game_dialogue_system import DialogueInputHandler
        from game_entities import Colors

        dialogue = self.game.dialogue_state.get_active()
        if not dialogue:
            logging.debug("Input: Dialogue input handler called but no active dialogue")
            return True

        # Use DialogueInputHandler to process input
        action = DialogueInputHandler.handle_input(dialogue, event.sym)
        logging.debug(f"Input: Dialogue '{dialogue.title}' received key {event.sym.name}, action={action}")

        # If dialogue handled the input, process it
        if action is not None:
            if action == "confirm":
                self._handle_dialogue_confirm()
                return True
            elif action in ["cancel", "dismiss"]:
                should_continue = self._handle_dialogue_dismiss()
                return should_continue
            elif action == "dont_show_again":
                self._handle_dialogue_dont_show_again()
                return True

        # Dialogue is active - don't process other inputs
        return True

    def _handle_dialogue_confirm(self):
        """Handle dialogue confirmation (user pressed Y)."""
        dialogue = self.game.dialogue_state.get_active()
        if not dialogue:
            return

        logging.debug(f"Input: Dialogue confirm for '{dialogue.title}'")

        # Check dialogue type by title (since we're using DialogueBox now)
        if "OVERCLOCK WARNING" in dialogue.title:
            # Player confirmed overclock - no need to do anything, exploit will be used
            # The overclock system sets self.overclock_confirmation before showing dialogue
            logging.debug("Input: Overclock confirmed")
        elif "GATEWAY" in dialogue.title:
            # Player confirmed gateway - proceed to next level
            logging.debug(f"Input: Gateway confirmed, advancing from level {self.game.level}")
            self.game.sound_manager.play_sound("level_complete")
            self.game.message_log.add_message("Gateway reached! Next network...")
            self.game.next_level()

        # Close dialogue
        self.game.dialogue_state.close()

    def _handle_dialogue_dismiss(self) -> bool:
        """
        Handle dialogue dismissal/cancellation (user pressed N or ESC).

        Returns:
            True if game should continue, False if should exit to menu
        """
        dialogue = self.game.dialogue_state.get_active()
        if not dialogue:
            return True

        logging.debug(f"Input: Dialogue dismiss for '{dialogue.title}'")

        # Check dialogue type by title
        if "UNDER ATTACK" in dialogue.title:
            # Close inventory when under attack (can't stay in inventory while being attacked)
            self.game.show_inventory = False
        elif "OVERCLOCK WARNING" in dialogue.title:
            # Cancel exploit use - just close dialogue
            pass
        elif "GATEWAY" in dialogue.title:
            # Player cancelled gateway
            self.game.message_log.add_message("Staying in current network")
        elif "PURGED" in dialogue.title or "BREAKTHROUGH" in dialogue.title:
            # Death/victory messages - any key closes and returns to menu
            self.game.dialogue_state.close()
            return False  # Exit to main menu

        # Close dialogue
        self.game.dialogue_state.close()
        return True  # Continue game

    def _handle_dialogue_dont_show_again(self):
        """Handle 'don't show this again' option (user pressed D)."""
        from game_entities import Colors

        dialogue = self.game.dialogue_state.get_active()
        if not dialogue or not dialogue.user_pref_key:
            return

        # Disable this dialogue type
        self.game.dialogue_state.disable_dialogue(dialogue.user_pref_key)

        # Add message to log
        self.game.message_log.add_message(
            "Dialogue disabled. Re-enable in Settings if needed.",
            Colors.YELLOW
        )

        # For overclock warning, pressing D should still execute the exploit
        if "OVERCLOCK WARNING" in dialogue.title:
            self._handle_dialogue_confirm()
        else:
            self.game.dialogue_state.close()

    def _handle_inventory_input(self, event) -> bool:
        """Handle input while inventory is open."""
        # Handle navigation using universal handler with callback
        if UniversalInputHandler.handle_list_navigation(self, event, 0, True, self._navigate_inventory):
            return True
        
        # Handle selection and other actions
        if UniversalInputHandler.is_confirm_key(event):
            self._use_selected_inventory_item()
        elif event.sym == tcod.event.KeySym.U:
            self._unequip_selected_exploit()
        elif event.sym == tcod.event.KeySym.X:
            self._examine_selected_item()
        elif event.sym == tcod.event.KeySym.I:
            self.game.show_inventory = False
        
        return True
    
    def _handle_lore_viewer_input(self, event) -> bool:
        """Handle input while lore viewer is open."""
        discovered_fragments = self.game.story_fragment_manager.get_discovered_fragments()
        
        if not discovered_fragments:
            # No fragments, only ESC should work to close (handled by main loop)
            return UniversalInputHandler.is_escape_key(event)
            
        if self.game.lore_viewer_mode == "list":
            # Handle navigation using universal handler with callback
            if UniversalInputHandler.handle_list_navigation(self, event, len(discovered_fragments), False, self._navigate_lore_viewer):
                return True

            # Handle selection
            if UniversalInputHandler.is_confirm_key(event):
                # Enter reading mode for selected fragment
                self.game.lore_viewer_mode = "reading"
                return True
            elif event.sym == tcod.event.KeySym.F:
                # 'F' key closes story fragment viewer and returns to game
                self.game.show_lore_viewer = False
                self.game.lore_viewer_mode = "list"
                self.game.lore_viewer_selection = 0
                return True
            elif UniversalInputHandler.is_escape_key(event):
                # ESC also closes story fragment viewer
                self.game.show_lore_viewer = False
                self.game.lore_viewer_mode = "list"
                self.game.lore_viewer_selection = 0
                return True
        
        elif self.game.lore_viewer_mode == "reading":
            # Reading mode - ESC or 'F' closes, other keys return to list
            if event.sym == tcod.event.KeySym.F or UniversalInputHandler.is_escape_key(event):
                # 'F' or ESC closes story fragment viewer and returns to game
                self.game.show_lore_viewer = False
                self.game.lore_viewer_mode = "list"
                self.game.lore_viewer_selection = 0
                return True
            else:
                # Any other key returns to list view
                self.game.lore_viewer_mode = "list"
                return True
        
        # Unhandled key - consume it and stay in lore viewer
        return True
    
    def _navigate_list(self, current_index, list_length, direction):
        """Generic list navigation helper."""
        if list_length > 0:
            if direction == -1:
                return max(0, current_index - 1)
            else:
                return min(list_length - 1, current_index + 1)
        return current_index

    def _navigate_lore_viewer(self, direction: int):
        """Navigate lore viewer selection."""
        discovered_fragments = self.game.story_fragment_manager.get_discovered_fragments()
        self.game.lore_viewer_selection = self._navigate_list(
            self.game.lore_viewer_selection,
            len(discovered_fragments),
            direction
        )
    
    def _handle_targeting_input(self, event) -> bool:
        """Handle input while in targeting mode."""
        # Movement keys - use shared mapping to avoid duplication
        if event.sym in InputMappings.MOVEMENT_MAP:
            dx, dy = InputMappings.MOVEMENT_MAP[event.sym]
            self.game._move_cursor(dx, dy)
        elif event.sym in (tcod.event.KeySym.RETURN, tcod.event.KeySym.KP_ENTER):
            logging.debug(f"Input: Targeting confirm - exploit={self.game.targeting_exploit}, target=({self.game.cursor_position.x},{self.game.cursor_position.y})")
            self.game.exploit_system.execute_exploit(
                self.game.targeting_exploit,
                self.game.cursor_position
            )

        return True
    
    def _handle_gameplay_input(self, event) -> bool:
        """Handle input during normal gameplay."""
        # Movement keys - use shared mapping to avoid duplication
        if event.sym in InputMappings.MOVEMENT_MAP:
            dx, dy = InputMappings.MOVEMENT_MAP[event.sym]
            # Clear mouse hover when using keyboard movement
            self.game.mouse_hover_world_pos = None
            self.game.move_player(dx, dy)
        
        # Wait/rest
        elif event.sym in (tcod.event.KeySym.SPACE, tcod.event.KeySym.PERIOD, tcod.event.KeySym.KP_5):
            self.game.maybe_process_turn()
        
        # UI toggles
        elif event.sym == tcod.event.KeySym.I:
            self._open_inventory()
        elif event.sym == tcod.event.KeySym.L:
            self._enter_look_mode()
        elif event.sym == tcod.event.KeySym.F:
            self.game.show_lore_viewer = True
        elif event.sym == tcod.event.KeySym.SLASH and (event.mod & (tcod.event.Modifier.LSHIFT | tcod.event.Modifier.RSHIFT)):
            self.game.show_help = True
        
        # Exploit usage (1-5 keys) - check as loop
        else:
            exploit_keys = {
                tcod.event.KeySym.N1: 0, tcod.event.KeySym.N2: 1,
                tcod.event.KeySym.N3: 2, tcod.event.KeySym.N4: 3,
                tcod.event.KeySym.N5: 4
            }
            if event.sym in exploit_keys:
                self._use_exploit_slot(exploit_keys[event.sym])
        
        return True
    
    def _navigate_inventory(self, direction: int):
        """Navigate inventory selection across equipped exploits and inventory items."""
        # Get total selectable items (equipped exploits + inventory items)
        equipped_count = len(self.game.player.inventory_manager.equipped_exploits)
        inventory_items = len(self.game.player.inventory_manager.get_display_items())
        total_items = equipped_count + inventory_items
        
        if total_items > 0:
            self.game.inventory_selection = (self.game.inventory_selection + direction) % total_items
    
    def _use_selected_inventory_item(self):
        """Use the currently selected item (unequip exploit or use inventory item)."""
        equipped_count = len(self.game.player.inventory_manager.equipped_exploits)
        
        if self.game.inventory_selection < equipped_count:
            # Selection is in equipped exploits - unequip the selected one
            self._unequip_selected_exploit()
        else:
            # Selection is in inventory items - use the selected item
            inventory_items = self.game.player.inventory_manager.get_display_items()
            item_index = self.game.inventory_selection - equipped_count
            
            if 0 <= item_index < len(inventory_items):
                selected_item = inventory_items[item_index]
                if selected_item.use(self.game.player, self.game):
                    # Check if it was a code or exploit - both consume a turn
                    if isinstance(selected_item, (CodeHack, ExploitItem)):
                        self.game.maybe_process_turn()

                    # Update selection if item was consumed
                    new_equipped_count = len(self.game.player.inventory_manager.equipped_exploits)
                    new_inventory_count = len(self.game.player.inventory_manager.get_display_items())
                    max_selection = new_equipped_count + new_inventory_count - 1

                    if max_selection >= 0:
                        self.game.inventory_selection = min(self.game.inventory_selection, max_selection)
    
    def _unequip_selected_exploit(self):
        """Unequip the specifically selected exploit."""
        equipped_exploits = self.game.player.inventory_manager.equipped_exploits

        if 0 <= self.game.inventory_selection < len(equipped_exploits):
            exploit_key = equipped_exploits[self.game.inventory_selection]
            if self.game.player.inventory_manager.unequip_exploit(exploit_key):
                # unequip_exploit() already adds the item back to inventory
                exploit_def = GameData.EXPLOITS[exploit_key]
                self.game.message_log.add_message(f"Unequipped {exploit_def.name}")
                # Unequipping consumes a turn
                self.game.maybe_process_turn()
            else:
                self.game.message_log.add_message("Cannot unequip exploit")
        else:
            self.game.message_log.add_message("No exploit selected")
    
    def _examine_selected_item(self):
        """Show detailed information about the selected inventory item."""
        equipped_exploits = self.game.player.inventory_manager.equipped_exploits
        display_items = self.game.player.inventory_manager.get_display_items()
        
        # Determine what is selected
        selection_index = self.game.inventory_selection
        
        # Check if we're selecting an equipped exploit
        if selection_index < len(equipped_exploits):
            # Examining equipped exploit
            exploit_key = equipped_exploits[selection_index]
            if exploit_key in GameData.EXPLOITS:
                self._show_exploit_details(GameData.EXPLOITS[exploit_key])
            else:
                self.game.message_log.add_message(f"Unknown exploit: {exploit_key}")
            return
        
        # Check if we're selecting an unequipped item
        unequipped_index = selection_index - len(equipped_exploits)
        if unequipped_index >= 0 and unequipped_index < len(display_items):
            selected_item = display_items[unequipped_index]
            
            # Check if it's an exploit (unequipped)
            if hasattr(selected_item, 'exploit_key') and selected_item.exploit_key in GameData.EXPLOITS:
                exploit_def = GameData.EXPLOITS[selected_item.exploit_key]
                self._show_exploit_details(exploit_def)
            elif hasattr(selected_item, 'color') and hasattr(selected_item, 'effect'):
                # Code hack
                self._show_code_hack_details(selected_item)
            else:
                # Generic item
                self.game.message_log.add_message(f"=== {selected_item.name} ===")
                self.game.message_log.add_message(f"Description: {selected_item.description}")
        else:
            self.game.message_log.add_message("No item selected")
    
    def _show_exploit_details(self, exploit_def):
        """Show detailed information about an exploit."""
        self.game.message_log.add_message(f"=== {exploit_def.name} ===")
        self.game.message_log.add_message(f"Category: {exploit_def.category.title()}")
        self.game.message_log.add_message(f"RAM Cost: {exploit_def.ram}")
        self.game.message_log.add_message(f"Heat Cost: {exploit_def.heat}")
        
        if exploit_def.damage > 0:
            self.game.message_log.add_message(f"Damage: {exploit_def.damage}")
        if exploit_def.range > 0:
            self.game.message_log.add_message(f"Range: {exploit_def.range} tiles")
        
        self.game.message_log.add_message(f"Targeting: {exploit_def.targeting.name}")
        self.game.message_log.add_message(f"Effect: {exploit_def.description}")
    
    def _show_code_hack_details(self, code_hack):
        """Show detailed information about a code."""
        if code_hack.discovered:
            if code_hack.color_name in self.game.code_hack_effects:
                effect_key, desc = self.game.code_hack_effects[code_hack.color_name]
                self.game.message_log.add_message(f"=== {code_hack.name} ===")
                self.game.message_log.add_message(f"Effect: {desc}")
                if code_hack.quantity > 1:
                    self.game.message_log.add_message(f"Quantity: {code_hack.quantity}")
            else:
                self.game.message_log.add_message("Code effect unknown")
        else:
            self.game.message_log.add_message(f"=== {code_hack.name} ===")
            self.game.message_log.add_message("Effect: Unknown until used")
            if code_hack.quantity > 1:
                self.game.message_log.add_message(f"Quantity: {code_hack.quantity}")
    
    def _open_inventory(self):
        """Open the inventory screen."""
        logging.debug("Input: Opening inventory")
        self.game.sound_manager.play_sound("ui_menu_open")
        self.game.show_inventory = True
        self.game.inventory_selection = 0
    
    def _use_exploit_slot(self, slot: int):
        """Use exploit in specified slot."""
        equipped = self.game.player.inventory_manager.equipped_exploits
        if 0 <= slot < len(equipped):
            exploit_key = equipped[slot]
            logging.debug(f"Input: Using exploit slot {slot+1}: {exploit_key}")
            self.game.exploit_system.use_exploit(exploit_key)
        else:
            logging.debug(f"Input: Exploit slot {slot+1} is empty or invalid")

    def _enter_look_mode(self):
        """Enter look mode."""
        logging.debug(f"Input: Entering look mode at player pos ({self.game.player.x},{self.game.player.y})")
        self.game.look_mode = True
        # Initialize look cursor at player position
        self.game.look_cursor_position = Position(self.game.player.x, self.game.player.y)
        self.game.message_log.add_message("Look mode - Move cursor to inspect, ESC or L to exit")
        self.game.sound_manager.play_sound("ui_menu_open")

    def _handle_look_mode_input(self, event) -> bool:
        """Handle input while in look mode."""
        # ESC or L exits look mode
        if UniversalInputHandler.is_escape_key(event) or event.sym == tcod.event.KeySym.L:
            logging.debug(f"Input: Exiting look mode from cursor ({self.game.look_cursor_position.x},{self.game.look_cursor_position.y})")
            self.game.look_mode = False
            self.game.message_log.add_message("Look mode exited")
            return True

        # Movement keys - use shared mapping to avoid duplication
        if event.sym in InputMappings.MOVEMENT_MAP:
            dx, dy = InputMappings.MOVEMENT_MAP[event.sym]
            self._move_look_cursor(dx, dy)
            return True

        # Unhandled key - consume it and stay in look mode
        return True

    def _move_look_cursor(self, dx: int, dy: int):
        """Move look mode cursor and update inspection info."""
        from game_config import GameConfig

        # Calculate new position
        new_x = max(0, min(GameConfig.MAP_WIDTH - 1, self.game.look_cursor_position.x + dx))
        new_y = max(0, min(GameConfig.MAP_HEIGHT - 1, self.game.look_cursor_position.y + dy))
        self.game.look_cursor_position = Position(new_x, new_y)

        # Inspection info is displayed in real-time via the inspection panel
        # No need to log to message log

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
        if not hasattr(event, 'position') or event.position is None:
            return False

        # event.position contains RAW PIXEL coordinates from SDL
        # Handlers will convert to appropriate coordinate system (console or sprite grid)
        pixel_x = event.position.x
        pixel_y = event.position.y

        # Convert to console tile coordinates and store for hover effects
        window_width, window_height = self._get_window_dimensions()
        tile_x = pixel_x * GameConfig.SCREEN_WIDTH // window_width
        tile_y = pixel_y * GameConfig.SCREEN_HEIGHT // window_height
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
            return self._handle_lore_viewer_mouse_motion(event)

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
        if not hasattr(event, 'position') or event.position is None:
            return False

        pixel_x = event.position.x
        pixel_y = event.position.y

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
            return self._handle_lore_viewer_mouse_wheel(event)

        return False

    def _is_valid_mouse_tile(self, tile_x: int, tile_y: int) -> bool:
        """Check if mouse tile coordinates are within valid screen bounds.

        Args:
            tile_x: Console X coordinate (0-79)
            tile_y: Console Y coordinate (0-49)

        Returns:
            True if coordinates are valid, False otherwise
        """
        from game_config import GameConfig
        return (0 <= tile_x < GameConfig.SCREEN_WIDTH and
                0 <= tile_y < GameConfig.SCREEN_HEIGHT)

    def _mouse_pixel_to_world(self, pixel_x: float, pixel_y: float) -> Optional[Position]:
        """Convert mouse pixel coords to world coords.

        Conversion flow:
        1. Convert pixels to sprite grid coordinates (in graphics mode) or console chars (in glyph mode)
        2. Subtract status bar height to get viewport coords
        3. Add camera offset to get world coords
        4. Validate against map bounds

        Args:
            pixel_x: SDL pixel X coordinate
            pixel_y: SDL pixel Y coordinate

        Returns:
            Position in world coordinates, or None if outside valid game area
        """
        from game_config import GameConfig

        # Get graphics mode to determine conversion method
        graphics_mode = self.game.settings.graphics_mode if hasattr(self.game, 'settings') else "glyph"

        # Convert pixels to grid coordinates
        if graphics_mode == "graphics":
            # In graphics mode, sprites are rendered at pixel = grid * tile_dimension
            # Use self.renderer which is passed during InputHandler initialization
            if self.renderer and hasattr(self.renderer, 'tile_manager') and self.renderer.tile_manager:
                tile_x, tile_y = CoordinateHelpers.pixel_to_sprite_grid(
                    pixel_x, pixel_y,
                    self.renderer.tile_manager.tile_width,
                    self.renderer.tile_manager.tile_height
                )
            else:
                logging.error(f"Graphics mode but renderer not available: renderer={self.renderer}, has_tile_mgr={hasattr(self.renderer, 'tile_manager') if self.renderer else False}")
                return None
        else:
            # In glyph mode, use console character conversion
            try:
                window_w, window_h = self._get_window_dimensions()
                tile_x, tile_y = CoordinateHelpers.pixel_to_char_coords(
                    pixel_x, pixel_y, window_w, window_h
                )
            except Exception as e:
                logging.error(f"Failed to convert pixels in glyph mode: {e}")
                return None

        # Use graphics_mode (already fetched above) to handle coordinate conversion
        viewport_width = GameConfig.VIEWPORT_WIDTH(graphics_mode)
        viewport_height = GameConfig.VIEWPORT_HEIGHT(graphics_mode)
        status_bar_height = GameConfig.STATUS_BAR_HEIGHT()

        # In GRAPHICS mode, grid coords from pixel_to_sprite_grid are RENDERING positions
        # Sprites render at: pixel = (viewport_x, viewport_y + status_bar) * tile_dimensions
        # So grid coords INCLUDE status bar offset - we need to subtract it
        # In GLYPH mode, tile coords from pixel_to_char_coords are CONSOLE positions
        # Console tiles map directly: viewport = console_tile - status_bar

        if graphics_mode == "graphics":
            # Grid coordinates include status bar offset, subtract to get viewport
            viewport_x = tile_x
            viewport_y = tile_y - status_bar_height
        else:
            # Console coordinates, subtract status bar to get viewport
            viewport_x = tile_x
            viewport_y = tile_y - status_bar_height

        # Validate viewport coordinates
        if viewport_y < 0 or viewport_y >= viewport_height:
            return None
        if viewport_x < 0 or viewport_x >= viewport_width:
            return None

        # Use the camera offset from the last render for consistency
        # This ensures input conversion matches what's actually displayed on screen
        if hasattr(self.game, 'last_camera_offset') and self.game.last_camera_offset:
            camera_x = self.game.last_camera_offset.x
            camera_y = self.game.last_camera_offset.y
        else:
            # Fallback: calculate fresh (shouldn't happen after first render)
            center_x = self.game.player.x
            center_y = self.game.player.y
            camera_x = max(0, min(GameConfig.MAP_WIDTH - viewport_width,
                                 center_x - viewport_width // 2))
            camera_y = max(0, min(GameConfig.MAP_HEIGHT - viewport_height,
                                 center_y - viewport_height // 2))

        # Convert to world coordinates
        world_x = viewport_x + camera_x
        world_y = viewport_y + camera_y

        # Validate against map bounds
        if not (0 <= world_x < GameConfig.MAP_WIDTH and
                0 <= world_y < GameConfig.MAP_HEIGHT):
            return None

        return Position(world_x, world_y)

    # ============================================================================
    # GAMEPLAY MOUSE HANDLERS (Phase 2)
    # ============================================================================

    def _handle_look_mode_mouse_motion(self, event: tcod.event.MouseMotion) -> bool:
        """Handle mouse motion in look mode - update cursor position."""
        world_pos = self._mouse_pixel_to_world(event.position.x, event.position.y)
        if world_pos:
            self.game.look_cursor_position = world_pos
            return True
        return False

    def _handle_targeting_mouse_motion(self, event: tcod.event.MouseMotion) -> bool:
        """Handle mouse motion in targeting mode - update cursor position."""
        world_pos = self._mouse_pixel_to_world(event.position.x, event.position.y)
        if world_pos:
            self.game.cursor_position = world_pos
            return True
        return False

    def _handle_gameplay_mouse_motion(self, event: tcod.event.MouseMotion) -> bool:
        """Handle mouse motion in normal gameplay - update hover position for visual feedback."""
        world_pos = self._mouse_pixel_to_world(event.position.x, event.position.y)
        if world_pos:
            self.game.mouse_hover_world_pos = world_pos
            return True
        else:
            # Clear hover if mouse moved outside valid game area
            self.game.mouse_hover_world_pos = None
        return False

    def _handle_left_click(self, event: tcod.event.MouseButtonDown) -> bool:
        """Handle left mouse click based on current game state."""
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
            return self._handle_lore_viewer_left_click(event)

        # Gameplay: click adjacent tile to move
        return self._handle_gameplay_left_click(event)

    def _handle_right_click(self, event: tcod.event.MouseButtonDown) -> bool:
        """Handle right mouse click - typically cancel/exit actions."""
        if self.game.look_mode:
            logging.debug("Input: Right-click exiting look mode")
            self.game.look_mode = False
            self.game.message_log.add_message("Look mode exited")
            return True
        elif self.game.targeting_mode:
            logging.debug("Input: Right-click cancelling targeting")
            self.game.targeting_mode = False
            self.game.targeting_exploit = None
            self.game.message_log.add_message("Targeting cancelled")
            return True

        return False

    def _handle_look_mode_left_click(self, event: tcod.event.MouseButtonDown) -> bool:
        """Handle left click in look mode - inspect entity at cursor."""
        world_pos = self._mouse_pixel_to_world(event.position.x, event.position.y)
        if world_pos:
            # Update cursor to clicked position
            self.game.look_cursor_position = world_pos
            # Inspection info is shown automatically in the inspection panel
            logging.debug(f"Input: Look mode left-click at ({world_pos.x},{world_pos.y})")
            return True
        return False

    def _handle_targeting_left_click(self, event: tcod.event.MouseButtonDown) -> bool:
        """Handle left click in targeting mode - execute exploit."""
        world_pos = self._mouse_pixel_to_world(event.position.x, event.position.y)
        if world_pos:
            # Update cursor position
            self.game.cursor_position = world_pos

            # Execute exploit at cursor position (same as pressing Enter)
            if self.game.targeting_exploit:
                logging.debug(f"Input: Targeting left-click executing {self.game.targeting_exploit} at ({world_pos.x},{world_pos.y})")
                self.game.exploit_system.execute_targeted_exploit(
                    self.game.targeting_exploit,
                    world_pos
                )
                # Targeting mode is exited by execute_targeted_exploit
            return True
        return False

    def _handle_gameplay_left_click(self, event: tcod.event.MouseButtonDown) -> bool:
        """Handle left click during gameplay - move to adjacent tile."""
        world_pos = self._mouse_pixel_to_world(event.position.x, event.position.y)

        if not world_pos:
            return False

        # Calculate delta from player position
        dx = world_pos.x - self.game.player.x
        dy = world_pos.y - self.game.player.y

        # Only allow adjacent tile movement (8-directional)
        if abs(dx) <= 1 and abs(dy) <= 1 and (dx != 0 or dy != 0):
            self.game.move_player(dx, dy)
            return True

        return False

    # ============================================================================
    # MENU MOUSE HANDLERS (Phase 3) - Stubs for now
    # ============================================================================

    def _handle_dialogue_mouse_motion(self, event: tcod.event.MouseMotion) -> bool:
        """Handle mouse motion over dialogue - provide visual feedback for hovering.

        Uses stored coordinates from last render to avoid recalculating dimensions.
        Future: Could add visual hover highlighting.
        """
        dialogue = self.game.dialogue_state.get_active()
        if not dialogue:
            return False

        # Use coordinates from last render (don't recalculate!)
        if not self.game.dialogue_state.last_render_coords:
            return False  # Not rendered yet

        coords = self.game.dialogue_state.last_render_coords

        # Convert pixel coordinates to console tile coordinates
        window_w, window_h = self._get_window_dimensions()
        tile_x, tile_y = CoordinateHelpers.pixel_to_char_coords(
            event.position.x, event.position.y, window_w, window_h
        )

        # Check if hovering over dialogue box
        if not (coords['box_x'] <= tile_x < coords['box_x'] + coords['box_width'] and
                coords['box_y'] <= tile_y < coords['box_y'] + coords['box_height']):
            return False  # Not hovering over dialogue

        # Check if hovering over the options row
        if tile_y != coords['options_y']:
            return False  # Not hovering over options

        # Use get_option_at_click to determine which option is being hovered
        # (reuses the same click detection logic for consistency)
        from game_dialogue_system import UnifiedRenderer
        hovered_option = UnifiedRenderer.get_option_at_click(self.game.dialogue_state, tile_x, tile_y)

        if hovered_option is not None:
            # Future: Could set a hover state here that the renderer uses to highlight the option
            return True

        return False

    def _handle_dialogue_left_click(self, event: tcod.event.MouseButtonDown) -> bool:
        """Handle left click on dialogue buttons.

        Dialogues have clickable option buttons like [Y] Confirm, [N] Cancel.
        We need to check if the click is within the dialogue box and on an option.
        """
        from game_dialogue_system import DialogueInputHandler, UnifiedRenderer
        from game_config import GameConfig

        dialogue = self.game.dialogue_state.get_active()
        if not dialogue:
            return False

        # Convert pixel coordinates to console tile coordinates
        # Get context for window size
        context = None
        if self.renderer and hasattr(self.renderer, 'context'):
            context = self.renderer.context
        elif hasattr(self.game, 'context'):
            context = self.game.context

        # Get window dimensions
        if context and hasattr(context, 'sdl_window'):
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
            # Clicked anywhere else - use first/default option (allows click-to-dismiss)
            action = DialogueInputHandler.handle_input(dialogue, dialogue.valid_keys[0])

        # Process the action (same logic as keyboard input)
        if action == "confirm":
            self._handle_dialogue_confirm()
        elif action in ["cancel", "dismiss"]:
            should_continue = self._handle_dialogue_dismiss()
            if not should_continue:
                # This returns via game state, but we return True here
                # because the event was handled
                pass
        elif action == "dont_show_again":
            self._handle_dialogue_dont_show_again()

        return True  # Event was handled

    def _handle_inventory_mouse_motion(self, event: tcod.event.MouseMotion) -> bool:
        """Handle mouse motion in inventory - update selection on hover.

        Uses renderer's single source of truth for coordinate mapping.
        """
        from game_rendering_ui import UIRenderer

        # Convert pixel coordinates to console tile coordinates
        # Try to get context from renderer first, then game
        context = None
        if self.renderer and hasattr(self.renderer, 'context'):
            context = self.renderer.context
        elif hasattr(self.game, 'context'):
            context = self.game.context
        if context and hasattr(context, 'sdl_window'):
            window_w, window_h = context.sdl_window.size
        else:
            window_w, window_h = (800, 600)

        _, tile_y = CoordinateHelpers.pixel_to_char_coords(
            event.position.x, event.position.y, window_w, window_h
        )

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
        if self.renderer and hasattr(self.renderer, 'context'):
            context = self.renderer.context
        elif hasattr(self.game, 'context'):
            context = self.game.context
        if context and hasattr(context, 'sdl_window'):
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

        return False

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

    def _handle_lore_viewer_mouse_motion(self, event: tcod.event.MouseMotion) -> bool:
        """Handle mouse motion in lore viewer - update selection.

        In list mode, hovering over a fragment highlights it.
        In reading mode, no hover effect.
        """
        if self.game.lore_viewer_mode != "list":
            return False

        # Fragment list starts at Y=4 (after header)
        # Each fragment takes 3 lines (title, preview, spacer)

        # Convert pixel coordinates to console tile coordinates
        # Try to get context from renderer first, then game
        context = None
        if self.renderer and hasattr(self.renderer, 'context'):
            context = self.renderer.context
        elif hasattr(self.game, 'context'):
            context = self.game.context
        if context and hasattr(context, 'sdl_window'):
            window_w, window_h = context.sdl_window.size
        else:
            window_w, window_h = (800, 600)

        _, tile_y = CoordinateHelpers.pixel_to_char_coords(
            event.position.x, event.position.y, window_w, window_h
        )

        content_start_y = 4
        if tile_y < content_start_y:
            return False

        # Calculate which fragment was hovered
        relative_y = tile_y - content_start_y
        fragment_index = relative_y // 3  # Each entry is 3 lines tall

        discovered_fragments = self.game.story_fragment_manager.get_discovered_fragments()
        if 0 <= fragment_index < len(discovered_fragments):
            self.game.lore_viewer_selection = fragment_index
            return True

        return False

    def _handle_lore_viewer_left_click(self, event: tcod.event.MouseButtonDown) -> bool:
        """Handle left click in lore viewer - select fragment or toggle mode."""

        # Convert pixel coordinates to console tile coordinates
        # Try to get context from renderer first, then game
        context = None
        if self.renderer and hasattr(self.renderer, 'context'):
            context = self.renderer.context
        elif hasattr(self.game, 'context'):
            context = self.game.context
        if context and hasattr(context, 'sdl_window'):
            window_w, window_h = context.sdl_window.size
        else:
            window_w, window_h = (800, 600)

        _, tile_y = CoordinateHelpers.pixel_to_char_coords(
            event.position.x, event.position.y, window_w, window_h
        )

        if self.game.lore_viewer_mode == "list":
            # Fragment list starts at Y=4
            content_start_y = 4

            if tile_y < content_start_y:
                return False

            # Calculate which fragment was clicked
            relative_y = tile_y - content_start_y
            fragment_index = relative_y // 3  # Each entry is 3 lines tall

            discovered_fragments = self.game.story_fragment_manager.get_discovered_fragments()
            if 0 <= fragment_index < len(discovered_fragments):
                # Select this fragment
                self.game.lore_viewer_selection = fragment_index
                # Enter reading mode (same as pressing Enter)
                self.game.lore_viewer_mode = "reading"
                logging.debug(f"Input: Lore viewer left-click opening fragment {fragment_index}")
                return True

        elif self.game.lore_viewer_mode == "reading":
            # Any click in reading mode returns to list view
            self.game.lore_viewer_mode = "list"
            logging.debug("Input: Lore viewer left-click returning to list mode")
            return True

        return False

    def _handle_lore_viewer_mouse_wheel(self, event: tcod.event.MouseWheel) -> bool:
        """Handle mouse wheel in lore viewer - scroll through fragments."""
        if self.game.lore_viewer_mode != "list":
            return False

        discovered_fragments = self.game.story_fragment_manager.get_discovered_fragments()
        if not discovered_fragments:
            return False

        if event.y > 0:
            # Scroll up (previous fragment)
            self.game.lore_viewer_selection = max(0, self.game.lore_viewer_selection - 1)
            return True
        elif event.y < 0:
            # Scroll down (next fragment)
            max_index = len(discovered_fragments) - 1
            self.game.lore_viewer_selection = min(max_index, self.game.lore_viewer_selection + 1)
            return True

        return False