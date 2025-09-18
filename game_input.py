"""
Game Input Module - Handles player input and translates to game actions
"""

import tcod
import tcod.event
from game_combat import ExploitSystem
from game_data import GameData
from game_inventory import CodeHack, ExploitItem
from game_ui import UniversalInputHandler


class InputHandler:
    """Handles all user input and translates it to game actions."""
    
    def __init__(self, game):
        self.game = game
        self.exploit_system = ExploitSystem(game)
    
    def handle_keydown(self, event: tcod.event.KeyDown) -> bool:
        """Handle keydown events.
        
        Args:
            event: The keyboard event to process
            
        Returns:
            True if game should continue, False if should exit
        """        
        # Dead/game over state - any key should exit to main menu
        if self.game.player.cpu <= 0 or self.game.game_over:
            # Exit to main menu instead of showing pause menu when dead
            return False
        
        # Modal screens - handle non-escape keys
        if self.game.show_help:
            self.game.show_help = False
            return True
        
        if self.game.show_story_fragment is not None:
            # Any key closes the story fragment display
            self.game.show_story_fragment = None
            return True
        
        if self.game.show_lore_viewer:
            return self._handle_lore_viewer_input(event)
        
        if self.game.show_gateway_confirmation:
            return self._handle_gateway_confirmation_input(event)
        
        if self.game.show_inventory:
            return self._handle_inventory_input(event)
        
        if self.game.targeting_mode:
            return self._handle_targeting_input(event)
        
        # Normal gameplay
        return self._handle_gameplay_input(event)
    
    def _handle_escape(self) -> bool:
        """Handle escape key for UI states."""
        if self.game.show_story_fragment is not None:
            self.game.show_story_fragment = None
        elif self.game.show_lore_viewer:
            self.game.show_lore_viewer = False
            self.game.lore_viewer_mode = "list"
            self.game.lore_viewer_selection = 0
        elif self.game.show_help:
            self.game.show_help = False
        elif self.game.show_gateway_confirmation:
            self.game.show_gateway_confirmation = False
        elif self.game.show_inventory:
            self.game.show_inventory = False
        elif self.game.targeting_mode:
            self.game.targeting_mode = False
            self.game.targeting_exploit = None
            self.game.message_log.add_message("Targeting cancelled")
        return True
    
    def _handle_gateway_confirmation_input(self, event) -> bool:
        """Handle input for gateway confirmation dialog."""
        if UniversalInputHandler.is_confirm_key(event) or event.sym == tcod.event.KeySym.Y:
            # Yes - proceed to next level
            self.game.show_gateway_confirmation = False
            self.game.sound_manager.play_sound("level_complete")
            self.game.message_log.add_message("Gateway reached! Next network...")
            self.game.next_level()
        elif event.sym == tcod.event.KeySym.N or UniversalInputHandler.is_escape_key(event):
            # No - cancel and don't waste turn
            self.game.show_gateway_confirmation = False
            self.game.message_log.add_message("Staying in current network")
        
        return True
    
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
            elif UniversalInputHandler.is_escape_key(event):
                # Let main loop handle ESC
                return False
        
        elif self.game.lore_viewer_mode == "reading":
            # Reading mode - any key except ESC returns to list
            if UniversalInputHandler.is_escape_key(event):
                # Let main loop handle ESC
                return False
            else:
                # Any other key returns to list
                self.game.lore_viewer_mode = "list"
                return True
        
        # Unhandled key - let other handlers process it
        return False
    
    def _navigate_lore_viewer(self, direction: int):
        """Navigate lore viewer selection."""
        discovered_fragments = self.game.story_fragment_manager.get_discovered_fragments()
        if discovered_fragments:
            if direction == -1:
                self.game.lore_viewer_selection = max(0, self.game.lore_viewer_selection - 1)
            else:
                self.game.lore_viewer_selection = min(len(discovered_fragments) - 1, self.game.lore_viewer_selection + 1)
    
    def _handle_targeting_input(self, event) -> bool:
        """Handle input while in targeting mode."""
        # Movement keys - expanded to include numpad and arrows
        movement_map = {
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
        
        if event.sym in movement_map:
            dx, dy = movement_map[event.sym]
            self.game._move_cursor(dx, dy)
        elif event.sym in (tcod.event.KeySym.RETURN, tcod.event.KeySym.KP_ENTER):
            self.exploit_system.execute_exploit(
                self.game.targeting_exploit, 
                self.game.cursor_position
            )
        
        return True
    
    def _handle_gameplay_input(self, event) -> bool:
        """Handle input during normal gameplay."""
        # Movement keys - expanded to include numpad and arrows
        movement_map = {
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
        
        if event.sym in movement_map:
            dx, dy = movement_map[event.sym]
            self.game.move_player(dx, dy)
        
        # Wait/rest
        elif event.sym in (tcod.event.KeySym.SPACE, tcod.event.KeySym.PERIOD, tcod.event.KeySym.KP_5):
            self.game.maybe_process_turn()
        
        # UI toggles
        elif event.sym == tcod.event.KeySym.I:
            self._open_inventory()
        elif event.sym == tcod.event.KeySym.L:
            self.game.show_lore_viewer = True
        elif event.sym == tcod.event.KeySym.SLASH and (event.mod & (tcod.event.Modifier.LSHIFT | tcod.event.Modifier.RSHIFT)):
            self.game.show_help = True
        
        # Exploit usage (1-5 keys)
        elif event.sym == tcod.event.KeySym.N1:
            self._use_exploit_slot(0)
        elif event.sym == tcod.event.KeySym.N2:
            self._use_exploit_slot(1)
        elif event.sym == tcod.event.KeySym.N3:
            self._use_exploit_slot(2)
        elif event.sym == tcod.event.KeySym.N4:
            self._use_exploit_slot(3)
        elif event.sym == tcod.event.KeySym.N5:
            self._use_exploit_slot(4)
        
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
                    # Check if it was a code - if so, advance turn
                    if isinstance(selected_item, CodeHack):
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
                # Add the exploit back to inventory as an item
                exploit_def = GameData.EXPLOITS[exploit_key]
                exploit_item = ExploitItem(exploit_key, exploit_def)
                self.game.player.inventory_manager.add_item(exploit_item)
                self.game.message_log.add_message(f"Unequipped {exploit_def.name}")
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
                # Data patch
                self._show_data_patch_details(selected_item)
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
    
    def _show_data_patch_details(self, data_patch):
        """Show detailed information about a code."""
        if data_patch.discovered:
            if data_patch.color_name in self.game.data_patch_effects:
                effect_key, desc = self.game.data_patch_effects[data_patch.color_name]
                self.game.message_log.add_message(f"=== {data_patch.name} ===")
                self.game.message_log.add_message(f"Effect: {desc}")
                if data_patch.quantity > 1:
                    self.game.message_log.add_message(f"Quantity: {data_patch.quantity}")
            else:
                self.game.message_log.add_message("Code effect unknown")
        else:
            self.game.message_log.add_message(f"=== {data_patch.name} ===")
            self.game.message_log.add_message("Effect: Unknown until used")
            if data_patch.quantity > 1:
                self.game.message_log.add_message(f"Quantity: {data_patch.quantity}")
    
    def _open_inventory(self):
        """Open the inventory screen."""
        self.game.sound_manager.play_sound("ui_menu_open")
        self.game.show_inventory = True
        self.game.inventory_selection = 0
    
    def _use_exploit_slot(self, slot: int):
        """Use exploit in specified slot."""
        equipped = self.game.player.inventory_manager.equipped_exploits
        if 0 <= slot < len(equipped):
            self.exploit_system.use_exploit(equipped[slot])