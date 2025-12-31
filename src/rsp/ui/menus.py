#!/usr/bin/env python3
"""
Rogue Signal Protocol - Menu System (Re-export Module)

This module provides a central import point for all menu classes.
The actual implementations have been split into separate files for better organization:
- game_menu_main.py: MainMenu class
- game_menu_settings.py: SettingsMenu class
- game_menu_help_lore.py: LoreMenu and HelpMenu classes (separate file)
- game_menu_background.py: MenuBackground class (separate file)

This file maintains backward compatibility by re-exporting all menu classes.
"""

# Import menu classes from their respective modules
from rsp.ui.menu_background import MenuBackground
from rsp.ui.menu_main import MainMenu
from rsp.ui.menu_settings import SettingsMenu

# Explicit exports (prevents ruff from removing "unused" imports)
__all__ = [
    "MenuBackground",
    "MainMenu",
    "SettingsMenu",
]
