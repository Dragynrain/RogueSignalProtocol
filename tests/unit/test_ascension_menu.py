#!/usr/bin/env python3
"""
Unit tests for Ascension Menu System (Phase 3).

Tests menu navigation, display, unlock state, and modifier display.
TDD-first: Write these tests before implementing game_menu_ascension.py.
"""


class TestAscensionMenuUnlockState:
    """Test menu shows correct unlock state for levels."""

    def test_level_zero_always_selectable(self):
        """A0 (base game) should always be selectable."""
        from rsp.ui.menu_ascension import AscensionMenu

        menu = AscensionMenu(highest_unlocked=0)
        assert menu.is_level_selectable(0)

    def test_unlocked_levels_selectable(self):
        """Levels up to highest_unlocked should be selectable."""
        from rsp.ui.menu_ascension import AscensionMenu

        menu = AscensionMenu(highest_unlocked=5)
        assert menu.is_level_selectable(0)
        assert menu.is_level_selectable(3)
        assert menu.is_level_selectable(5)

    def test_locked_levels_not_selectable(self):
        """Levels above highest_unlocked should not be selectable."""
        from rsp.ui.menu_ascension import AscensionMenu

        menu = AscensionMenu(highest_unlocked=5)
        assert not menu.is_level_selectable(6)
        assert not menu.is_level_selectable(10)
        assert not menu.is_level_selectable(20)

    def test_all_levels_selectable_at_max(self):
        """All levels should be selectable when A20 unlocked."""
        from rsp.ui.menu_ascension import AscensionMenu

        menu = AscensionMenu(highest_unlocked=20)
        for level in range(21):
            assert menu.is_level_selectable(level)


class TestAscensionMenuModifierDisplay:
    """Test cumulative modifier display for levels."""

    def test_a0_shows_no_modifiers(self):
        """A0 should show no modifiers (base game)."""
        from rsp.ui.menu_ascension import AscensionMenu

        menu = AscensionMenu(highest_unlocked=10)
        modifiers = menu.get_modifiers_for_level(0)
        assert modifiers == "Base game - no modifiers"

    def test_a1_shows_scanner_vision(self):
        """A1 should show scanner vision bonus."""
        from rsp.ui.menu_ascension import AscensionMenu

        menu = AscensionMenu(highest_unlocked=10)
        modifiers = menu.get_modifiers_for_level(1)
        assert "Scanners +1 vision" in modifiers

    def test_a5_shows_cumulative_modifiers(self):
        """A5 should show all A1-A5 modifiers cumulatively."""
        from rsp.ui.menu_ascension import AscensionMenu

        menu = AscensionMenu(highest_unlocked=10)
        modifiers = menu.get_modifiers_for_level(5)
        # Should contain modifiers from A1-A5
        assert "Scanners +1 vision" in modifiers  # A1
        assert "Enemies +10 CPU" in modifiers  # A2
        assert "Trace builds faster" in modifiers  # A3
        assert "Enemies +20% damage" in modifiers  # A4
        assert "All enemies +1 vision" in modifiers  # A5

    def test_locked_level_shows_placeholder(self):
        """Locked levels should show '???' for modifiers."""
        from rsp.ui.menu_ascension import AscensionMenu

        menu = AscensionMenu(highest_unlocked=5)
        modifiers = menu.get_modifiers_for_level(6)
        assert modifiers == "???"

    def test_locked_level_at_boundary(self):
        """Level exactly one above unlocked should show ???."""
        from rsp.ui.menu_ascension import AscensionMenu

        menu = AscensionMenu(highest_unlocked=10)
        modifiers = menu.get_modifiers_for_level(11)
        assert modifiers == "???"


class TestAscensionMenuNavigation:
    """Test menu navigation behavior."""

    def test_navigate_up_wraps_from_top(self):
        """Navigating up from top should wrap to bottom."""
        from rsp.ui.menu_ascension import AscensionMenu

        menu = AscensionMenu(highest_unlocked=20)
        menu.current_selection = 0
        menu.navigate_up()
        assert menu.current_selection == 20

    def test_navigate_down_wraps_from_bottom(self):
        """Navigating down from bottom should wrap to top."""
        from rsp.ui.menu_ascension import AscensionMenu

        menu = AscensionMenu(highest_unlocked=20)
        menu.current_selection = 20
        menu.navigate_down()
        assert menu.current_selection == 0

    def test_navigate_down_increments(self):
        """Navigating down should increment selection."""
        from rsp.ui.menu_ascension import AscensionMenu

        menu = AscensionMenu(highest_unlocked=20)
        menu.current_selection = 5
        menu.navigate_down()
        assert menu.current_selection == 6

    def test_navigate_up_decrements(self):
        """Navigating up should decrement selection."""
        from rsp.ui.menu_ascension import AscensionMenu

        menu = AscensionMenu(highest_unlocked=20)
        menu.current_selection = 5
        menu.navigate_up()
        assert menu.current_selection == 4


class TestAscensionMenuSelection:
    """Test selection confirmation behavior."""

    def test_confirm_unlocked_level_saves(self):
        """Confirming selection on unlocked level should save to settings."""
        from unittest.mock import MagicMock, patch

        from rsp.ui.menu_ascension import AscensionMenu

        menu = AscensionMenu(highest_unlocked=10)
        menu.current_selection = 7

        # Mock the settings
        with patch("rsp.ui.menu_ascension.GameSettings") as mock_settings_class:
            mock_instance = MagicMock()
            mock_settings_class.get_instance.return_value = mock_instance

            result = menu.confirm_selection()

            assert result == "selected"
            mock_instance.set_ascension_level.assert_called_once_with(7)

    def test_confirm_locked_level_rejected(self):
        """Confirming selection on locked level should be rejected."""
        from rsp.ui.menu_ascension import AscensionMenu

        menu = AscensionMenu(highest_unlocked=5)
        menu.current_selection = 10  # Locked

        result = menu.confirm_selection()

        assert result == "locked"

    def test_get_current_level_selected(self):
        """Should be able to get the currently selected level."""
        from rsp.ui.menu_ascension import AscensionMenu

        menu = AscensionMenu(highest_unlocked=10)
        menu.current_selection = 7
        assert menu.get_selected_level() == 7


class TestAscensionMenuInitialization:
    """Test menu initialization state."""

    def test_initial_selection_at_current_level(self):
        """Menu should initialize with selection at current ascension level."""
        from unittest.mock import MagicMock, patch

        from rsp.ui.menu_ascension import AscensionMenu

        with patch("rsp.ui.menu_ascension.GameSettings") as mock_settings_class:
            mock_instance = MagicMock()
            mock_instance.get_ascension_level.return_value = 5
            mock_settings_class.get_instance.return_value = mock_instance

            menu = AscensionMenu(highest_unlocked=10, initial_level=5)

            assert menu.current_selection == 5

    def test_total_levels_is_21(self):
        """Menu should have 21 levels (0-20)."""
        from rsp.ui.menu_ascension import AscensionMenu

        menu = AscensionMenu(highest_unlocked=20)
        assert menu.total_levels == 21

    def test_highest_unlocked_stored(self):
        """Menu should store highest unlocked level."""
        from rsp.ui.menu_ascension import AscensionMenu

        menu = AscensionMenu(highest_unlocked=15)
        assert menu.highest_unlocked == 15


class TestGameSettingsAscensionAccessors:
    """Test GameSettings ascension accessor methods."""

    def test_get_ascension_level_default(self):
        """get_ascension_level should return 0 by default."""
        from unittest.mock import patch

        from rsp.core.config import GameSettings

        with patch.object(GameSettings, "load_settings"):
            settings = GameSettings()
            # ascension dict should exist with defaults
            assert settings.get_ascension_level() == 0

    def test_set_ascension_level(self):
        """set_ascension_level should update the level."""
        from unittest.mock import patch

        from rsp.core.config import GameSettings

        with patch.object(GameSettings, "load_settings"):
            with patch.object(GameSettings, "save_settings"):
                settings = GameSettings()
                settings.set_ascension_level(5)
                assert settings.get_ascension_level() == 5

    def test_get_highest_ascension_unlocked_default(self):
        """get_highest_ascension_unlocked should return 0 by default."""
        from unittest.mock import patch

        from rsp.core.config import GameSettings

        with patch.object(GameSettings, "load_settings"):
            settings = GameSettings()
            assert settings.get_highest_ascension_unlocked() == 0

    def test_unlock_ascension_updates_highest(self):
        """unlock_ascension should update highest_unlocked if higher."""
        from unittest.mock import patch

        from rsp.core.config import GameSettings

        with patch.object(GameSettings, "load_settings"):
            with patch.object(GameSettings, "save_settings"):
                settings = GameSettings()
                result = settings.unlock_ascension(1)
                assert result is True
                assert settings.get_highest_ascension_unlocked() == 1

    def test_unlock_ascension_ignores_lower(self):
        """unlock_ascension should not update if level is not higher."""
        from unittest.mock import patch

        from rsp.core.config import GameSettings

        with patch.object(GameSettings, "load_settings"):
            with patch.object(GameSettings, "save_settings"):
                settings = GameSettings()
                settings.ascension["highest_unlocked"] = 5
                result = settings.unlock_ascension(3)
                assert result is False
                assert settings.get_highest_ascension_unlocked() == 5


class TestStatusBarAscensionIndicator:
    """Test status bar shows ascension level."""

    def test_status_bar_shows_ascension_when_above_zero(self):
        """Status bar should show 'A#' when ascension > 0."""
        from unittest.mock import MagicMock

        from rsp.ui.status_bar import StatusBarRenderer

        # Create mock game with ascension level
        mock_game = MagicMock()
        mock_game.ascension_level = 5
        mock_game.player.cpu = 100
        mock_game.player.max_cpu = 100
        mock_game.player.heat = 0
        mock_game.player.max_heat = 100
        mock_game.player.trace_level = 0
        mock_game.player.ram_used = 4
        mock_game.player.ram_total = 8

        renderer = StatusBarRenderer()

        # Get status parts that would be rendered
        parts = renderer._get_status_parts(mock_game)

        # Should include ascension indicator
        assert any("A5" in part for part in parts)

    def test_status_bar_hides_ascension_at_zero(self):
        """Status bar should NOT show ascension at A0."""
        from unittest.mock import MagicMock

        from rsp.ui.status_bar import StatusBarRenderer

        mock_game = MagicMock()
        mock_game.ascension_level = 0
        mock_game.player.cpu = 100
        mock_game.player.max_cpu = 100
        mock_game.player.heat = 0
        mock_game.player.max_heat = 100
        mock_game.player.trace_level = 0
        mock_game.player.ram_used = 4
        mock_game.player.ram_total = 8

        renderer = StatusBarRenderer()

        parts = renderer._get_status_parts(mock_game)

        # Should NOT include ascension indicator at A0
        assert not any("A0" in part for part in parts)


class TestMainMenuAscensionDisplay:
    """Test main menu shows ascension-related options."""

    def test_main_menu_shows_ascension_option_when_unlocked(self):
        """Main menu should show 'Ascension' option when A1+ unlocked."""
        from unittest.mock import MagicMock, patch

        from rsp.ui.menu_main import MainMenu

        with patch("rsp.ui.menu_main.GameSettings") as mock_settings_class:
            mock_instance = MagicMock()
            mock_instance.get_highest_ascension_unlocked.return_value = 1
            mock_instance.graphics_mode = "glyph"
            mock_settings_class.get_instance.return_value = mock_instance

            menu = MainMenu()
            menu.refresh_options()

            # Check options include Ascension
            assert any("Ascension" in opt for opt in menu.options)

    def test_main_menu_hides_ascension_option_at_a0(self):
        """Main menu should NOT show 'Ascension' option at A0."""
        from unittest.mock import MagicMock, patch

        from rsp.ui.menu_main import MainMenu

        with patch("rsp.ui.menu_main.GameSettings") as mock_settings_class:
            mock_instance = MagicMock()
            mock_instance.get_highest_ascension_unlocked.return_value = 0
            mock_instance.graphics_mode = "glyph"
            mock_settings_class.get_instance.return_value = mock_instance

            menu = MainMenu()
            menu.refresh_options()

            # Check options do NOT include Ascension
            assert not any("Ascension" in opt for opt in menu.options)


class TestAscensionMenuMouseHandling:
    """Test mouse click handling for ascension menu."""

    def test_left_click_on_unlocked_level_confirms_selection(self):
        """Left clicking an unlocked level should confirm and return 'back'."""
        from types import SimpleNamespace
        from unittest.mock import patch

        from rsp.ui.menu_ascension import AscensionMenu

        menu = AscensionMenu(highest_unlocked=5)
        # Simulate glyph mode (no background)
        menu._background = None

        # In glyph mode: box_top=3, list_start_y=box_top+6=9
        # Level 0 is at y=9, level 1 at y=10, etc.
        event = SimpleNamespace(tile=SimpleNamespace(x=40, y=9))  # Click on level 0

        with patch.object(menu, "confirm_selection", return_value="selected"):
            result = menu.handle_left_click(event)

        assert result == "back"

    def test_left_click_on_locked_level_does_not_confirm(self):
        """Left clicking a locked level should update selection but not confirm."""
        from types import SimpleNamespace

        from rsp.ui.menu_ascension import AscensionMenu

        menu = AscensionMenu(highest_unlocked=5)
        menu._background = None

        # In glyph mode: list_start_y=9
        # Level 10 is at y=19 (9+10), but with scroll we need to scroll first
        menu.scroll_offset = 10  # Show levels 10-19
        event = SimpleNamespace(tile=SimpleNamespace(x=40, y=9))  # Click on level 10 (scrolled)

        result = menu.handle_left_click(event)

        # Should update selection to level 10 but return "" since it's locked
        assert menu.current_selection == 10
        assert result == ""

    def test_left_click_in_view_only_mode_does_not_confirm(self):
        """In view_only mode, left click should navigate but not confirm."""
        from types import SimpleNamespace
        from unittest.mock import patch

        from rsp.ui.menu_ascension import AscensionMenu

        menu = AscensionMenu(highest_unlocked=5, view_only=True)
        menu._background = None

        event = SimpleNamespace(tile=SimpleNamespace(x=40, y=9))  # Click on level 0

        with patch.object(menu, "confirm_selection") as mock_confirm:
            result = menu.handle_left_click(event)

        # Should NOT call confirm_selection in view_only mode
        mock_confirm.assert_not_called()
        assert result == ""
        assert menu.current_selection == 0
