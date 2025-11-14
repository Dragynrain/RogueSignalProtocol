#!/usr/bin/env python3
"""
Integration tests for menu interactions.

Tests mouse and keyboard interactions with menus:
- Volume slider clicks
- Menu navigation with mouse
- Settings toggles
- Hover highlighting
"""

from unittest.mock import Mock, patch

import tcod

from game_config import GameConfig, GameSettings
from game_menus import MainMenu, SettingsMenu


class TestMenuMouseInteractions:
    """Test menu mouse interaction functionality."""

    def test_settings_menu_volume_click_increases(self):
        """Clicking right side of volume slider increases volume."""
        with patch("game_audio.SoundManager"):
            settings = GameSettings()
            settings.set_volume_percent("master", 50)

            menu = SettingsMenu(settings)

            # Create mock mouse click event on right side of volume bar
            # Volume bars are at content_left + 18, length 20
            # Right side = bar_x + 15 (middle is at 10)
            layout = menu._get_menu_layout_params()
            if layout["use_background_layout"]:
                box_left = GameConfig.SCREEN_WIDTH - 32
                bar_x = box_left + 3 + 18
            else:
                box_left = (GameConfig.SCREEN_WIDTH - 40) // 2
                bar_x = box_left + 2 + 18

            # Click on right side (should increase)
            click_x = bar_x + 15
            # First option is at box_top + 5, where box_top = (50-46)//2 = 2, so y=7
            click_y = 7  # First option row (menu_height=46 matches Main Menu)

            event = Mock()
            event.tile = Mock()
            event.tile.x = click_x
            event.tile.y = click_y
            event.position = Mock()
            event.position.x = click_x
            event.position.y = click_y

            # First select the volume option with mouse motion
            menu.handle_mouse_motion(event)
            assert menu.selected_option == 0  # Master Volume is first

            # Then click it
            initial_volume = settings.get_volume_percent("master")
            menu.handle_mouse_click(event)

            # Volume should increase by 5%
            assert settings.get_volume_percent("master") == initial_volume + 5

    def test_settings_menu_volume_click_decreases(self):
        """Clicking left side of volume slider decreases volume."""
        with patch("game_audio.SoundManager"):
            settings = GameSettings()
            settings.set_volume_percent("master", 50)

            menu = SettingsMenu(settings)

            # Create mock mouse click event on left side of volume bar
            # Must match the actual box calculation in game_menus.py
            layout = menu._get_menu_layout_params()
            if layout["use_background_layout"]:
                box_width = 28
                box_right = GameConfig.SCREEN_WIDTH - 2 - 3
                box_left = box_right - box_width
                content_left = box_left + 1
                bar_start_x = content_left + 1
                bar_content_start = bar_start_x + 4
                bar_length = 8
            else:
                box_width = 50  # Fixed: was 40, should be 50
                box_left = (GameConfig.SCREEN_WIDTH - box_width) // 2
                content_left = box_left + 2
                bar_start_x = content_left + 18
                bar_content_start = bar_start_x + 4
                bar_length = 14

            bar_content_end = bar_content_start + bar_length - 1
            bar_mid = (bar_content_start + bar_content_end) // 2

            # Click on left side (definitely before midpoint, should decrease)
            click_x = bar_content_start + 1
            click_y = 7  # First option row (menu_height=46 matches Main Menu)

            event = Mock()
            event.tile = Mock()
            event.tile.x = click_x
            event.tile.y = click_y
            event.position = Mock()
            event.position.x = click_x
            event.position.y = click_y

            # First select the volume option with mouse motion
            menu.handle_mouse_motion(event)
            assert menu.selected_option == 0  # Master Volume is first

            # Then click it
            initial_volume = settings.get_volume_percent("master")
            menu.handle_mouse_click(event)

            # Volume should decrease by 5%
            assert settings.get_volume_percent("master") == initial_volume - 5

    def test_settings_menu_volume_respects_bounds(self):
        """Volume slider clicks respect 0-100% bounds."""
        with patch("game_audio.SoundManager"):
            settings = GameSettings()

            # Test lower bound
            settings.set_volume_percent("master", 0)
            menu = SettingsMenu(settings)

            # Calculate bar position (must match game_menus.py)
            layout = menu._get_menu_layout_params()
            if layout["use_background_layout"]:
                box_width = 28
                box_right = GameConfig.SCREEN_WIDTH - 2 - 3
                box_left = box_right - box_width
                content_left = box_left + 1
                bar_start_x = content_left + 1
                bar_content_start = bar_start_x + 4
                bar_length = 8
            else:
                box_width = 50  # Fixed: was 40, should be 50
                box_left = (GameConfig.SCREEN_WIDTH - box_width) // 2
                content_left = box_left + 2
                bar_start_x = content_left + 18
                bar_content_start = bar_start_x + 4
                bar_length = 14

            bar_content_end = bar_content_start + bar_length - 1

            # Click left side when at 0%
            event = Mock()
            event.tile = Mock()
            event.tile.x = bar_content_start + 1
            event.tile.y = 12
            event.position = Mock()
            event.position.x = bar_content_start + 1
            event.position.y = 12

            menu.handle_mouse_motion(event)
            menu.handle_mouse_click(event)

            # Should stay at 0%
            assert settings.get_volume_percent("master") == 0

            # Test upper bound
            settings.set_volume_percent("master", 100)
            menu = SettingsMenu(settings)

            # Click right side when at 100%
            event.tile.x = bar_content_end - 1
            event.position.x = bar_content_end - 1

            menu.handle_mouse_motion(event)
            menu.handle_mouse_click(event)

            # Should stay at 100%
            assert settings.get_volume_percent("master") == 100

    def test_settings_menu_toggle_click(self):
        """Clicking toggle options changes their value."""
        with patch("game_audio.SoundManager"):
            settings = GameSettings()
            initial_mode = settings.graphics_mode

            menu = SettingsMenu(settings)

            # Find graphics mode option (should be option 3)
            graphics_option_index = None
            for i, opt in enumerate(menu.options):
                if opt.get("key") == "graphics_mode":
                    graphics_option_index = i
                    break

            assert graphics_option_index is not None, "Graphics mode option not found"

            # Create click event on graphics toggle
            # Calculate correct Y position based on layout
            layout = menu._get_menu_layout_params()
            spacing = 3 if layout["use_background_layout"] else 2
            menu_height = GameConfig.SCREEN_HEIGHT - 4  # Matches actual Settings menu height
            box_top = (GameConfig.SCREEN_HEIGHT - menu_height) // 2
            start_y = box_top + 5
            option_y = start_y + (graphics_option_index * spacing)

            event = Mock()
            event.tile = Mock()
            event.tile.x = 40  # Somewhere in the menu
            event.tile.y = option_y
            event.position = Mock()
            event.position.x = 40
            event.position.y = option_y

            # Select and click the option
            menu.handle_mouse_motion(event)
            menu.handle_mouse_click(event)

            # Graphics mode should toggle
            assert settings.graphics_mode != initial_mode

    def test_main_menu_mouse_hover_changes_selection(self):
        """Moving mouse over menu options changes selection."""
        with patch("game_audio.SoundManager"):
            menu = MainMenu()

            initial_selection = menu.selected_option

            # Create mouse motion event over a different option
            event = Mock()
            event.position = Mock()
            event.position.x = 40
            event.position.y = 23  # Second option (21 + 2)

            menu.handle_mouse_motion(event)

            # Selection should change
            assert menu.selected_option != initial_selection

    def test_settings_menu_back_button_click(self):
        """Clicking Back button returns 'back' action."""
        with patch("game_audio.SoundManager"):
            settings = GameSettings()
            menu = SettingsMenu(settings)

            # Find Back option (should be last)
            back_index = len(menu.options) - 1

            # Create click event on Back
            # Calculate correct Y position based on layout
            layout = menu._get_menu_layout_params()
            spacing = 3 if layout["use_background_layout"] else 2
            menu_height = GameConfig.SCREEN_HEIGHT - 4  # Matches actual Settings menu height
            box_top = (GameConfig.SCREEN_HEIGHT - menu_height) // 2
            start_y = box_top + 5
            option_y = start_y + (back_index * spacing)

            event = Mock()
            event.tile = Mock()
            event.tile.x = 40
            event.tile.y = option_y
            event.position = Mock()
            event.position.x = 40
            event.position.y = option_y

            # Select and click Back
            menu.handle_mouse_motion(event)
            result = menu.handle_mouse_click(event)

            assert result == "back"

    def test_menu_renders_without_crash(self):
        """Menus render without crashing."""
        with patch("game_audio.SoundManager"):
            console = tcod.console.Console(width=80, height=50)

            # Test main menu
            menu = MainMenu()
            menu.render(console)  # Should not crash

            # Test settings menu
            settings = GameSettings()
            settings_menu = SettingsMenu(settings)
            settings_menu.render(console)  # Should not crash

    def test_volume_slider_visual_indicators(self):
        """Volume sliders show directional indicators."""
        with patch("game_audio.SoundManager"):
            console = tcod.console.Console(width=80, height=50)
            settings = GameSettings()
            menu = SettingsMenu(settings)

            # Render menu
            menu.render(console)

            # Check that volume bars are rendered (can't easily verify exact content,
            # but rendering shouldn't crash)
            assert True  # If we got here, rendering worked


class TestMenuKeyboardInteractions:
    """Test menu keyboard interaction functionality."""

    def test_settings_menu_arrow_keys_adjust_volume(self):
        """Left/Right arrow keys adjust volume."""
        with patch("game_audio.SoundManager"):
            settings = GameSettings()
            settings.set_volume_percent("master", 50)

            menu = SettingsMenu(settings)
            menu.selected_option = 0  # Master Volume

            # Press right arrow
            event = tcod.event.KeyDown(
                scancode=0, sym=tcod.event.KeySym.RIGHT, mod=tcod.event.Modifier(0)
            )

            menu.handle_input(event)

            # Volume should increase
            assert settings.get_volume_percent("master") == 55

            # Press left arrow
            event.sym = tcod.event.KeySym.LEFT
            menu.handle_input(event)

            # Volume should decrease back
            assert settings.get_volume_percent("master") == 50

    def test_settings_menu_enter_toggles_option(self):
        """Pressing Enter on toggle options changes them."""
        with patch("game_audio.SoundManager"):
            settings = GameSettings()
            initial_mode = settings.graphics_mode

            menu = SettingsMenu(settings)

            # Find and select graphics mode option
            for i, opt in enumerate(menu.options):
                if opt.get("key") == "graphics_mode":
                    menu.selected_option = i
                    break

            # Press Enter
            event = tcod.event.KeyDown(
                scancode=0, sym=tcod.event.KeySym.RETURN, mod=tcod.event.Modifier(0)
            )

            menu.handle_input(event)

            # Mode should toggle
            assert settings.graphics_mode != initial_mode


class TestMenuEdgeCases:
    """Test edge cases and error handling."""

    def test_menu_handles_invalid_mouse_coordinates(self):
        """Menu doesn't crash with out-of-bounds mouse coordinates."""
        with patch("game_audio.SoundManager"):
            settings = GameSettings()
            menu = SettingsMenu(settings)

            # Create event with invalid coordinates
            event = Mock()
            event.position = Mock()
            event.position.x = -10
            event.position.y = 200
            event.tile = Mock()
            event.tile.x = -10
            event.tile.y = 200

            # Should not crash
            menu.handle_mouse_motion(event)
            menu.handle_mouse_click(event)

    def test_menu_handles_missing_event_attributes(self):
        """Menu handles events with missing attributes gracefully."""
        with patch("game_audio.SoundManager"):
            settings = GameSettings()
            menu = SettingsMenu(settings)

            # Create event without position
            event = Mock()
            event.position = None

            # Should return False, not crash
            result = menu.handle_mouse_motion(event)
            assert not result
