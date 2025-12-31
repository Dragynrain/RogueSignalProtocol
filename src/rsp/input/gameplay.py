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

from rsp.rendering.coordinates import CoordinateHelpers
from rsp.entities.base import Position
from rsp.input.actions import InputAction, InputContext
from rsp.input.base import BaseInputHandler
from rsp.input.coordinates import InputCoordinateConverter


class GameplayInputHandler(BaseInputHandler):
    """Handles gameplay input (movement, exploits, UI buttons)."""

    def __init__(
        self, game, renderer=None, input_mapper=None, controllers=None, gamepad_handler=None
    ):
        """
        Initialize gameplay input handler.

        Args:
            game: Game instance
            renderer: Optional GameRenderer instance
            input_mapper: Shared InputMapper instance (for consistent bindings)
            controllers: Set of connected controllers for gamepad input
            gamepad_handler: Shared GamepadInputHandler instance (for consistent state)
        """
        # Initialize BaseInputHandler with shared InputMapper, controllers, and gamepad_handler
        super().__init__(
            game,
            renderer,
            input_mapper=input_mapper,
            controllers=controllers,
            gamepad_handler=gamepad_handler,
        )

    def get_context(self) -> InputContext:
        """Get current input context for gameplay."""
        return InputContext.GAMEPLAY

    def get_default_return(self) -> bool:
        """Gameplay handler returns True by default (event consumed)."""
        return True

    # NOTE: handle_input() inherited from BaseInputHandler handles keyboard, gamepad, and mouse.
    # Do NOT override - the base class routes events through execute_action() correctly.
    # Auto-walk cancellation and DEBUG_EXPORT are handled in execute_action().

    def use_exploit_slot(self, slot: int) -> bool:
        """
        Use exploit in specified slot.

        Args:
            slot: Exploit slot index (0-4)

        Returns:
            True after attempting to use the exploit slot
        """
        equipped = self.game.player.inventory_manager.equipped_exploits
        if 0 <= slot < len(equipped):
            exploit_key = equipped[slot]
            self.game.exploit_system.use_exploit(exploit_key)
        else:
            logging.debug(f"Input: Exploit slot {slot+1} is empty or invalid")
        return True

    def open_inventory(self):
        """Open the inventory screen with sound effect."""
        self.game.sound_manager.play_sound("ui_menu_open")
        self.game.show_inventory = True

    def enter_look_mode(self):
        """Enter look mode with sound effect, starting cursor at player position."""
        self.game.look_mode_mouse_last_update = 0.0
        self.game.sound_manager.play_sound("ui_menu_open")
        self.game.look_mode = True
        self.game.look_cursor_position = Position(self.game.player.x, self.game.player.y)
        self.game.message_log.add_message("Look mode activated (ESC or L to exit)")

    def trigger_debug_export(self):
        """Trigger debug package export with confirmation dialog."""
        from rsp.ui.dialogue import DialogueBox
        from rsp.entities.base import Colors

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

        self.game.dialogue_state.show(dialogue)
        self.game._pending_debug_export = True

    def handle_mouse_motion(self, event: tcod.event.MouseMotion) -> bool:
        """
        Handle mouse motion in normal gameplay - update hover position for visual feedback.

        Args:
            event: Mouse motion event

        Returns:
            True if hover position was updated, False otherwise
        """
        graphics_mode = (
            self.game.settings.graphics_mode
            if hasattr(self.game, "settings") and self.game.settings is not None
            else "glyph"
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
        from rsp.core.config import GameConfig

        inv_button_y = GameConfig.SCREEN_HEIGHT - 1
        if tile_y != inv_button_y:
            return False

        # Calculate Inv button position (must match rendering code)
        inv_button_text = "[Inv]"
        inv_button_x = GameConfig.SCREEN_WIDTH - len(inv_button_text) - 1
        inv_button_end_x = inv_button_x + len(inv_button_text)

        # Check if click is within Inv button bounds
        if inv_button_x <= tile_x < inv_button_end_x:
            self.open_inventory()
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
        from rsp.rendering.ui import UIRenderer

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
            self.game.settings.graphics_mode
            if hasattr(self.game, "settings") and self.game.settings is not None
            else "glyph"
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

    # Actions that don't cancel auto-walk (UI toggles that overlay gameplay)
    _NO_CANCEL_AUTOWALK_ACTIONS = frozenset({
        InputAction.TOGGLE_HELP,
        InputAction.TOGGLE_INVENTORY,
        InputAction.TOGGLE_LOOK_MODE,
        InputAction.TOGGLE_LORE_VIEWER,
        InputAction.TOGGLE_ACHIEVEMENTS,
        InputAction.TOGGLE_ASCENSION,
        InputAction.CANCEL,
        InputAction.DEBUG_EXPORT,
    })

    def execute_action(self, action: InputAction) -> bool:
        """
        Execute an InputAction in gameplay context.

        Translates abstract actions to concrete game logic. Reuses existing methods
        to avoid duplication.

        Args:
            action: The InputAction to execute

        Returns:
            True if action was handled
        """
        # Cancel auto-walk on most actions (except UI toggles)
        if self.game.autowalk.is_active():
            if action not in self._NO_CANCEL_AUTOWALK_ACTIONS:
                self.game.autowalk.cancel()

        # Debug export (Shift+F12)
        if action == InputAction.DEBUG_EXPORT:
            self.trigger_debug_export()
            return True

        # Clear mouse hover when using keyboard/gamepad movement
        if action in (
            InputAction.MOVE_NORTH,
            InputAction.MOVE_SOUTH,
            InputAction.MOVE_EAST,
            InputAction.MOVE_WEST,
            InputAction.MOVE_NORTHEAST,
            InputAction.MOVE_NORTHWEST,
            InputAction.MOVE_SOUTHEAST,
            InputAction.MOVE_SOUTHWEST,
        ):
            self.game.mouse_hover_world_pos = None

        # Movement actions
        if action == InputAction.MOVE_NORTH:
            self.game.move_player(0, -1)
            return True
        elif action == InputAction.MOVE_SOUTH:
            self.game.move_player(0, 1)
            return True
        elif action == InputAction.MOVE_EAST:
            self.game.move_player(1, 0)
            return True
        elif action == InputAction.MOVE_WEST:
            self.game.move_player(-1, 0)
            return True
        elif action == InputAction.MOVE_NORTHEAST:
            self.game.move_player(1, -1)
            return True
        elif action == InputAction.MOVE_NORTHWEST:
            self.game.move_player(-1, -1)
            return True
        elif action == InputAction.MOVE_SOUTHEAST:
            self.game.move_player(1, 1)
            return True
        elif action == InputAction.MOVE_SOUTHWEST:
            self.game.move_player(-1, 1)
            return True

        # Wait/pass turn
        elif action == InputAction.WAIT:
            self.game.move_player(0, 0)
            return True

        # Exploit direct slots (keyboard 1-5 keys)
        elif action == InputAction.EXPLOIT_SLOT_1:
            return self.use_exploit_slot(0)
        elif action == InputAction.EXPLOIT_SLOT_2:
            return self.use_exploit_slot(1)
        elif action == InputAction.EXPLOIT_SLOT_3:
            return self.use_exploit_slot(2)
        elif action == InputAction.EXPLOIT_SLOT_4:
            return self.use_exploit_slot(3)
        elif action == InputAction.EXPLOIT_SLOT_5:
            return self.use_exploit_slot(4)

        # NEW: Gamepad exploit cycling (RB/LB buttons)
        elif action == InputAction.EXPLOIT_CYCLE_NEXT:
            self.game.cycle_exploit_selection(+1)
            return True
        elif action == InputAction.EXPLOIT_CYCLE_PREV:
            self.game.cycle_exploit_selection(-1)
            return True

        # NEW: Execute selected exploit (RT trigger)
        elif action == InputAction.EXPLOIT_EXECUTE:
            # Get currently selected exploit index
            equipped_exploits = self.game.player.inventory_manager.equipped_exploits
            if equipped_exploits and self.game.selected_exploit_index < len(equipped_exploits):
                # Use the selected slot directly
                return self.use_exploit_slot(self.game.selected_exploit_index)
            return True  # Handled but no action (no exploits equipped)

        # UI toggles
        elif action == InputAction.TOGGLE_INVENTORY:
            self.open_inventory()
            return True
        elif action == InputAction.TOGGLE_LOOK_MODE:
            self.enter_look_mode()
            return True
        elif action == InputAction.TOGGLE_HELP:
            self.game.show_help = True
            return True
        elif action == InputAction.TOGGLE_LORE_VIEWER:
            # Only open lore viewer if renderer is available (not in headless tests)
            if self.renderer:
                self.game.show_lore_viewer = True
            return True
        elif action == InputAction.TOGGLE_ACHIEVEMENTS:
            self.game.show_achievements = True
            return True
        elif action == InputAction.TOGGLE_ASCENSION:
            self.game.show_ascension = True
            return True

        # ESC/Cancel in gameplay is handled at game_loop level (not here)
        # Return True to indicate "event processed, continue playing"
        elif action == InputAction.CANCEL:
            return True

        # Unknown action - consume it but continue playing
        return True
