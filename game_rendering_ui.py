#!/usr/bin/env python3
"""
Game Rendering UI
Coordinator for all UI overlays and HUD elements.
"""

import tcod

from game_rendering_ui_message_log import MessageLogRenderer
from game_rendering_ui_status import StatusBarRenderer
from game_rendering_ui_panels import PanelRenderer
from game_rendering_ui_screens import FullScreenRenderer


class UIRenderer:
    """Renders UI elements by coordinating specialized renderers."""

    def __init__(self, settings=None, context=None, tile_manager=None):
        """
        Initialize UI renderer with component renderers.

        Args:
            settings: GameSettings instance (optional, for graphical help)
            context: TCOD context (optional, for graphical help)
            tile_manager: TileManager instance (optional, for graphical help)
        """
        self.message_log_renderer = MessageLogRenderer()
        self.status_renderer = StatusBarRenderer()
        self.panel_renderer = PanelRenderer()
        self.screen_renderer = FullScreenRenderer(
            self.status_renderer,
            self.message_log_renderer,
            settings=settings,
            context=context,
            tile_manager=tile_manager
        )

    # === Delegate to component renderers ===

    def render_system_log(self, console: tcod.console.Console, game):
        """Render the system log on the right side."""
        self.message_log_renderer.render_system_log(console, game)

    def render_top_status_bar(self, console: tcod.console.Console, game):
        """Render the top status bar across the full width."""
        self.status_renderer.render_top_status_bar(console, game)

    def render_bottom_panel(self, console: tcod.console.Console, game):
        """Render the bottom information panel."""
        self.status_renderer.render_bottom_panel(console, game)

    def render_inspection_panel(self, console: tcod.console.Console, game):
        """Render the inspection panel when in look mode."""
        self.panel_renderer.render_inspection_panel(console, game)

    def render_help_screen(self, console: tcod.console.Console):
        """Render the help screen using appropriate help menu."""
        self.screen_renderer.render_help_screen(console)

    def render_help_sprites(self):
        """Render help screen sprites (for GraphicalHelpMenu only)."""
        self.screen_renderer.render_help_sprites()

    def render_inventory_screen(self, console: tcod.console.Console, game):
        """Render the inventory screen with scrolling support."""
        self.screen_renderer.render_inventory_screen(console, game)

    def render_story_fragment_screen(self, console: tcod.console.Console, game, fragment_index: int):
        """Render a single story fragment discovery screen."""
        self.screen_renderer.render_story_fragment_screen(console, game, fragment_index)

    def render_lore_viewer_screen(self, console: tcod.console.Console, game):
        """Render the lore viewer showing all discovered fragments."""
        self.screen_renderer.render_lore_viewer_screen(console, game)
