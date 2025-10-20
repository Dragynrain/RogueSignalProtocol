#!/usr/bin/env python3
"""
Rogue Signal Protocol - Game Rendering UI

Coordinates all UI rendering through specialized subsystems.
Delegates status bars to StatusBarRenderer, message log to MessageLogRenderer,
inspection panels to PanelRenderer, and full-screen overlays to FullScreenRenderer.
Acts as a facade to simplify UI rendering for the main GameRenderer.
"""

import tcod

from game_rendering_ui_message_log import MessageLogRenderer
from game_rendering_ui_status import StatusBarRenderer
from game_rendering_ui_panels import PanelRenderer
from game_rendering_ui_screens import FullScreenRenderer


class UIRenderer:
    """
    UI rendering coordinator that delegates to specialized subsystems.

    Acts as a facade for GameRenderer, providing simple delegation methods
    to specialized renderers:
    - MessageLogRenderer: System message log (right panel)
    - StatusBarRenderer: Top status bar and bottom info panel
    - PanelRenderer: Inspection panel for look mode
    - FullScreenRenderer: Help, inventory, story fragments, lore viewer

    Key attributes:
        message_log_renderer: Renders scrolling message log
        status_renderer: Renders status bars and info panels
        panel_renderer: Renders inspection overlay
        screen_renderer: Renders full-screen overlays
    """

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
        """
        Render the system message log on the right side of the screen.

        Args:
            console: TCOD console to render to
            game: GameEngine with message_log attribute
        """
        self.message_log_renderer.render_system_log(console, game)

    def render_top_status_bar(self, console: tcod.console.Console, game):
        """
        Render the top status bar with player stats.

        Args:
            console: TCOD console to render to
            game: GameEngine with player and game_state
        """
        self.status_renderer.render_top_status_bar(console, game)

    def render_bottom_panel(self, console: tcod.console.Console, game):
        """
        Render the bottom information panel with current floor and help text.

        Args:
            console: TCOD console to render to
            game: GameEngine with game_state
        """
        self.status_renderer.render_bottom_panel(console, game)

    def render_inspection_panel(self, console: tcod.console.Console, game):
        """
        Render the inspection panel when in look mode.

        Args:
            console: TCOD console to render to
            game: GameEngine with cursor_pos and inspection data
        """
        self.panel_renderer.render_inspection_panel(console, game)

    def render_help_screen(self, console: tcod.console.Console):
        """
        Render the help screen (graphical or text-based).

        Args:
            console: TCOD console to render to
        """
        self.screen_renderer.render_help_screen(console)

    def render_help_sprites(self):
        """
        Render help screen sprites for GraphicalHelpMenu.

        Only active when using graphics mode with GraphicalHelpMenu.
        No-op for text-based help menu.
        """
        self.screen_renderer.render_help_sprites()

    def render_inventory_screen(self, console: tcod.console.Console, game):
        """
        Render the inventory screen with scrolling support.

        Args:
            console: TCOD console to render to
            game: GameEngine with player inventory and scroll state
        """
        self.screen_renderer.render_inventory_screen(console, game)

    def render_story_fragment_screen(self, console: tcod.console.Console, game, fragment_index: int):
        """
        Render a story fragment discovery screen.

        Args:
            console: TCOD console to render to
            game: GameEngine with story fragment data
            fragment_index: Index of fragment to display
        """
        self.screen_renderer.render_story_fragment_screen(console, game, fragment_index)

    def render_lore_viewer_screen(self, console: tcod.console.Console, game):
        """
        Render the lore viewer showing all discovered story fragments.

        Args:
            console: TCOD console to render to
            game: GameEngine with story_fragment_manager
        """
        self.screen_renderer.render_lore_viewer_screen(console, game)
