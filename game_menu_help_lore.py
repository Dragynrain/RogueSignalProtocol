#!/usr/bin/env python3
"""
Rogue Signal Protocol - Help and Lore Menus

Help menu system with text-based display and factory for mode selection.
LoreMenu displays discovered story fragments from main menu.
Factory function (create_help_menu) selects HelpMenu or GraphicalHelpMenu based on graphics mode.
"""

import logging
import textwrap

import tcod

from game_config import GameConfig
from game_entities import Colors
from game_help_content import HelpContent
from game_screen_utilities import ScreenRenderingUtils
from game_story import StoryFragmentManager
from game_ui import UniversalInputHandler, render_char_safe


def create_help_menu(settings, context=None, tile_manager=None):
    """
    Factory function to create appropriate help menu based on graphics mode.

    Args:
        settings: GameSettings instance
        context: TCOD context (required for graphics mode)
        tile_manager: TileManager instance (required for graphics mode)

    Returns:
        HelpMenu or GraphicalHelpMenu instance

    Raises:
        RuntimeError: If graphics mode is selected but required components are missing
        ImportError: If GraphicalHelpMenu module cannot be imported
    """
    if settings.graphics_mode == "graphics":
        # Fail fast with clear error messages if required components are missing
        if tile_manager is None:
            raise RuntimeError(
                "Graphics mode help menu requires TileManager, but tile_manager is None.\n"
                "This indicates the TileManager was not initialized properly.\n"
                "Possible causes:\n"
                "  - TileManager initialization failed during startup\n"
                "  - Graphics mode was switched but TileManager was not created\n"
                "Check logs for TileManager initialization errors."
            )
        if context is None:
            raise RuntimeError(
                "Graphics mode help menu requires TCOD context, but context is None.\n"
                "This indicates the context was not passed to the help menu factory.\n"
                "This is a programming error - context should always be provided."
            )

        # Import GraphicalHelpMenu - let ImportError propagate if file is missing
        from game_menu_help_graphics import GraphicalHelpMenu

        # Create menu - let any exceptions propagate (they indicate real bugs)
        logging.info("Creating GraphicalHelpMenu")
        return GraphicalHelpMenu(context, settings, tile_manager)
    else:
        # Glyph mode - use standard text-based help
        logging.info("Creating standard HelpMenu (glyph mode)")
        return HelpMenu()


class LoreMenu:
    """Data Fragments viewer menu for main menu."""

    def __init__(self):
        self.story_fragment_manager = None
        self.lore_viewer_selection = 0
        self.lore_viewer_mode = "list"  # "list" or "reading"

    def _load_story_fragments(self):
        """Load story fragment manager from save data."""
        if self.story_fragment_manager is None:
            self.story_fragment_manager = StoryFragmentManager()

    def render(self, console: tcod.console.Console) -> None:
        """Render the lore viewer screen."""
        console.clear()

        self._load_story_fragments()
        discovered_fragments = self.story_fragment_manager.get_discovered_fragments()
        discovered_count, total_count = self.story_fragment_manager.get_fragment_count()

        if self.lore_viewer_mode == "reading" and discovered_fragments:
            self._render_reading_mode(console, discovered_fragments)
        else:
            self._render_list_mode(console, discovered_fragments, discovered_count, total_count)

    def _render_list_mode(self, console, discovered_fragments, discovered_count, total_count):
        """Render data fragment list."""
        title = f"DISCOVERED DATA FRAGMENTS ({discovered_count}/{total_count})"
        ScreenRenderingUtils.render_centered_title(console, title, 2, Colors.YELLOW)

        if not discovered_fragments:
            render_char_safe(console, 2, 5, "No data fragments discovered yet.", fg=Colors.WHITE)
            render_char_safe(console, 2, 6, "Start playing to discover the story!", fg=Colors.WHITE)
            render_char_safe(
                console, 2, GameConfig.SCREEN_HEIGHT - 2, "ESC/Right-Click: Back", fg=Colors.CYAN
            )
            return

        start_y = 5
        for i, (fragment_index, fragment_text) in enumerate(discovered_fragments):
            # Clamp selection
            if self.lore_viewer_selection >= len(discovered_fragments):
                self.lore_viewer_selection = len(discovered_fragments) - 1

            is_selected = i == self.lore_viewer_selection
            color = Colors.CYAN if is_selected else Colors.WHITE
            prefix = "▶ " if is_selected else "  "

            # Show first line of fragment as title
            first_line = fragment_text.split("\n")[0][:60]
            render_char_safe(
                console,
                2,
                start_y + i,
                f"{prefix}Fragment {fragment_index + 1}: {first_line}",
                fg=color,
            )

        # Instructions
        render_char_safe(
            console,
            2,
            GameConfig.SCREEN_HEIGHT - 4,
            "↕/Wheel: Navigate │ Enter/Click: Read │ ESC/Right-Click: Back",
            fg=Colors.LIGHT_GRAY,
        )

    def _render_reading_mode(self, console, discovered_fragments):
        """Render individual fragment for reading."""
        if self.lore_viewer_selection >= len(discovered_fragments):
            self.lore_viewer_mode = "list"
            return

        fragment_index, fragment_text = discovered_fragments[self.lore_viewer_selection]

        title = f"DATA FRAGMENT {fragment_index + 1}"
        ScreenRenderingUtils.render_centered_title(console, title, 2, Colors.YELLOW)

        # Render fragment text with word wrapping utility
        ScreenRenderingUtils.render_word_wrapped_text(
            console,
            fragment_text,
            2,
            5,
            max_width=GameConfig.SCREEN_WIDTH - 4,
            max_height=GameConfig.SCREEN_HEIGHT - 4,
        )

        render_char_safe(
            console,
            2,
            GameConfig.SCREEN_HEIGHT - 2,
            "ESC/Right-Click: Back to list │ Click/Any key: Close",
            fg=Colors.CYAN,
        )

    def handle_input(self, event) -> str:
        """Handle lore menu input with proper navigation."""
        self._load_story_fragments()
        discovered_fragments = self.story_fragment_manager.get_discovered_fragments()

        if not discovered_fragments:
            # No fragments - ESC returns to main menu
            if UniversalInputHandler.is_escape_key(event):
                return "back"
            return ""

        if self.lore_viewer_mode == "list":
            # Handle navigation using universal handler
            if UniversalInputHandler.handle_list_navigation(
                self, event, len(discovered_fragments), False, self._navigate_lore_selection
            ):
                return ""

            # Handle selection
            if UniversalInputHandler.is_confirm_key(event):
                self.lore_viewer_mode = "reading"
                return ""
            elif UniversalInputHandler.is_escape_key(event):
                return "back"

        elif self.lore_viewer_mode == "reading":
            # ESC returns to list, any other key closes completely
            if UniversalInputHandler.is_escape_key(event):
                self.lore_viewer_mode = "list"
                return ""
            elif UniversalInputHandler.handle_any_key_screen(event):
                return "back"

        return ""

    def handle_mouse_motion(self, event) -> bool:
        """Handle mouse motion - update selection based on hover."""
        if self.lore_viewer_mode != "list":
            return False

        self._load_story_fragments()
        discovered_fragments = self.story_fragment_manager.get_discovered_fragments()

        if not discovered_fragments or not hasattr(event, "position") or not event.position:
            return False

        # Fragment list starts at Y=5, 1 line per item (rendered with start_y + i)
        start_y = 5
        spacing = 1
        tile_y = int(event.position.y)

        if tile_y >= start_y:
            index = (tile_y - start_y) // spacing
            if 0 <= index < len(discovered_fragments):
                self.lore_viewer_selection = index
                return True

        return False

    def handle_mouse_click(self, event) -> str:
        """Handle mouse click - select fragment, navigate, or go back."""
        import tcod.event

        # Right-click = go back (standard behavior)
        if hasattr(event, "button") and event.button == tcod.event.MouseButton.RIGHT:
            if self.lore_viewer_mode == "reading":
                # In reading mode, go back to list
                self.lore_viewer_mode = "list"
                return ""
            else:
                # In list mode, go back to main menu
                return "back"

        if not hasattr(event, "position") or not event.position:
            return ""

        if self.lore_viewer_mode == "reading":
            # Left-click anywhere in reading mode returns to list
            self.lore_viewer_mode = "list"
            return ""
        else:
            # In list mode, update selection and open (left-click only)
            if self.handle_mouse_motion(event):
                # Mouse was over a valid item, open it
                self.lore_viewer_mode = "reading"
            return ""

    def handle_mouse_wheel(self, event) -> bool:
        """Handle mouse wheel - scroll through fragments."""
        if self.lore_viewer_mode != "list":
            return False

        self._load_story_fragments()
        discovered_fragments = self.story_fragment_manager.get_discovered_fragments()

        if not discovered_fragments:
            return False

        if hasattr(event, "y"):
            if event.y > 0:
                # Scroll up
                self._navigate_lore_selection(-1)
            elif event.y < 0:
                # Scroll down
                self._navigate_lore_selection(1)
            return True

        return False

    def _navigate_lore_selection(self, direction: int):
        """Navigate lore selection."""
        discovered_fragments = self.story_fragment_manager.get_discovered_fragments()
        if discovered_fragments:
            if direction == -1:
                self.lore_viewer_selection = max(0, self.lore_viewer_selection - 1)
            else:
                self.lore_viewer_selection = min(
                    len(discovered_fragments) - 1, self.lore_viewer_selection + 1
                )


class HelpMenu:
    """Refactored help menu using centralized content and layout helpers."""

    def __init__(self):
        self.current_page = 0
        self.total_pages = 3

    def render(self, console: tcod.console.Console) -> None:
        """Render the help screen with absolute positioning."""
        console.clear()

        # Title with page indicator
        title = f"ROGUE SIGNAL PROTOCOL - HELP (Page {self.current_page + 1}/{self.total_pages})"
        ScreenRenderingUtils.render_centered_title(console, title, 1, Colors.YELLOW)

        # Get and render page content using absolute positioning
        page_content = self._build_page_content()

        # Pages can return either format:
        # - (x, text, color) for sequential (pages 1 & 2)
        # - (x, y, text, color) for absolute (page 3)
        # Detect format by checking first element length
        if page_content and len(page_content[0]) == 4:
            # Absolute positioning format (x, y, text, color)
            for x, y, text, color in page_content:
                if y < GameConfig.SCREEN_HEIGHT - 4:
                    render_char_safe(console, x, y, text, fg=color)
        else:
            # Sequential format (x, text, color) - legacy for pages 1 & 2
            y = 3
            for x, text, color in page_content:
                if y < GameConfig.SCREEN_HEIGHT - 4:
                    render_char_safe(console, x, y, text, fg=color)
                    y += 1

        # Page navigation and back instruction
        nav_text = "← →/Mouse Wheel: Change page │ ESC/Right-Click: Back"
        render_char_safe(console, 2, GameConfig.SCREEN_HEIGHT - 2, nav_text, fg=Colors.CYAN)

    def _build_page_content(self):
        """Build page content using HelpContent and calculated positions."""
        if self.current_page == 0:
            return self._build_page_1()
        elif self.current_page == 1:
            return self._build_page_2()
        else:
            return self._build_page_3()

    def _build_page_1(self):
        """Page 1: Map Symbols, Objectives, Mechanics, Controls."""
        lines = []
        utils = ScreenRenderingUtils

        # Blank lines at top
        lines.append((0, "", Colors.WHITE))
        lines.append((0, "", Colors.WHITE))

        # MAP SYMBOLS section (moved to top)
        heading = "MAP SYMBOLS:"
        lines.append((utils.center_x(heading), heading, Colors.CYAN))
        lines.append((0, "", Colors.WHITE))

        # Map symbols - left-aligned block, centered as a group
        symbol_text = [
            f"{glyph}  {name} {desc}" for glyph, name, desc, _ in HelpContent.get_map_symbols()
        ]
        block_x = utils.center_block_x(symbol_text)
        for i, (glyph, name, desc, color) in enumerate(HelpContent.get_map_symbols()):
            lines.append((block_x, symbol_text[i], color))

        lines.append((0, "", Colors.WHITE))
        lines.append((0, "", Colors.WHITE))

        # OBJECTIVE & MECHANICS section
        heading = "OBJECTIVE & MECHANICS:"
        lines.append((utils.center_x(heading), heading, Colors.CYAN))
        lines.append((0, "", Colors.WHITE))

        # Objectives - each line centered individually
        for text, color in HelpContent.get_objectives():
            lines.append((utils.center_x(text), text, color))

        lines.append((0, "", Colors.WHITE))

        # Core mechanics - left-aligned block, centered as a group
        mechanics_text = [f"{stat}: {desc}" for stat, desc, _ in HelpContent.get_core_mechanics()]
        block_x = utils.center_block_x(mechanics_text)
        for i, (stat, desc, color) in enumerate(HelpContent.get_core_mechanics()):
            text = mechanics_text[i]
            lines.append((block_x, text, color))

        lines.append((0, "", Colors.WHITE))

        # CONTROLS section
        heading = "CONTROLS:"
        lines.append((utils.center_x(heading), heading, Colors.CYAN))
        lines.append((0, "", Colors.WHITE))

        controls = HelpContent.get_controls()

        # Movement and exploits - left-aligned block, centered as a group
        movement_text = [f"{label}: {desc}" for label, desc in controls["movement"]]
        block_x = utils.center_block_x(movement_text)
        for label, desc in controls["movement"]:
            text = f"{label}: {desc}"
            lines.append((block_x, text, Colors.WHITE))

        lines.append((0, "", Colors.WHITE))

        # Screen shortcuts - left-aligned block, centered as a group
        screens = controls["screens"]
        screen_text = [f"{label}: {desc}" for label, desc in screens]
        block_x = utils.center_block_x(screen_text)
        for label, desc in screens:
            text = f"{label}: {desc}"
            lines.append((block_x, text, Colors.WHITE))

        lines.append((0, "", Colors.WHITE))

        # Inventory controls - left-aligned block, centered as a group
        inventory_text = [f"{label}: {desc}" for label, desc in controls["inventory"]]
        block_x = utils.center_block_x(inventory_text)
        for label, desc in controls["inventory"]:
            text = f"{label}: {desc}"
            lines.append((block_x, text, Colors.WHITE))

        lines.append((0, "", Colors.WHITE))

        # Mouse controls - left-aligned block, centered as a group
        mouse_text = []
        for label, desc in controls["mouse"]:
            if "Click" in label:
                mouse_text.append(f"Mouse: {label} to {desc.lower()}")
            elif "Wheel" in label:
                mouse_text.append(f"Wheel to {desc.lower()}")
            else:
                mouse_text.append(f"Right-click to {desc.lower()}")

        block_x = utils.center_block_x(mouse_text)
        for i, (label, desc) in enumerate(controls["mouse"]):
            lines.append(
                (
                    block_x,
                    mouse_text[i],
                    Colors.WHITE if "Right" not in label else Colors.LIGHT_GRAY,
                )
            )

        # Debug
        for label, desc in controls["debug"]:
            text = f"{label}: {desc}"
            lines.append((utils.center_x(text), text, Colors.LIGHT_GRAY))

        return lines

    def _build_page_2(self):
        """Page 2: Power-ups & Enemies."""
        lines = []
        utils = ScreenRenderingUtils

        # Add some top spacing
        for _ in range(3):
            lines.append((0, "", Colors.WHITE))

        # POWER-UPS section
        heading = "POWER-UPS:"
        lines.append((utils.center_x(heading), heading, Colors.CYAN))
        lines.append((0, "", Colors.WHITE))

        # Power-ups - left-aligned block, centered as a group
        powerup_text = [
            f"{glyph}  {name} - {desc}" for glyph, name, desc, _ in HelpContent.get_power_ups()
        ]
        block_x = utils.center_block_x(powerup_text)
        for i, (glyph, name, desc, color) in enumerate(HelpContent.get_power_ups()):
            lines.append((block_x, powerup_text[i], color))

        # Add spacing
        for _ in range(2):
            lines.append((0, "", Colors.WHITE))

        # Nodes - left-aligned block, centered as a group
        node_text = [
            f"{glyph}  {name} - {desc}" for glyph, name, desc, _ in HelpContent.get_nodes()
        ]
        block_x = utils.center_block_x(node_text)
        for i, (glyph, name, desc, color) in enumerate(HelpContent.get_nodes()):
            lines.append((block_x, node_text[i], color))

        # Add spacing
        for _ in range(2):
            lines.append((0, "", Colors.WHITE))

        # Upgrades - left-aligned block, centered as a group
        upgrade_text = [
            f"{glyph}  {name} - {desc}" for glyph, name, desc, _ in HelpContent.get_upgrades()
        ]
        block_x = utils.center_block_x(upgrade_text)
        for i, (glyph, name, desc, color) in enumerate(HelpContent.get_upgrades()):
            lines.append((block_x, upgrade_text[i], color))

        # Add spacing
        for _ in range(5):
            lines.append((0, "", Colors.WHITE))

        # ENEMIES section
        heading = "ENEMIES (HP / Vision / Damage):"
        lines.append((utils.center_x(heading), heading, Colors.CYAN))
        lines.append((0, "", Colors.WHITE))

        # Load enemy data and render with proper column alignment
        enemies = HelpContent.get_enemy_data()
        enemy_order = [
            "Scanner",
            "Firewall",
            "Patrol",
            "Bot",
            "Hunter",
            "Virus",
            "Inhibitor",
            "Admin Avatar",
        ]

        # Build all enemy lines first to calculate block width
        enemy_lines = []
        for enemy_name in enemy_order:
            if enemy_name in enemies:
                data = enemies[enemy_name]
                glyph = data["glyph"]
                cpu = data["cpu"]
                vision = data["vision"]
                damage = data["damage"]
                desc = data["description"]

                # Fixed-width columns: Name(13) + Stats(16) + Desc
                text = f"{glyph} {enemy_name:<13} {cpu:3d} / {vision} / {damage:2d}  - {desc}"
                enemy_lines.append((text, data["behavior"]))

        # Calculate block position
        block_x = utils.center_block_x([line[0] for line in enemy_lines])

        # Render with proper alignment
        for i, (text, behavior) in enumerate(enemy_lines):
            color = HelpContent.ENEMY_COLORS[behavior]
            lines.append((block_x, text, color))

            # Add spacing after firewall and bot (between groups)
            if enemy_order[i] in ["Firewall", "Bot"]:
                lines.append((0, "", Colors.WHITE))

        return lines

    def _build_page_3(self):
        """Page 3: Exploits & Status Effects (2-column layout - IDENTICAL to graphics mode)."""
        # Two-column positions (narrower left column with 2-line exploits, wider gap)
        left_x = 5
        right_x = 42  # More gap between columns

        exploits = HelpContent.get_exploits()
        effects = HelpContent.get_status_effects()

        # Use absolute positioning (x, y, text, color) - same as graphics mode
        text_lines = []

        # LEFT COLUMN - COMBAT EXPLOITS (2 lines per exploit)
        y_left = 4
        text_lines.append((left_x, y_left, "COMBAT EXPLOITS:", Colors.CYAN))
        y_left += 2

        for name, desc, color in exploits["combat"]:
            text_lines.append((left_x + 1, y_left, name, color))  # Name in color
            y_left += 1
            text_lines.append((left_x + 1, y_left, desc, Colors.WHITE))  # Description in white
            y_left += 1

        y_left += 2  # Spacing between sections

        # LEFT COLUMN - STEALTH EXPLOITS (2 lines per exploit)
        text_lines.append((left_x, y_left, "STEALTH EXPLOITS:", Colors.CYAN))
        y_left += 2

        for name, desc, color in exploits["stealth"]:
            text_lines.append((left_x + 1, y_left, name, color))  # Name in color
            y_left += 1
            text_lines.append((left_x + 1, y_left, desc, Colors.WHITE))  # Description in white
            y_left += 1

        y_left += 2  # Spacing between sections

        # LEFT COLUMN - UTILITY EXPLOITS (2 lines per exploit)
        text_lines.append((left_x, y_left, "UTILITY EXPLOITS:", Colors.CYAN))
        y_left += 2

        for name, desc, color in exploits["utility"]:
            text_lines.append((left_x + 1, y_left, name, color))  # Name in color
            y_left += 1
            text_lines.append((left_x + 1, y_left, desc, Colors.WHITE))  # Description in white
            y_left += 1

        # RIGHT COLUMN - STATUS EFFECTS (2 lines per effect)
        y_right = 4
        text_lines.append((right_x, y_right, "STATUS EFFECTS:", Colors.CYAN))
        y_right += 2

        for name, desc, color in effects["positive"]:
            text_lines.append((right_x + 1, y_right, name, color))  # Name in color
            y_right += 1
            text_lines.append((right_x + 1, y_right, desc, Colors.WHITE))  # Description in white
            y_right += 1

        y_right += 1  # Blank line between positive and negative effects

        for name, desc, color in effects["negative"]:
            text_lines.append((right_x + 1, y_right, name, color))  # Name in color
            y_right += 1
            text_lines.append((right_x + 1, y_right, desc, Colors.WHITE))  # Description in white
            y_right += 1

        y_right += 2  # Spacing between sections

        # RIGHT COLUMN - SURVIVAL TIPS (with wrapping for long lines)
        text_lines.append((right_x, y_right, "SURVIVAL TIPS:", Colors.YELLOW))
        y_right += 2

        tips = HelpContent.get_survival_tips()
        max_width = 28  # Right column width (reduced for more right padding)
        for text, color in tips:
            # Word wrap using textwrap
            wrapped_lines = textwrap.wrap(text, width=max_width)
            for line in wrapped_lines:
                text_lines.append((right_x + 1, y_right, line, color))
                y_right += 1
            # Extra blank line after each complete tip
            y_right += 2

        # Return absolute positioning format (x, y, text, color)
        return text_lines

    # Input handling methods (unchanged from original)
    def handle_input(self, event) -> str:
        """Handle help menu input with page navigation."""
        if UniversalInputHandler.is_escape_key(event):
            return "back"

        if event.type == "KEYDOWN":
            if event.sym in (tcod.event.KeySym.LEFT, tcod.event.KeySym.PAGEUP):
                self._navigate_page(-1)
            elif event.sym in (tcod.event.KeySym.RIGHT, tcod.event.KeySym.PAGEDOWN):
                self._navigate_page(1)

        return ""

    def _navigate_page(self, direction: int):
        """Navigate between help pages."""
        self.current_page = (self.current_page + direction) % self.total_pages

    def handle_mouse_motion(self, event) -> bool:
        """Handle mouse motion."""
        return False

    def handle_mouse_click(self, event) -> str:
        """Handle mouse click - right-click to return."""
        import tcod.event

        # Right-click = go back (standard behavior)
        if hasattr(event, "button") and event.button == tcod.event.MouseButton.RIGHT:
            return "back"

        # Left-click on empty space does nothing (removed confusing click-anywhere-to-exit)
        return ""

    def handle_mouse_wheel(self, event) -> bool:
        """Handle mouse wheel - navigate pages."""
        if hasattr(event, "y"):
            if event.y > 0:
                self._navigate_page(-1)
            elif event.y < 0:
                self._navigate_page(1)
            return True
        return False
