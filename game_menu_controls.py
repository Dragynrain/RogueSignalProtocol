#!/usr/bin/env python3
"""
Rogue Signal Protocol - Controls Configuration Menu

Provides settings configuration for:
- Keyboard bindings (full remapping)
- Gamepad bindings (full remapping)
- Gamepad settings (deadzone, threshold, direction locking)

Phase 4 & 5 implementation of PLAN_GAMEPAD.md.
"""

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import tcod
import tcod.event
import tcod.sdl.joystick

from game_config import GameConfig, GameSettings
from game_entities import Colors
from game_help_hints import (
    get_controls_hub_help,
    get_gamepad_binding_instructions,
    get_gamepad_bindings_help,
    get_gamepad_settings_help,
    get_keyboard_bindings_help,
)
from game_input_actions import InputAction, InputContext
from game_input_mappings import (
    MODIFIER_ONLY_KEYS,
    RESERVED_BUTTONS,
    RESERVED_KEYS,
    axis_to_display_name,
    button_to_display_name,
)
from game_menu_base import BaseMenu
from game_screen_utilities import ScreenRenderingUtils, ScrollableListManager
from game_ui import render_char_safe

if TYPE_CHECKING:
    from game_input_mappings import InputMapper


# Gamepad action categories organized by context tab
# Users can switch between Gameplay and Menus tabs to customize different contexts
# Structure matches keyboard ACTION_CATEGORIES for consistency
GAMEPAD_GAMEPLAY_CATEGORIES = [
    (
        "MOVEMENT",
        [
            InputAction.MOVE_NORTH,
            InputAction.MOVE_SOUTH,
            InputAction.MOVE_WEST,
            InputAction.MOVE_EAST,
        ],
    ),
    (
        "ACTIONS",
        [
            InputAction.WAIT,
            InputAction.CANCEL,  # B button in gameplay (exit modes, etc.)
            InputAction.EXIT_TO_MENU,
        ],
    ),
    (
        "EXPLOITS",
        [
            InputAction.EXPLOIT_SLOT_1,
            InputAction.EXPLOIT_CYCLE_PREV,
            InputAction.EXPLOIT_CYCLE_NEXT,
            InputAction.EXPLOIT_EXECUTE,
        ],
    ),
    (
        "UI TOGGLES",
        [
            InputAction.TOGGLE_INVENTORY,
            InputAction.TOGGLE_LOOK_MODE,
            InputAction.TOGGLE_HELP,
            InputAction.TOGGLE_LORE_VIEWER,
            InputAction.TOGGLE_ACHIEVEMENTS,
        ],
    ),
]

# Menu navigation bindings (applies to inventory, help, settings, etc.)
GAMEPAD_MENU_CATEGORIES = [
    (
        "NAVIGATION",
        [
            InputAction.CONFIRM,
            InputAction.CANCEL,
            InputAction.NAVIGATE_UP,
            InputAction.NAVIGATE_DOWN,
            InputAction.NAVIGATE_LEFT,
            InputAction.NAVIGATE_RIGHT,
            InputAction.NAVIGATE_PAGE_UP,
            InputAction.NAVIGATE_PAGE_DOWN,
        ],
    ),
]

# For backwards compatibility
GAMEPAD_ACTION_CATEGORIES = GAMEPAD_GAMEPLAY_CATEGORIES

# Action categories for display (keyboard bindings)
# Organized to match gamepad structure for consistency
ACTION_CATEGORIES = [
    (
        "MOVEMENT",
        [
            InputAction.MOVE_NORTH,
            InputAction.MOVE_SOUTH,
            InputAction.MOVE_EAST,
            InputAction.MOVE_WEST,
            InputAction.MOVE_NORTHEAST,
            InputAction.MOVE_NORTHWEST,
            InputAction.MOVE_SOUTHEAST,
            InputAction.MOVE_SOUTHWEST,
        ],
    ),
    (
        "ACTIONS",
        [
            InputAction.WAIT,
            InputAction.CONFIRM,
            InputAction.CANCEL,
            InputAction.EXIT_TO_MENU,
        ],
    ),
    (
        "EXPLOITS",
        [
            InputAction.EXPLOIT_SLOT_1,
            InputAction.EXPLOIT_SLOT_2,
            InputAction.EXPLOIT_SLOT_3,
            InputAction.EXPLOIT_SLOT_4,
            InputAction.EXPLOIT_SLOT_5,
            InputAction.EXPLOIT_CYCLE_PREV,
            InputAction.EXPLOIT_CYCLE_NEXT,
            InputAction.EXPLOIT_EXECUTE,
        ],
    ),
    (
        "UI TOGGLES",
        [
            InputAction.TOGGLE_INVENTORY,
            InputAction.TOGGLE_LOOK_MODE,
            InputAction.TOGGLE_HELP,
            InputAction.TOGGLE_LORE_VIEWER,
            InputAction.TOGGLE_ACHIEVEMENTS,
        ],
    ),
]

# Human-readable action names
ACTION_DISPLAY_NAMES = {
    InputAction.MOVE_NORTH: "Move North",
    InputAction.MOVE_SOUTH: "Move South",
    InputAction.MOVE_EAST: "Move East",
    InputAction.MOVE_WEST: "Move West",
    InputAction.MOVE_NORTHEAST: "Move Northeast",
    InputAction.MOVE_NORTHWEST: "Move Northwest",
    InputAction.MOVE_SOUTHEAST: "Move Southeast",
    InputAction.MOVE_SOUTHWEST: "Move Southwest",
    InputAction.WAIT: "Wait / Pass Turn",
    InputAction.CONFIRM: "Confirm / Select",
    InputAction.CANCEL: "Cancel / Back",
    InputAction.EXPLOIT_SLOT_1: "Exploit Slot 1",
    InputAction.EXPLOIT_SLOT_2: "Exploit Slot 2",
    InputAction.EXPLOIT_SLOT_3: "Exploit Slot 3",
    InputAction.EXPLOIT_SLOT_4: "Exploit Slot 4",
    InputAction.EXPLOIT_SLOT_5: "Exploit Slot 5",
    InputAction.EXPLOIT_CYCLE_PREV: "Cycle Exploit Prev",
    InputAction.EXPLOIT_CYCLE_NEXT: "Cycle Exploit Next",
    InputAction.EXPLOIT_EXECUTE: "Execute Selected Exploit",
    InputAction.TOGGLE_INVENTORY: "Toggle Inventory",
    InputAction.TOGGLE_LOOK_MODE: "Toggle Look Mode",
    InputAction.TOGGLE_LORE_VIEWER: "Toggle Lore Viewer",
    InputAction.TOGGLE_ACHIEVEMENTS: "Toggle Achievements",
    InputAction.TOGGLE_HELP: "Toggle Help",
    InputAction.EXIT_TO_MENU: "Main Menu",
    InputAction.NAVIGATE_UP: "Navigate Up",
    InputAction.NAVIGATE_DOWN: "Navigate Down",
    InputAction.NAVIGATE_LEFT: "Navigate Left",
    InputAction.NAVIGATE_RIGHT: "Navigate Right",
    InputAction.NAVIGATE_PAGE_UP: "Page Up",
    InputAction.NAVIGATE_PAGE_DOWN: "Page Down",
    InputAction.DIALOGUE_SKIP_WARNING: "Don't Warn Again",
}


# =============================================================================
# CONTROLS MENU HUB
# =============================================================================


class ControlsMenuHub(BaseMenu):
    """
    Main controls configuration hub.

    Provides access to:
    - Keyboard Bindings
    - Gamepad Bindings
    - Gamepad Settings
    """

    def __init__(
        self,
        settings: GameSettings,
        input_mapper: "InputMapper | None" = None,
        menu_background=None,
    ):
        super().__init__(menu_background)
        self.settings = settings  # Store settings for UI color access
        # Ensure input_mapper exists - create default if not provided
        if input_mapper is not None:
            self.input_mapper = input_mapper
        elif not hasattr(self, "input_mapper") or self.input_mapper is None:
            from game_input_mappings import InputMapper

            self.input_mapper = InputMapper()
        self.options = [
            "Keyboard Bindings",
            "Gamepad Bindings",
            "Gamepad Settings",
            "Back",
        ]

    def render(self, console: tcod.console.Console) -> None:
        """Render the controls hub menu."""
        if self._has_background():
            self._clear_text_areas_only(console)
        else:
            console.clear()

        # Get UI color for decorations
        ui_color = self.settings.get_ui_color_rgb()

        # Calculate menu height
        menu_height = GameConfig.SCREEN_HEIGHT - 4

        # Render the right-side box using common method
        box = self._render_right_side_box(console, menu_height, ui_color, y_offset=3)

        # Title
        title = "CONTROLS"
        render_char_safe(
            console,
            box["center_x"] - len(title) // 2,
            box["top"] + 2,
            title,
            fg=Colors.WHITE,
            bg=Colors.BLACK,
        )

        # Options
        start_y = box["top"] + 6
        spacing = 3 if box["use_background_layout"] else 2

        for i, option in enumerate(self.options):
            if i == self.selected_option:
                color = Colors.YELLOW
                bg_color = Colors.DEEP_PURPLE
            else:
                color = Colors.WHITE
                bg_color = Colors.BLACK
            option_y = start_y + i * spacing

            # Center option text
            option_x = box["center_x"] - len(option) // 2

            render_char_safe(console, option_x, option_y, option, fg=color, bg=bg_color)

        # Instructions - dynamically reflects current bindings
        instructions = get_controls_hub_help(box["use_background_layout"], self.input_mapper)

        # Ensure instructions fit within box content area
        max_width = box.get("content_width", box["width"] - 2)
        if len(instructions) > max_width:
            # Truncate if somehow still too long
            instructions = instructions[: max_width - 3] + "..."

        inst_x = box["center_x"] - len(instructions) // 2
        render_char_safe(
            console,
            inst_x,
            box["bottom"] - 3,
            instructions,
            fg=Colors.LIGHT_GRAY,
            bg=Colors.BLACK,
        )

    def get_context(self):
        """Return input context for this menu."""
        return InputContext.CONTROLS_MENU

    def execute_action(self, action) -> str:
        """Execute an InputAction and return menu command."""
        # Navigation
        if action in (InputAction.NAVIGATE_UP, InputAction.MOVE_NORTH):
            self.selected_option = (self.selected_option - 1) % len(self.options)
            return ""
        elif action in (InputAction.NAVIGATE_DOWN, InputAction.MOVE_SOUTH):
            self.selected_option = (self.selected_option + 1) % len(self.options)
            return ""

        # Confirm/Select
        elif action == InputAction.CONFIRM:
            if not self.options or not (0 <= self.selected_option < len(self.options)):
                return ""
            option = self.options[self.selected_option]
            if option.startswith("Keyboard Bindings"):
                return "keyboard_bindings"
            elif option.startswith("Gamepad Bindings"):
                return "gamepad_bindings"
            elif option == "Gamepad Settings":
                return "gamepad_settings"
            elif option == "Back":
                return "back"
            return ""

        # Cancel/Back
        elif action == InputAction.CANCEL:
            return "back"

        return ""

    def _get_action_for_option(self, option_index: int) -> str | None:
        """Get action string for a menu option (for mouse clicks)."""
        if option_index < 0 or option_index >= len(self.options):
            return None

        option = self.options[option_index]
        if option.startswith("Keyboard Bindings"):
            return "keyboard_bindings"
        elif option.startswith("Gamepad Bindings"):
            return "gamepad_bindings"
        elif option == "Gamepad Settings":
            return "gamepad_settings"
        elif option == "Back":
            return "back"
        return None


# =============================================================================
# BASE BINDINGS MENU (Abstract Base Class)
# =============================================================================


class BaseBindingsMenu(BaseMenu, ABC):
    """
    Abstract base class for keyboard and gamepad binding menus.

    Provides shared functionality:
    - Scrollable list of actions with bindings
    - Binding mode overlay for capturing input
    - Conflict detection and resolution dialog
    - Navigation and selection handling

    Subclasses must implement input-specific methods for:
    - Getting current bindings for actions
    - Handling binding capture input
    - Handling conflict resolution input
    - Saving/resetting bindings
    """

    # Scroll speed configuration (shared defaults, subclasses can override)
    ARROW_SCROLL_SPEED = 1
    PAGE_SCROLL_SPEED = 10
    WHEEL_SCROLL_SPEED = 3

    def __init__(self, settings: GameSettings, input_mapper: "InputMapper", menu_background=None):
        super().__init__(menu_background)
        self.settings = settings
        self.input_mapper = input_mapper

        # Build list of bindable items (categories + actions)
        self._build_action_list()

        # Scroll state - subclasses may adjust max_visible_lines
        self.max_visible_lines = GameConfig.SCREEN_HEIGHT - 11
        self.scroll_manager = ScrollableListManager(
            total_items=len(self.display_items), visible_height=self.max_visible_lines
        )

        # Binding mode state
        self.binding_mode = False
        self.binding_action: InputAction | None = None

        # Conflict dialog state
        self.show_conflict_dialog = False
        self.conflict_actions: list[InputAction] = []
        self.conflict_selection = 0  # 0 = Yes, 1 = No

    # =========================================================================
    # ABSTRACT METHODS (subclasses must implement)
    # =========================================================================

    @abstractmethod
    def _get_title(self) -> str:
        """Return the menu title (e.g., 'KEYBOARD BINDINGS')."""
        pass

    @abstractmethod
    def _get_subtitle(self) -> str:
        """Return the menu subtitle."""
        pass

    @abstractmethod
    def _get_action_categories(self) -> list:
        """Return list of (category_name, [actions]) tuples."""
        pass

    @abstractmethod
    def _get_bindings_for_action(self, action: InputAction) -> list[str]:
        """Return list of binding display strings for an action."""
        pass

    @abstractmethod
    def _has_custom_bindings(self, action: InputAction) -> bool:
        """Check if action has custom bindings."""
        pass

    @abstractmethod
    def _get_help_text(self) -> tuple[str, str | None]:
        """Return (main_help, additional_help) tuple for footer."""
        pass

    @abstractmethod
    def _handle_binding_input(self, event) -> str:
        """Handle input while in binding mode. Return action string."""
        pass

    @abstractmethod
    def _handle_conflict_input(self, event) -> str:
        """Handle input in conflict dialog. Return action string."""
        pass

    @abstractmethod
    def _render_binding_overlay_content(
        self, console: tcod.console.Console, box_x: int, box_y: int, box_width: int
    ) -> None:
        """Render input-specific content in the binding overlay."""
        pass

    @abstractmethod
    def _render_conflict_info(
        self, console: tcod.console.Console, box_x: int, box_y: int, box_width: int
    ) -> None:
        """Render input-specific conflict information."""
        pass

    @abstractmethod
    def _reset_to_defaults(self) -> None:
        """Reset all bindings to defaults."""
        pass

    @abstractmethod
    def _save_bindings(self) -> None:
        """Save custom bindings to settings."""
        pass

    @abstractmethod
    def _handle_reset_key(self, event) -> bool:
        """Handle reset key press. Return True if handled."""
        pass

    # =========================================================================
    # SHARED IMPLEMENTATION
    # =========================================================================

    def _build_action_list(self):
        """Build the list of display items (categories and actions)."""
        self.display_items = []
        self.selectable_indices = []

        for category_name, actions in self._get_action_categories():
            # Add category header (not selectable)
            self.display_items.append(
                {
                    "type": "category",
                    "name": category_name,
                }
            )
            # Add blank line after header
            self.display_items.append({"type": "blank"})

            # Add actions (selectable)
            for action in actions:
                self.selectable_indices.append(len(self.display_items))
                self.display_items.append(
                    {
                        "type": "action",
                        "action": action,
                        "name": ACTION_DISPLAY_NAMES.get(action, action.name),
                    }
                )

            # Add blank line after category
            self.display_items.append({"type": "blank"})

        # Current selection is an index into selectable_indices
        self.selected_index = 0

    def render(self, console: tcod.console.Console) -> None:
        """Render the bindings menu."""
        console.clear()

        # Render binding mode overlay if active
        if self.binding_mode:
            self._render_binding_overlay(console)
            return

        # Render conflict dialog if active
        if self.show_conflict_dialog:
            self._render_conflict_dialog(console)
            return

        # Render main content
        self._render_main_content(console)

    def _render_main_content(self, console: tcod.console.Console) -> None:
        """Render the main bindings list. Subclasses can override for custom headers."""
        # Header
        content_start_y = ScreenRenderingUtils.render_screen_header(
            console,
            self._get_title(),
            subtitle=self._get_subtitle(),
            border_color=Colors.CYAN,
            title_color=Colors.CYAN,
        )

        # Hook for subclass-specific content (e.g., tab selector)
        content_start_y = self._render_header_extras(console, content_start_y)

        # Update scroll manager
        self.scroll_manager.set_total_items(len(self.display_items))

        # Ensure selection is visible
        if self.selectable_indices and 0 <= self.selected_index < len(self.selectable_indices):
            actual_index = self.selectable_indices[self.selected_index]
            self.scroll_manager.adjust_for_selection(actual_index)

        # Get visible range
        start_idx, end_idx = self.scroll_manager.get_visible_range()

        # Render visible items
        y = content_start_y
        for i in range(start_idx, min(end_idx, len(self.display_items))):
            item = self.display_items[i]

            if item["type"] == "category":
                header_text = f"=== {item['name']} ==="
                render_char_safe(console, 4, y, header_text, fg=Colors.ELECTRIC_PURPLE)
            elif item["type"] == "action":
                is_selected = (
                    self.selectable_indices and i == self.selectable_indices[self.selected_index]
                )
                self._render_action_row(console, item, y, is_selected)

            y += 1

        # Scroll indicators
        if self.scroll_manager.should_show_scroll_up():
            render_char_safe(console, 4, content_start_y - 1, "^ MORE ^", fg=Colors.YELLOW)
        if self.scroll_manager.should_show_scroll_down():
            render_char_safe(
                console, 4, content_start_y + self.max_visible_lines, "v MORE v", fg=Colors.YELLOW
            )

        # Footer with instructions
        main_help, additional_help = self._get_help_text()
        ScreenRenderingUtils.render_screen_footer(
            console,
            main_help,
            additional_line=additional_help,
            color=Colors.LIGHT_GRAY,
        )

    def _render_header_extras(self, console: tcod.console.Console, content_start_y: int) -> int:
        """Hook for subclasses to render extra header content (e.g., tabs). Return new content_start_y."""
        return content_start_y

    def _render_action_row(
        self, console: tcod.console.Console, item: dict, y: int, is_selected: bool
    ):
        """Render a single action row with bindings."""
        action = item["action"]
        name = item["name"]

        # Selection highlighting
        if is_selected:
            bg = Colors.DEEP_PURPLE
            fg = Colors.YELLOW
            prefix = "> "
        else:
            bg = Colors.BLACK
            fg = Colors.WHITE
            prefix = "  "

        # Action name (left-aligned)
        action_text = f"{prefix}{name}"
        render_char_safe(console, 4, y, action_text, fg=fg, bg=bg)

        # Dot leaders
        dot_start = 6 + len(name)
        dot_end = 36
        dots = "." * max(0, dot_end - dot_start)
        render_char_safe(console, dot_start, y, dots, fg=Colors.DARK_GRAY, bg=bg)

        # Bindings (right-aligned)
        bindings = self._get_bindings_for_action(action)
        has_custom = self._has_custom_bindings(action)
        max_bindings = 4 if self._is_gamepad_menu() else 3

        if bindings:
            binding_text = " ".join(f"[{b}]" for b in bindings[:max_bindings])
            if len(bindings) > max_bindings:
                binding_text += f" [+{len(bindings) - max_bindings}]"
            if has_custom:
                binding_text += " *"
        else:
            binding_text = "[unbound]"

        render_char_safe(
            console, 38, y, binding_text, fg=fg if is_selected else Colors.LIGHT_GRAY, bg=bg
        )

    def _is_gamepad_menu(self) -> bool:
        """Return True if this is a gamepad bindings menu."""
        return False  # Override in GamepadBindingsMenu

    def _render_binding_overlay(self, console: tcod.console.Console):
        """Render the binding capture overlay."""
        # Dim background
        for y in range(GameConfig.SCREEN_HEIGHT):
            for x in range(GameConfig.SCREEN_WIDTH):
                console.rgba["bg"][y, x] = (20, 20, 30, 255)

        # Center dialog box (54 chars wide to fit binding text + instructions)
        box_width = min(54, GameConfig.SCREEN_WIDTH - 2)
        box_height = min(14, GameConfig.SCREEN_HEIGHT - 2)
        box_x = max(0, (GameConfig.SCREEN_WIDTH - box_width) // 2)
        box_y = max(0, (GameConfig.SCREEN_HEIGHT - box_height) // 2)

        # Draw box background with bounds checking
        for dy in range(box_height):
            for dx in range(box_width):
                target_y = box_y + dy
                target_x = box_x + dx
                if (
                    0 <= target_y < GameConfig.SCREEN_HEIGHT
                    and 0 <= target_x < GameConfig.SCREEN_WIDTH
                ):
                    console.rgba["bg"][target_y, target_x] = (0, 0, 0, 255)

        # Draw border
        console.draw_frame(box_x, box_y, box_width, box_height, fg=Colors.CYAN)

        # Render input-specific content
        self._render_binding_overlay_content(console, box_x, box_y, box_width)

    def _render_conflict_dialog(self, console: tcod.console.Console):
        """Render the conflict resolution dialog."""
        # Dim background
        for y in range(GameConfig.SCREEN_HEIGHT):
            for x in range(GameConfig.SCREEN_WIDTH):
                console.rgba["bg"][y, x] = (20, 20, 30, 255)

        # Center dialog box (44 chars wide to fit conflict message)
        box_width = min(44, GameConfig.SCREEN_WIDTH - 2)
        box_height = min(14, GameConfig.SCREEN_HEIGHT - 2)
        box_x = max(0, (GameConfig.SCREEN_WIDTH - box_width) // 2)
        box_y = max(0, (GameConfig.SCREEN_HEIGHT - box_height) // 2)

        # Draw box background
        for dy in range(box_height):
            for dx in range(box_width):
                console.rgba["bg"][box_y + dy, box_x + dx] = (0, 0, 0, 255)

        # Draw border
        console.draw_frame(box_x, box_y, box_width, box_height, fg=Colors.GOLDEN)

        # Title
        title = self._get_conflict_title()
        title_x = box_x + (box_width - len(title)) // 2
        render_char_safe(console, title_x, box_y + 2, title, fg=Colors.GOLDEN)

        # Render input-specific conflict info
        self._render_conflict_info(console, box_x, box_y, box_width)

        # List conflicting actions
        y_offset = 5
        for conflict_action in self.conflict_actions[:2]:
            action_name = ACTION_DISPLAY_NAMES.get(conflict_action, conflict_action.name)
            action_x = box_x + (box_width - len(action_name)) // 2
            render_char_safe(console, action_x, box_y + y_offset, action_name, fg=Colors.YELLOW)
            y_offset += 1

        # Question
        question = "Replace existing binding?"
        question_x = box_x + (box_width - len(question)) // 2
        render_char_safe(console, question_x, box_y + 8, question, fg=Colors.WHITE)

        # Options
        options = ["Yes, Replace", "No, Cancel"]
        for i, option in enumerate(options):
            if i == self.conflict_selection:
                color = Colors.GOLDEN
                prefix = "> "
            else:
                color = Colors.WHITE
                prefix = "  "

            option_text = prefix + option
            option_x = box_x + (box_width - len(option_text)) // 2
            render_char_safe(console, option_x, box_y + 10 + i, option_text, fg=color)

    def _get_conflict_title(self) -> str:
        """Return conflict dialog title. Override for different input types."""
        return "KEY CONFLICT"

    def get_context(self):
        """Return input context for this menu."""
        return InputContext.CONTROLS_MENU

    def handle_input(self, event) -> str:
        """Handle input events, routing to appropriate handler."""
        # In binding mode, capture input
        if self.binding_mode:
            return self._handle_binding_input(event)

        # In conflict dialog, handle that
        if self.show_conflict_dialog:
            return self._handle_conflict_input(event)

        # Handle reset key
        if self._handle_reset_key(event):
            return ""

        # Normal menu handling
        return super().handle_input(event)

    def execute_action(self, action) -> str:
        """Execute an InputAction and return menu command."""
        # Navigation
        if action in (InputAction.NAVIGATE_UP, InputAction.MOVE_NORTH):
            self._navigate(-1)
            return ""
        elif action in (InputAction.NAVIGATE_DOWN, InputAction.MOVE_SOUTH):
            self._navigate(1)
            return ""

        # Page navigation
        elif action == InputAction.NAVIGATE_PAGE_UP:
            for _ in range(self.PAGE_SCROLL_SPEED):
                self._navigate(-1)
            return ""
        elif action == InputAction.NAVIGATE_PAGE_DOWN:
            for _ in range(self.PAGE_SCROLL_SPEED):
                self._navigate(1)
            return ""

        # Confirm - enter binding mode
        elif action == InputAction.CONFIRM:
            if self.selectable_indices:
                actual_index = self.selectable_indices[self.selected_index]
                item = self.display_items[actual_index]
                if item["type"] == "action":
                    self.binding_mode = True
                    self.binding_action = item["action"]
                    # Cache controller name on entry (gamepad menu only)
                    if isinstance(self, GamepadBindingsMenu):
                        self._detect_controller()
            return ""

        # Reset to default (X button on gamepad)
        elif action == InputAction.CONTROLS_RESET_DEFAULT:
            if self.binding_mode and self.binding_action:
                self._clear_binding_for_action(self.binding_action)
                self._save_bindings()
                logging.info(f"Reset {self.binding_action.name} to default")
                self.binding_mode = False
                self.binding_action = None
            return ""

        # Reset all bindings (Y button on gamepad)
        elif action == InputAction.CONTROLS_RESET_ALL:
            self._reset_to_defaults()
            return ""

        # Cancel/Back
        elif action == InputAction.CANCEL:
            return "back"

        return ""

    @abstractmethod
    def _clear_binding_for_action(self, action: InputAction) -> None:
        """Clear bindings for a specific action. Subclasses must implement."""
        pass

    def _navigate(self, direction: int):
        """Navigate through selectable items."""
        if not self.selectable_indices:
            return

        new_index = self.selected_index + direction
        new_index = max(0, min(new_index, len(self.selectable_indices) - 1))
        self.selected_index = new_index

    def _close_conflict_dialog(self):
        """Close the conflict dialog and reset state."""
        self.show_conflict_dialog = False
        self.conflict_actions = []
        self.binding_action = None

    def handle_mouse_wheel(self, event) -> str:
        """Handle mouse wheel - scroll through list."""
        if hasattr(event, "y"):
            if event.y > 0:
                for _ in range(self.WHEEL_SCROLL_SPEED):
                    self._navigate(-1)
            elif event.y < 0:
                for _ in range(self.WHEEL_SCROLL_SPEED):
                    self._navigate(1)
        return ""


# =============================================================================
# KEYBOARD BINDINGS MENU
# =============================================================================


class KeyboardBindingsMenu(BaseBindingsMenu):
    """
    Keyboard remapping interface.

    Extends BaseBindingsMenu with keyboard-specific:
    - Key capture for binding
    - Modifier key support (Shift+key combos)
    - Keyboard conflict detection
    """

    def __init__(self, settings: GameSettings, input_mapper: "InputMapper", menu_background=None):
        # Keyboard-specific state (must be set before super().__init__ calls _build_action_list)
        self.pending_key: tcod.event.KeySym | None = None
        self.pending_modifier: int = 0

        super().__init__(settings, input_mapper, menu_background)

    # =========================================================================
    # ABSTRACT METHOD IMPLEMENTATIONS
    # =========================================================================

    def _get_title(self) -> str:
        return "KEYBOARD BINDINGS"

    def _get_subtitle(self) -> str:
        return "Customize your keyboard controls"

    def _get_action_categories(self) -> list:
        return ACTION_CATEGORIES

    def _get_bindings_for_action(self, action: InputAction) -> list[str]:
        return self.input_mapper.get_all_keys_for_action(action)

    def _has_custom_bindings(self, action: InputAction) -> bool:
        return self.input_mapper.has_custom_keyboard_bindings(action)

    def _get_help_text(self) -> tuple[str, str | None]:
        return get_keyboard_bindings_help(self.input_mapper)

    def _reset_to_defaults(self) -> None:
        self.input_mapper.reset_to_defaults("keyboard")
        self._save_bindings()
        logging.info("Reset all keyboard bindings to defaults")

    def _save_bindings(self) -> None:
        keyboard_bindings, _ = self.input_mapper.save_custom_bindings()
        self.settings.custom_keyboard_bindings = keyboard_bindings
        self.settings.save_settings()
        logging.debug("Saved keyboard bindings to settings")

    def _clear_binding_for_action(self, action: InputAction) -> None:
        self.input_mapper.clear_keyboard_bindings(action)

    def _handle_reset_key(self, event) -> bool:
        """Handle R key for reset."""
        event_type = getattr(event, "type", "KEYDOWN")
        if event_type == "KEYDOWN":
            key = event.sym
            if key == tcod.event.KeySym.R:
                self._reset_to_defaults()
                return True
        return False

    def _render_binding_overlay_content(
        self, console: tcod.console.Console, box_x: int, box_y: int, box_width: int
    ) -> None:
        """Render keyboard-specific binding overlay content."""
        # Title
        title = "PRESS KEY TO BIND"
        title_x = box_x + (box_width - len(title)) // 2
        render_char_safe(console, title_x, box_y + 2, title, fg=Colors.CYAN)

        # Action name
        if self.binding_action:
            action_name = ACTION_DISPLAY_NAMES.get(self.binding_action, self.binding_action.name)
            action_x = box_x + (box_width - len(action_name)) // 2
            render_char_safe(console, action_x, box_y + 4, action_name, fg=Colors.YELLOW)

        # Current bindings
        if self.binding_action:
            current_bindings = self.input_mapper.get_default_keys_for_action(self.binding_action)
            if current_bindings:
                current_text = "Current: " + " ".join(f"[{b}]" for b in current_bindings[:3])
            else:
                current_text = "Current: [unbound]"
            current_x = box_x + (box_width - len(current_text)) // 2
            render_char_safe(console, current_x, box_y + 6, current_text, fg=Colors.LIGHT_GRAY)

        # Instructions
        instructions1 = "Press any key to add binding..."
        inst1_x = box_x + (box_width - len(instructions1)) // 2
        render_char_safe(console, inst1_x, box_y + 8, instructions1, fg=Colors.WHITE)

        instructions2 = "ESC to cancel  |  DEL to clear all"
        inst2_x = box_x + (box_width - len(instructions2)) // 2
        render_char_safe(console, inst2_x, box_y + 10, instructions2, fg=Colors.LIGHT_GRAY)

    def _render_conflict_info(
        self, console: tcod.console.Console, box_x: int, box_y: int, box_width: int
    ) -> None:
        """Render keyboard-specific conflict information."""
        if self.pending_key:
            from game_input_mappings import KeyBinding, key_binding_to_display_name

            binding = KeyBinding(self.pending_key, self.pending_modifier)
            key_name = key_binding_to_display_name(binding)
            conflict_text = f"[{key_name}] is already bound to:"
            conflict_x = box_x + (box_width - len(conflict_text)) // 2
            render_char_safe(console, conflict_x, box_y + 4, conflict_text, fg=Colors.WHITE)

    def _handle_binding_input(self, event) -> str:
        """Handle input while in binding mode."""
        event_type = getattr(event, "type", "KEYDOWN")

        if event_type == "KEYDOWN":
            key = event.sym
            modifier = getattr(event, "mod", 0)

            # ESC cancels binding mode
            if key == tcod.event.KeySym.ESCAPE:
                self.binding_mode = False
                self.binding_action = None
                return ""

            # DELETE clears all bindings for this action
            if key == tcod.event.KeySym.DELETE:
                if self.binding_action:
                    self.input_mapper.clear_keyboard_bindings(self.binding_action)
                    self._save_bindings()
                    logging.info(f"Cleared bindings for {self.binding_action.name}")
                self.binding_mode = False
                self.binding_action = None
                return ""

            # Ignore modifier-only keys
            if key in MODIFIER_ONLY_KEYS:
                return ""

            # Check if key is reserved
            if key in RESERVED_KEYS:
                return ""

            # Check for conflicts
            conflicts = self.input_mapper.get_conflicts(self.binding_action, key, modifier)
            if conflicts:
                self.pending_key = key
                self.pending_modifier = modifier
                self.conflict_actions = conflicts
                self.conflict_selection = 0
                self.show_conflict_dialog = True
                self.binding_mode = False
                return ""

            # No conflict - add the binding
            self.input_mapper.add_keyboard_binding(self.binding_action, key, modifier=modifier)
            self._save_bindings()
            from game_input_mappings import KeyBinding, key_binding_to_display_name

            binding = KeyBinding(key, modifier)
            logging.info(
                f"Added binding: {key_binding_to_display_name(binding)} -> {self.binding_action.name}"
            )
            self.binding_mode = False
            self.binding_action = None

        return ""

    def _handle_conflict_input(self, event) -> str:
        """Handle input in conflict dialog."""
        event_type = getattr(event, "type", "KEYDOWN")

        if event_type == "KEYDOWN":
            key = event.sym

            # Navigation
            if key in (
                tcod.event.KeySym.UP,
                tcod.event.KeySym.DOWN,
                tcod.event.KeySym.W,
                tcod.event.KeySym.S,
            ):
                self.conflict_selection = 1 - self.conflict_selection
                return ""

            # Confirm
            if key in (tcod.event.KeySym.RETURN, tcod.event.KeySym.KP_ENTER):
                if self.conflict_selection == 0:  # Yes, replace
                    if self.binding_action and self.pending_key:
                        self.input_mapper.replace_keyboard_binding(
                            self.binding_action, self.pending_key, modifier=self.pending_modifier
                        )
                        self._save_bindings()
                        from game_input_mappings import KeyBinding, key_binding_to_display_name

                        binding = KeyBinding(self.pending_key, self.pending_modifier)
                        logging.info(
                            f"Replaced binding: {key_binding_to_display_name(binding)} -> {self.binding_action.name}"
                        )
                self._close_keyboard_conflict_dialog()
                return ""

            # Cancel
            if key == tcod.event.KeySym.ESCAPE:
                self._close_keyboard_conflict_dialog()
                return ""

        return ""

    def _close_keyboard_conflict_dialog(self):
        """Close the conflict dialog and reset keyboard-specific state."""
        self.show_conflict_dialog = False
        self.pending_key = None
        self.pending_modifier = 0
        self.conflict_actions = []
        self.binding_action = None


# =============================================================================
# GAMEPAD SETTINGS MENU
# =============================================================================


class GamepadSettingsMenu(BaseMenu):
    """
    Gamepad configuration settings.

    Allows adjustment of:
    - Gamepad enabled/disabled
    - Stick deadzone (5-40%)
    - Movement threshold (30-80%)
    - Direction locking on/off
    - Swap sticks (accessibility)
    """

    def __init__(
        self,
        settings: GameSettings,
        input_mapper: "InputMapper | None" = None,
        menu_background=None,
    ):
        super().__init__(menu_background)
        self.settings = settings  # Store settings for modification
        # Ensure input_mapper exists - create default if not provided
        if input_mapper is not None:
            self.input_mapper = input_mapper
        elif not hasattr(self, "input_mapper") or self.input_mapper is None:
            from game_input_mappings import InputMapper

            self.input_mapper = InputMapper()

        self.options = [
            {
                "name": "Gamepad Enabled",
                "type": "toggle",
                "key": "gamepad_enabled",
                "help": "Enable or disable gamepad input entirely.",
            },
            {
                "name": "Stick Deadzone",
                "type": "slider",
                "key": "gamepad_deadzone",
                "min": 0.05,
                "max": 0.40,
                "step": 0.05,
                "help": "Ignores small stick movements (drift correction). Higher = more forgiving.",
            },
            {
                "name": "Movement Threshold",
                "type": "slider",
                "key": "gamepad_threshold",
                "min": 0.10,
                "max": 0.50,
                "step": 0.05,
                "help": "How far to push stick before movement triggers. Lower = more sensitive.",
            },
            {
                "name": "Direction Locking",
                "type": "toggle",
                "key": "gamepad_direction_locking",
                "help": "When ON, moving the stick locks to one direction until released.",
            },
            {
                "name": "Swap Sticks",
                "type": "toggle",
                "key": "gamepad_swap_sticks",
                "help": "Swap left/right stick functions. Right=movement, Left=look mode.",
            },
            {"name": "Back", "type": "action", "help": ""},
        ]

    def render(self, console: tcod.console.Console) -> None:
        """Render the gamepad settings menu."""
        console.clear()

        # Header
        content_start_y = ScreenRenderingUtils.render_screen_header(
            console,
            "GAMEPAD SETTINGS",
            subtitle="Configure gamepad behavior",
            border_color=Colors.CYAN,
            title_color=Colors.CYAN,
        )

        # Options
        y = content_start_y + 2
        for i, option in enumerate(self.options):
            is_selected = i == self.selected_option
            self._render_option(console, option, y, is_selected)
            y += 3

        # Help text for selected option (shown below options)
        selected_option = self.options[self.selected_option]
        help_text = selected_option.get("help", "")
        if help_text:
            help_y = content_start_y + 2 + len(self.options) * 3 + 1
            # Word-wrap help text if too long
            if len(help_text) > GameConfig.SCREEN_WIDTH - 8:
                # Simple word wrap
                words = help_text.split()
                lines = []
                current_line = ""
                for word in words:
                    if len(current_line) + len(word) + 1 <= GameConfig.SCREEN_WIDTH - 8:
                        current_line += (" " if current_line else "") + word
                    else:
                        lines.append(current_line)
                        current_line = word
                if current_line:
                    lines.append(current_line)
                for i, line in enumerate(lines[:2]):  # Max 2 lines
                    render_char_safe(console, 4, help_y + i, line, fg=Colors.LIGHT_GRAY)
            else:
                render_char_safe(console, 4, help_y, help_text, fg=Colors.LIGHT_GRAY)

        # Footer with instructions - dynamically reflects current bindings
        ScreenRenderingUtils.render_screen_footer(
            console,
            get_gamepad_settings_help(self.input_mapper),
            color=Colors.LIGHT_GRAY,
        )

    def _render_option(
        self, console: tcod.console.Console, option: dict, y: int, is_selected: bool
    ):
        """Render a single option row."""
        name = option["name"]
        option_type = option["type"]

        # Selection highlighting
        if is_selected:
            fg = Colors.YELLOW
            bg = Colors.DEEP_PURPLE
            prefix = "> "
        else:
            fg = Colors.WHITE
            bg = Colors.BLACK
            prefix = "  "

        # Option name
        name_text = f"{prefix}{name}"
        render_char_safe(console, 4, y, name_text, fg=fg, bg=bg)

        # Value rendering based on type
        if option_type == "toggle":
            value = getattr(self.settings, option["key"], True)
            value_text = "[ON ]" if value else "[OFF]"
            value_x = GameConfig.SCREEN_WIDTH - 10
            render_char_safe(console, value_x, y, value_text, fg=fg, bg=bg)

        elif option_type == "slider":
            value = getattr(self.settings, option["key"], option.get("min", 0))
            percent = int(value * 100)

            # Slider bar with bounds clamping
            bar_width = 10
            range_size = option["max"] - option["min"]
            if range_size > 0:
                filled = int(bar_width * (value - option["min"]) / range_size)
            else:
                filled = 0
            filled = max(0, min(bar_width, filled))  # Clamp to valid range
            bar = "[" + "=" * filled + "-" * (bar_width - filled) + "]"

            slider_text = f"< {bar} > {percent}%"
            slider_x = GameConfig.SCREEN_WIDTH - len(slider_text) - 4
            render_char_safe(console, slider_x, y, slider_text, fg=fg, bg=bg)

        elif option_type == "action":
            # No value to render
            pass

    def get_context(self):
        """Return input context for this menu."""
        return InputContext.CONTROLS_MENU

    def execute_action(self, action) -> str:
        """Execute an InputAction and return menu command."""
        # Navigation
        if action in (InputAction.NAVIGATE_UP, InputAction.MOVE_NORTH):
            self.selected_option = (self.selected_option - 1) % len(self.options)
            return ""
        elif action in (InputAction.NAVIGATE_DOWN, InputAction.MOVE_SOUTH):
            self.selected_option = (self.selected_option + 1) % len(self.options)
            return ""

        # Adjust value
        elif action in (InputAction.NAVIGATE_LEFT, InputAction.MOVE_WEST):
            self._adjust_option(-1)
            return ""
        elif action in (InputAction.NAVIGATE_RIGHT, InputAction.MOVE_EAST):
            self._adjust_option(1)
            return ""

        # Confirm - toggle for bool, select for action
        elif action == InputAction.CONFIRM:
            if not self.options or not (0 <= self.selected_option < len(self.options)):
                return ""
            option = self.options[self.selected_option]
            if option["type"] == "action":
                if option["name"] == "Back":
                    return "back"
            elif option["type"] == "toggle":
                self._adjust_option(1)  # Toggle
            return ""

        # Cancel/Back
        elif action == InputAction.CANCEL:
            return "back"

        return ""

    def _adjust_option(self, direction: int):
        """Adjust the currently selected option value."""
        if not self.options or not (0 <= self.selected_option < len(self.options)):
            return
        option = self.options[self.selected_option]
        option_type = option["type"]

        if option_type == "toggle":
            key = option["key"]
            current = getattr(self.settings, key, True)
            setattr(self.settings, key, not current)
            self.settings.save_settings()
            logging.info(f"Gamepad setting '{key}' toggled to {not current}")

        elif option_type == "slider":
            key = option["key"]
            current = getattr(self.settings, key, option.get("min", 0))
            step = option.get("step", 0.05)
            min_val = option.get("min", 0)
            max_val = option.get("max", 1)

            new_val = current + (direction * step)
            new_val = max(min_val, min(max_val, new_val))
            new_val = round(new_val, 2)  # Avoid floating point weirdness

            setattr(self.settings, key, new_val)
            self.settings.save_settings()
            logging.info(f"Gamepad setting '{key}' adjusted to {new_val}")


# =============================================================================
# GAMEPAD BINDINGS MENU (PHASE 5)
# =============================================================================


class GamepadBindingsMenu(BaseBindingsMenu):
    """
    Gamepad button remapping interface with context tabs.

    Extends BaseBindingsMenu with gamepad-specific:
    - Context tabs (Gameplay vs Menus) with LB/RB switching
    - Button capture for binding
    - Controller detection display
    """

    # Additional scroll speed configuration for gamepad (smaller pages)
    PAGE_SCROLL_SPEED = 8

    # Context tab configuration
    # Note: "Menus" uses INVENTORY as a representative context for all menu bindings.
    # Menu bindings (confirm, cancel, navigate) are shared across all menu contexts
    # (inventory, help, settings, etc.) so INVENTORY is used as the canonical context.
    CONTEXT_TABS = [
        ("Gameplay", InputContext.GAMEPLAY, GAMEPAD_GAMEPLAY_CATEGORIES),
        ("Menus", InputContext.INVENTORY, GAMEPAD_MENU_CATEGORIES),
    ]

    def __init__(self, settings: GameSettings, input_mapper: "InputMapper", menu_background=None):
        # Gamepad-specific state (must be set before super().__init__)
        self.current_tab = 0
        self.pending_button: int | None = None
        self.detected_controller_name: str | None = None

        super().__init__(settings, input_mapper, menu_background)

        # Adjust max_visible_lines for tab header
        self.max_visible_lines = GameConfig.SCREEN_HEIGHT - 12
        self.scroll_manager.visible_height = self.max_visible_lines

    # =========================================================================
    # ABSTRACT METHOD IMPLEMENTATIONS
    # =========================================================================

    def _get_title(self) -> str:
        return "GAMEPAD BINDINGS"

    def _get_subtitle(self) -> str:
        return "LB/RB: Switch Tab"

    def _get_action_categories(self) -> list:
        return self.CONTEXT_TABS[self.current_tab][2]

    def _get_bindings_for_action(self, action: InputAction) -> list[str]:
        bindings = []
        context = self._get_current_context()

        # Get button bindings (default + custom)
        buttons = self.input_mapper.get_all_buttons_for_action(action, context)
        for button in buttons:
            bindings.append(button_to_display_name(button))

        # Get axis bindings (triggers) - only defaults for now
        axes = self.input_mapper.get_default_axes_for_action(action, context)
        for axis in axes:
            bindings.append(axis_to_display_name(axis))

        return bindings

    def _has_custom_bindings(self, action: InputAction) -> bool:
        return self.input_mapper.has_custom_gamepad_bindings(action, self._get_current_context())

    def _get_help_text(self) -> tuple[str, str | None]:
        return get_gamepad_bindings_help(self.input_mapper)

    def _is_gamepad_menu(self) -> bool:
        return True

    def _get_conflict_title(self) -> str:
        return "BUTTON CONFLICT"

    def _reset_to_defaults(self) -> None:
        self.input_mapper.reset_to_defaults("gamepad")
        self._save_bindings()
        logging.info("Reset all gamepad bindings to defaults")

    def _save_bindings(self) -> None:
        _, gamepad_bindings = self.input_mapper.save_custom_bindings()
        self.settings.custom_gamepad_bindings = gamepad_bindings
        self.settings.save_settings()
        logging.debug("Saved gamepad bindings to settings")

    def _clear_binding_for_action(self, action: InputAction) -> None:
        self.input_mapper.clear_gamepad_bindings(action, self._get_current_context())

    def _handle_reset_key(self, event) -> bool:
        """Handle reset keys and tab switching."""
        event_type = getattr(event, "type", None)

        if event_type == "KEYDOWN":
            key = event.sym
            if key == tcod.event.KeySym.R:
                self._reset_to_defaults()
                return True
            elif key == tcod.event.KeySym.LEFTBRACKET:
                self._switch_tab(-1)
                return True
            elif key == tcod.event.KeySym.RIGHTBRACKET:
                self._switch_tab(1)
                return True

        elif event_type == "CONTROLLERBUTTONDOWN":
            CB = tcod.sdl.joystick.ControllerButton
            if event.button == CB.Y:
                self._reset_to_defaults()
                return True
            elif event.button == CB.LEFTSHOULDER:
                self._switch_tab(-1)
                return True
            elif event.button == CB.RIGHTSHOULDER:
                self._switch_tab(1)
                return True

        return False

    def _render_binding_overlay_content(
        self, console: tcod.console.Console, box_x: int, box_y: int, box_width: int
    ) -> None:
        """Render gamepad-specific binding overlay content."""
        # Title
        title = "PRESS BUTTON TO BIND"
        title_x = box_x + (box_width - len(title)) // 2
        render_char_safe(console, title_x, box_y + 2, title, fg=Colors.CYAN)

        # Action name
        if self.binding_action:
            action_name = ACTION_DISPLAY_NAMES.get(self.binding_action, self.binding_action.name)
            action_x = box_x + (box_width - len(action_name)) // 2
            render_char_safe(console, action_x, box_y + 4, action_name, fg=Colors.YELLOW)

        # Current bindings
        if self.binding_action:
            current_bindings = self._get_bindings_for_action(self.binding_action)
            if current_bindings:
                current_text = "Current: " + " ".join(f"[{b}]" for b in current_bindings[:3])
            else:
                current_text = "Current: [unbound]"
            current_x = box_x + (box_width - len(current_text)) // 2
            render_char_safe(console, current_x, box_y + 6, current_text, fg=Colors.LIGHT_GRAY)

        # Controller status (cached on binding mode entry)
        if self.detected_controller_name:
            ctrl_text = f"Controller: {self.detected_controller_name}"
        else:
            ctrl_text = "No controller detected - connect gamepad"
        ctrl_x = box_x + (box_width - len(ctrl_text)) // 2
        render_char_safe(
            console,
            ctrl_x,
            box_y + 8,
            ctrl_text,
            fg=Colors.GREEN if self.detected_controller_name else Colors.RED,
        )

        # Instructions
        instructions1 = "Press any button to bind..."
        inst1_x = box_x + (box_width - len(instructions1)) // 2
        render_char_safe(console, inst1_x, box_y + 10, instructions1, fg=Colors.WHITE)

        instructions2 = get_gamepad_binding_instructions()
        inst2_x = box_x + (box_width - len(instructions2)) // 2
        render_char_safe(console, inst2_x, box_y + 12, instructions2, fg=Colors.LIGHT_GRAY)

    def _render_conflict_info(
        self, console: tcod.console.Console, box_x: int, box_y: int, box_width: int
    ) -> None:
        """Render gamepad-specific conflict information."""
        if self.pending_button is not None:
            button_name = button_to_display_name(self.pending_button)
            conflict_text = f"[{button_name}] is already bound to:"
            conflict_x = box_x + (box_width - len(conflict_text)) // 2
            render_char_safe(console, conflict_x, box_y + 4, conflict_text, fg=Colors.WHITE)

    def _handle_binding_input(self, event) -> str:
        """Handle input while in binding mode."""
        event_type = getattr(event, "type", None)

        # Handle keyboard input (ESC to cancel, DEL to clear)
        if event_type == "KEYDOWN":
            key = event.sym
            if key == tcod.event.KeySym.ESCAPE:
                self.binding_mode = False
                self.binding_action = None
                return ""
            elif key == tcod.event.KeySym.DELETE:
                if self.binding_action:
                    self.input_mapper.clear_gamepad_bindings(
                        self.binding_action, self._get_current_context()
                    )
                    self._save_bindings()
                    logging.info(f"Cleared gamepad bindings for {self.binding_action.name}")
                self.binding_mode = False
                self.binding_action = None
                return ""

        # Handle gamepad button press
        if event_type == "CONTROLLERBUTTONDOWN":
            button = event.button
            CB = tcod.sdl.joystick.ControllerButton

            # B button cancels binding mode
            if button == CB.B:
                self.binding_mode = False
                self.binding_action = None
                return ""

            # X button clears binding
            if button == CB.X:
                if self.binding_action:
                    self.input_mapper.clear_gamepad_bindings(
                        self.binding_action, self._get_current_context()
                    )
                    self._save_bindings()
                    logging.info(f"Cleared gamepad bindings for {self.binding_action.name}")
                self.binding_mode = False
                self.binding_action = None
                return ""

            # Check if button is reserved
            if button in RESERVED_BUTTONS:
                return ""

            # Check for conflicts in current context
            conflicts = self.input_mapper.get_gamepad_conflicts(
                self.binding_action, button, self._get_current_context()
            )
            if conflicts:
                self.pending_button = button
                self.conflict_actions = conflicts
                self.conflict_selection = 0
                self.show_conflict_dialog = True
                self.binding_mode = False
                return ""

            # No conflict - add the binding
            self.input_mapper.add_gamepad_binding(
                self.binding_action, button, self._get_current_context()
            )
            self._save_bindings()
            logging.info(
                f"Added binding: {button_to_display_name(button)} -> {self.binding_action.name}"
            )
            self.binding_mode = False
            self.binding_action = None

        return ""

    def _handle_conflict_input(self, event) -> str:
        """Handle input in conflict dialog."""
        event_type = getattr(event, "type", None)

        # Keyboard navigation
        if event_type == "KEYDOWN":
            key = event.sym

            if key in (
                tcod.event.KeySym.UP,
                tcod.event.KeySym.DOWN,
                tcod.event.KeySym.W,
                tcod.event.KeySym.S,
            ):
                self.conflict_selection = 1 - self.conflict_selection
                return ""

            if key in (tcod.event.KeySym.RETURN, tcod.event.KeySym.KP_ENTER):
                if self.conflict_selection == 0:  # Yes, replace
                    self._apply_conflict_replacement()
                self._close_gamepad_conflict_dialog()
                return ""

            if key == tcod.event.KeySym.ESCAPE:
                self._close_gamepad_conflict_dialog()
                return ""

        # Gamepad navigation
        if event_type == "CONTROLLERBUTTONDOWN":
            button = event.button
            CB = tcod.sdl.joystick.ControllerButton

            if button in (CB.DPAD_UP, CB.DPAD_DOWN):
                self.conflict_selection = 1 - self.conflict_selection
                return ""

            if button == CB.A:
                if self.conflict_selection == 0:  # Yes, replace
                    self._apply_conflict_replacement()
                self._close_gamepad_conflict_dialog()
                return ""

            if button == CB.B:
                self._close_gamepad_conflict_dialog()
                return ""

        return ""

    # =========================================================================
    # GAMEPAD-SPECIFIC METHODS
    # =========================================================================

    def _get_current_context(self) -> InputContext:
        """Get the InputContext for the current tab."""
        # Bounds check to prevent IndexError if current_tab is corrupted
        if not (0 <= self.current_tab < len(self.CONTEXT_TABS)):
            logging.warning(f"Invalid tab index {self.current_tab}, resetting to 0")
            self.current_tab = 0
        return self.CONTEXT_TABS[self.current_tab][1]

    def _switch_tab(self, direction: int):
        """Switch between context tabs."""
        new_tab = (self.current_tab + direction) % len(self.CONTEXT_TABS)
        if new_tab != self.current_tab:
            self.current_tab = new_tab
            self._build_action_list()
            self.scroll_manager.set_total_items(len(self.display_items))
            self.scroll_manager.reset()

    def _render_header_extras(self, console: tcod.console.Console, content_start_y: int) -> int:
        """Render tab selector and adjust content start."""
        self._render_tab_selector(console, content_start_y)
        return content_start_y + 2

    def _render_tab_selector(self, console: tcod.console.Console, y: int):
        """Render the context tab selector."""
        x = 4
        for i, (tab_name, _, _) in enumerate(self.CONTEXT_TABS):
            if i == self.current_tab:
                # Selected tab
                tab_text = f"[ {tab_name} ]"
                fg = Colors.CYAN
                bg = Colors.DEEP_PURPLE
            else:
                # Unselected tab
                tab_text = f"  {tab_name}  "
                fg = Colors.LIGHT_GRAY
                bg = Colors.BLACK

            render_char_safe(console, x, y, tab_text, fg=fg, bg=bg)
            x += len(tab_text) + 2

    def _detect_controller(self):
        """Detect connected controller and update name."""
        try:
            controllers = tcod.sdl.joystick.get_controllers()
            if controllers:
                self.detected_controller_name = controllers[0].name[:30]  # Truncate long names
            else:
                self.detected_controller_name = None
        except Exception:
            self.detected_controller_name = None

    def _apply_conflict_replacement(self):
        """Apply the pending binding replacement in current context."""
        if self.binding_action and self.pending_button is not None:
            self.input_mapper.replace_gamepad_binding(
                self.binding_action, self.pending_button, self._get_current_context()
            )
            self._save_bindings()
            logging.info(
                f"Replaced binding: {button_to_display_name(self.pending_button)} -> {self.binding_action.name}"
            )

    def _close_gamepad_conflict_dialog(self):
        """Close the conflict dialog and reset gamepad-specific state."""
        self.show_conflict_dialog = False
        self.pending_button = None
        self.conflict_actions = []
        self.binding_action = None
