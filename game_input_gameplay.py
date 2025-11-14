"""
game_input_gameplay.py - Gameplay Input Handler

Handles normal gameplay input including:
- Movement (keyboard and mouse)
- Exploit usage (keyboard number keys and mouse clicks)
- UI button clicks (inventory, exploit bar)
- Auto-walk initiation

This module was extracted from game_input.py to provide focused,
maintainable gameplay interaction logic.
"""

import logging

import tcod.event

from game_coordinate_helpers import CoordinateHelpers
from game_entities import Position
from game_input_coordinates import InputCoordinateConverter


class GameplayInputHandler:
    """Handles gameplay input (movement, exploits, UI buttons)."""

    def __init__(self, game, renderer=None, input_handler=None):
        """
        Initialize gameplay input handler.

        Args:
            game: Game instance
            renderer: Optional GameRenderer instance
            input_handler: Parent InputHandler for accessing helper methods
        """
        self.game = game
        self.renderer = renderer
        self.input_handler = input_handler

    def handle_input(self, event: tcod.event.KeyDown) -> bool:
        """
        Handle keyboard input during normal gameplay.

        Args:
            event: Keyboard event

        Returns:
            True if event was handled
        """
        from game_input import InputMappings

        # Global hotkey: Shift+F12 - Export Debug Package
        if event.sym == tcod.event.KeySym.F12 and (event.mod & tcod.event.Modifier.SHIFT):
            if self.input_handler:
                self.input_handler._trigger_debug_export()
            return True

        # Check if auto-walk is active - cancel on most keys (except UI toggles)
        if self.game.autowalk.is_active():
            # Allow UI toggles without cancelling auto-walk
            ui_toggle_keys = {
                tcod.event.KeySym.SLASH,  # Help (when shift-pressed)
                tcod.event.KeySym.ESCAPE,  # Already handled earlier
            }

            # Cancel auto-walk on any action key (movement, exploits, etc.)
            if event.sym not in ui_toggle_keys:
                self.game.autowalk.cancel()
                # Fall through to process the key normally

        # Movement keys - use shared mapping to avoid duplication
        if event.sym in InputMappings.MOVEMENT_MAP:
            dx, dy = InputMappings.MOVEMENT_MAP[event.sym]
            # Clear mouse hover when using keyboard movement
            self.game.mouse_hover_world_pos = None
            self.game.move_player(dx, dy)

        # Wait/rest
        elif event.sym in (
            tcod.event.KeySym.SPACE,
            tcod.event.KeySym.PERIOD,
            tcod.event.KeySym.KP_5,
        ):
            self.game.maybe_process_turn()

        # UI toggles
        elif event.sym == tcod.event.KeySym.I:
            if self.input_handler:
                self.input_handler._open_inventory()
        elif event.sym == tcod.event.KeySym.L:
            if self.input_handler:
                self.input_handler._enter_look_mode()
        elif event.sym == tcod.event.KeySym.F:
            self.game.show_lore_viewer = True
        elif event.sym == tcod.event.KeySym.SLASH and (
            event.mod & (tcod.event.Modifier.LSHIFT | tcod.event.Modifier.RSHIFT)
        ):
            self.game.show_help = True
        elif event.sym == tcod.event.KeySym.V:
            self.game.show_achievements = True

        # Exploit usage (1-5 keys) - check as loop
        else:
            exploit_keys = {
                tcod.event.KeySym.N1: 0,
                tcod.event.KeySym.N2: 1,
                tcod.event.KeySym.N3: 2,
                tcod.event.KeySym.N4: 3,
                tcod.event.KeySym.N5: 4,
            }
            if event.sym in exploit_keys:
                self.use_exploit_slot(exploit_keys[event.sym])

        return True

    def use_exploit_slot(self, slot: int):
        """
        Use exploit in specified slot.

        Args:
            slot: Exploit slot index (0-4)
        """
        equipped = self.game.player.inventory_manager.equipped_exploits
        if 0 <= slot < len(equipped):
            exploit_key = equipped[slot]
            self.game.exploit_system.use_exploit(exploit_key)
        else:
            logging.debug(f"Input: Exploit slot {slot+1} is empty or invalid")

    def handle_mouse_motion(self, event: tcod.event.MouseMotion) -> bool:
        """
        Handle mouse motion in normal gameplay - update hover position for visual feedback.

        Args:
            event: Mouse motion event

        Returns:
            True if hover position was updated, False otherwise
        """
        graphics_mode = (
            self.game.settings.graphics_mode if hasattr(self.game, "settings") else "glyph"
        )
        world_pos = InputCoordinateConverter.pixel_to_world_position(
            event.position.x, event.position.y, self.renderer, self.game, graphics_mode
        )
        if world_pos:
            self.game.mouse_hover_world_pos = world_pos
            return True
        else:
            # Clear hover if mouse moved outside valid game area
            self.game.mouse_hover_world_pos = None
        return False

    def handle_inv_button_click(self, event: tcod.event.MouseButtonDown) -> bool:
        """
        Handle left click on Inv button in bottom panel.

        Args:
            event: Mouse button down event with pixel position

        Returns:
            True if click was on Inv button, False otherwise
        """
        # Convert pixel coordinates to console tile coordinates
        window_w, window_h = InputCoordinateConverter.get_window_dimensions(
            self.renderer, self.game
        )
        tile_x, tile_y = CoordinateHelpers.pixel_to_char_coords(
            event.position.x, event.position.y, window_w, window_h
        )

        # Inv button is on bottom row (must match rendering code)
        from game_config import GameConfig

        inv_button_y = GameConfig.SCREEN_HEIGHT - 1
        if tile_y != inv_button_y:
            return False

        # Calculate Inv button position (must match rendering code)
        inv_button_text = "[Inv]"
        inv_button_x = GameConfig.SCREEN_WIDTH - len(inv_button_text) - 1
        inv_button_end_x = inv_button_x + len(inv_button_text)

        # Check if click is within Inv button bounds
        if inv_button_x <= tile_x < inv_button_end_x:
            if self.input_handler:
                self.input_handler._open_inventory()
            return True

        return False

    def handle_exploit_bar_click(self, event: tcod.event.MouseButtonDown) -> bool:
        """
        Handle left click on exploit bar - activate the clicked exploit.

        Converts pixel coordinates to console tile coordinates and checks if an exploit
        was clicked using UIRenderer's stored positions. If clicked, activates that exploit
        (same as pressing 1-5 keys).

        Args:
            event: Mouse button down event with pixel position

        Returns:
            True if an exploit was clicked, False otherwise
        """
        from game_rendering_ui import UIRenderer

        # Convert pixel coordinates to console tile coordinates
        window_w, window_h = InputCoordinateConverter.get_window_dimensions(
            self.renderer, self.game
        )
        tile_x, tile_y = CoordinateHelpers.pixel_to_char_coords(
            event.position.x, event.position.y, window_w, window_h
        )

        # Check if an exploit was clicked
        exploit_slot = UIRenderer.get_exploit_at_click(tile_x, tile_y)

        if exploit_slot is not None:
            # Activate the exploit (same as pressing the number key)
            self.use_exploit_slot(exploit_slot)
            return True

        return False

    def handle_left_click(self, event: tcod.event.MouseButtonDown) -> bool:
        """
        Handle left click during gameplay - move to tile or start auto-walk.

        Clicking behavior:
        - Adjacent tile (8-directional): Immediate movement
        - Distant tile: Start auto-walk pathfinding
        - Player position: Pass turn (like spacebar)

        Args:
            event: Mouse button down event

        Returns:
            True (event is always consumed in gameplay)
        """
        graphics_mode = (
            self.game.settings.graphics_mode if hasattr(self.game, "settings") else "glyph"
        )
        world_pos = InputCoordinateConverter.pixel_to_world_position(
            event.position.x, event.position.y, self.renderer, self.game, graphics_mode
        )

        if not world_pos:
            # Click was outside valid game area - still handled, just ignored
            return True

        # Calculate delta from player position
        dx = world_pos.x - self.game.player.x
        dy = world_pos.y - self.game.player.y

        # If clicking on player position, pass turn (like spacebar)
        if dx == 0 and dy == 0:
            self.game.move_player(0, 0)  # Pass turn
            return True

        # Adjacent tile: immediate movement (8-directional)
        if abs(dx) <= 1 and abs(dy) <= 1:
            self.game.move_player(dx, dy)
            return True

        # Distant tile: start auto-walk using TCOD pathfinding
        player_pos = Position(self.game.player.x, self.game.player.y)
        if self.game.autowalk.start(player_pos, world_pos, self.game):
            logging.info(f"Started auto-walk to {world_pos}")
            return True
        else:
            # No path found - event was handled, just no action taken
            logging.debug(f"No path to {world_pos}")
            return True
