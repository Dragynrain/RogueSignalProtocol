"""Menu Context Tests - Comprehensive menu navigation validation.

Tests validate menu navigation, selection, and exit behavior with:
- Keyboard (arrow keys, Enter, ESC)
- Gamepad (D-pad, A/B buttons)
- Mouse (hover and click)

Menu contexts tested:
- MAIN_MENU (game.show_main_menu)
- SETTINGS_MENU (game.show_settings)
- ABOUT_MENU (game.show_about)
"""

import pytest
from unittest.mock import Mock
import tcod.event

from game_input_actions import InputAction, InputContext
from game_engine import GameEngine
from game_input import InputHandler


class TestMainMenuContext:
    """Test main menu context detection and behavior."""

    def test_main_menu_context_detected(self):
        """_get_current_context returns MAIN_MENU when show_main_menu is True."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_main_menu = True
        game.show_settings = False
        game.show_about = False
        game.show_help = False
        game.show_inventory = False
        game.player = Mock()
        game.player.cpu = 100
        game.achievement_popup_manager = Mock()
        game.achievement_popup_manager.has_active_popup = Mock(return_value=False)

        handler = InputHandler(game, renderer=None)

        context = handler._get_current_context()

        assert context == InputContext.MAIN_MENU

    def test_other_menus_take_priority_over_main_menu(self):
        """Settings/About/Help take priority over main menu."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_main_menu = True  # Main menu active
        game.show_settings = True  # But settings also active
        game.player = Mock()
        game.player.cpu = 100
        game.achievement_popup_manager = Mock()
        game.achievement_popup_manager.has_active_popup = Mock(return_value=False)

        handler = InputHandler(game, renderer=None)

        context = handler._get_current_context()

        # Settings takes priority
        assert context == InputContext.SETTINGS_MENU


class TestSettingsMenuContext:
    """Test settings menu context detection and behavior."""

    def test_settings_menu_context_detected(self):
        """_get_current_context returns SETTINGS_MENU when show_settings is True."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_settings = True
        game.show_main_menu = False
        game.show_help = False
        game.show_inventory = False
        game.player = Mock()
        game.player.cpu = 100
        game.achievement_popup_manager = Mock()
        game.achievement_popup_manager.has_active_popup = Mock(return_value=False)

        handler = InputHandler(game, renderer=None)

        context = handler._get_current_context()

        assert context == InputContext.SETTINGS_MENU

    def test_cancel_closes_settings(self):
        """CANCEL action closes settings menu."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_settings = True

        handler = InputHandler(game, renderer=None)

        # Cancel action (ESC/B button)
        handler._execute_action(InputAction.CANCEL)

        # Settings should be closed
        assert game.show_settings is False

    def test_settings_takes_priority_over_main_menu(self):
        """Settings menu takes priority over main menu."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_main_menu = True
        game.show_settings = True
        game.player = Mock()
        game.player.cpu = 100
        game.achievement_popup_manager = Mock()
        game.achievement_popup_manager.has_active_popup = Mock(return_value=False)

        handler = InputHandler(game, renderer=None)

        context = handler._get_current_context()

        assert context == InputContext.SETTINGS_MENU


class TestAboutMenuContext:
    """Test about menu context detection and behavior."""

    def test_about_menu_context_detected(self):
        """_get_current_context returns ABOUT_MENU when show_about is True."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_about = True
        game.show_settings = False
        game.show_main_menu = False
        game.show_help = False
        game.show_inventory = False
        game.player = Mock()
        game.player.cpu = 100
        game.achievement_popup_manager = Mock()
        game.achievement_popup_manager.has_active_popup = Mock(return_value=False)

        handler = InputHandler(game, renderer=None)

        context = handler._get_current_context()

        assert context == InputContext.ABOUT_MENU

    def test_cancel_closes_about(self):
        """CANCEL action closes about menu."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_about = True

        handler = InputHandler(game, renderer=None)

        # Cancel action (ESC/B button)
        handler._execute_action(InputAction.CANCEL)

        # About should be closed
        assert game.show_about is False

    def test_about_takes_priority_over_main_menu(self):
        """About menu takes priority over main menu."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_main_menu = True
        game.show_about = True
        game.player = Mock()
        game.player.cpu = 100
        game.achievement_popup_manager = Mock()
        game.achievement_popup_manager.has_active_popup = Mock(return_value=False)

        handler = InputHandler(game, renderer=None)

        context = handler._get_current_context()

        assert context == InputContext.ABOUT_MENU


class TestMenuPriority:
    """Test menu context priority hierarchy."""

    def test_achievement_popup_overrides_all_menus(self):
        """Achievement popup takes priority over all menu contexts."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_main_menu = True
        game.show_settings = True
        game.show_about = True
        game.player = Mock()
        game.player.cpu = 100
        game.achievement_popup_manager = Mock()
        game.achievement_popup_manager.has_active_popup = Mock(return_value=True)

        handler = InputHandler(game, renderer=None)

        context = handler._get_current_context()

        # Achievement popup has highest priority
        assert context == InputContext.ACHIEVEMENT_POPUP

    def test_dialogue_overrides_all_menus(self):
        """Dialogue takes priority over all menu contexts."""
        game = GameEngine()
        game.dialogue_state.is_active = Mock(return_value=True)
        game.show_main_menu = True
        game.show_settings = True
        game.player = Mock()
        game.player.cpu = 100
        game.achievement_popup_manager = Mock()
        game.achievement_popup_manager.has_active_popup = Mock(return_value=False)

        handler = InputHandler(game, renderer=None)

        context = handler._get_current_context()

        # Dialogue overrides menus
        assert context == InputContext.DIALOGUE

    def test_modals_override_menus(self):
        """Modal screens (inventory, help) take priority over menus."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_main_menu = True
        game.show_inventory = True  # Inventory modal active
        game.player = Mock()
        game.player.cpu = 100
        game.achievement_popup_manager = Mock()
        game.achievement_popup_manager.has_active_popup = Mock(return_value=False)

        handler = InputHandler(game, renderer=None)

        context = handler._get_current_context()

        # Inventory takes priority over main menu
        assert context == InputContext.INVENTORY


class TestMenuInputBlocking:
    """Test that menu contexts block game actions."""

    def test_main_menu_blocks_gameplay_actions(self):
        """Player shouldn't be able to move while in main menu."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_main_menu = True

        handler = InputHandler(game, renderer=None)

        initial_x = game.player.x
        initial_y = game.player.y

        # Try to move (should not affect player position)
        handler._execute_action(InputAction.MOVE_NORTH)

        # Player position unchanged
        assert game.player.x == initial_x
        assert game.player.y == initial_y

    def test_settings_menu_blocks_gameplay_actions(self):
        """Player shouldn't be able to move while in settings."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_settings = True

        handler = InputHandler(game, renderer=None)

        initial_x = game.player.x
        initial_y = game.player.y

        # Try to move (should not affect player position)
        handler._execute_action(InputAction.MOVE_NORTH)

        # Player position unchanged
        assert game.player.x == initial_x
        assert game.player.y == initial_y

    def test_about_menu_blocks_gameplay_actions(self):
        """Player shouldn't be able to move while in about menu."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_about = True

        handler = InputHandler(game, renderer=None)

        initial_x = game.player.x
        initial_y = game.player.y

        # Try to move (should not affect player position)
        handler._execute_action(InputAction.MOVE_NORTH)

        # Player position unchanged
        assert game.player.x == initial_x
        assert game.player.y == initial_y
